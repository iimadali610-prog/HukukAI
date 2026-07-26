import os
import requests
import numpy as np
from dotenv import load_dotenv
from pgvector.django import CosineDistance
from sklearn.feature_extraction.text import TfidfVectorizer
from core.models import DocumentChunk, LegalDocument, DocumentType
from core.scraper import LiveLegalScraper

load_dotenv()


class LegalAIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(".env dosyasında geçerli bir GROQ_API_KEY tanımlanmamış!")

        self.vectorizer = TfidfVectorizer(max_features=768)
        self.scraper = LiveLegalScraper()

    def _generate_local_embeddings(self, texts: list[str]) -> list[list[float]]:
        tfidf_matrix = self.vectorizer.fit_transform(texts).toarray()
        embeddings = []
        for row in tfidf_matrix:
            if len(row) < 768:
                padded = np.pad(row, (0, 768 - len(row)), 'constant')
                embeddings.append(padded.tolist())
            else:
                embeddings.append(row[:768].tolist())
        return embeddings

    def update_missing_embeddings(self):
        empty_chunks = list(DocumentChunk.objects.filter(embedding__isnull=True))
        if not empty_chunks:
            return

        texts = [chunk.content for chunk in empty_chunks]
        embeddings = self._generate_local_embeddings(texts)

        for chunk, emb in zip(empty_chunks, embeddings):
            chunk.embedding = emb
            chunk.save()

    def get_strictly_relevant_chunks(self, query: str, top_k: int = 3):
        """
        Sadece ve sadece aranan soruyla DOĞRUDAN kelime/anlam bağı olan kararları getirir.
        Alakasız İş Kanunu vb. kararları KESİNLİKLE eler.
        """
        all_chunks = list(DocumentChunk.objects.all())
        if not all_chunks:
            return []

        # Sorudaki anahtar kelimeleri ayıkla (3 karakterden uzunlar)
        query_words = [w.lower() for w in query.split() if len(w) > 3]

        strictly_matched = []

        for chunk in all_chunks:
            content_lower = chunk.content.lower()
            title_lower = chunk.document.title.lower()

            # Sorudaki anahtar kelimelerden en az biri metinde veya başlıkta geçiyor mu?
            matches = [word for word in query_words if word in content_lower or word in title_lower]

            # Eğer sorulan kelimelerle HİÇBİR alakası yoksa (örn: soru taşınmaz ama karar iş kanunu ise) Doğrudan atla!
            if len(matches) > 0:
                strictly_matched.append(chunk)

        return strictly_matched[:top_k]

    def _auto_ingest_live_data(self, query: str):
        """Soruya özel taze canlı veri çeker ve kaydeder."""
        live_data = self.scraper.fetch_legal_info(query)

        for item in live_data:
            doc, created = LegalDocument.objects.get_or_create(
                source_url=item["url"] + f"#{hash(item['content'])}",
                defaults={
                    "title": item["title"],
                    "doc_type": DocumentType.KANUN,
                    "raw_content": item["content"]
                }
            )
            if created:
                DocumentChunk.objects.create(
                    document=doc,
                    chunk_index=0,
                    content=item["content"]
                )

    def _generate_ai_response(self, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"AI Servis Hatası ({response.status_code}): {response.text}")

    def answer_query(self, query: str) -> dict:
        self.update_missing_embeddings()

        # 1. Sıkı Filtreleme: Sorudaki kelimeler geçmiyor ise veri alma!
        relevant_chunks = self.get_strictly_relevant_chunks(query)

        # 2. Eğer veritabanında soruyla ALAKALI karar yoksa canlı internet verisini çek
        if not relevant_chunks:
            self._auto_ingest_live_data(query)
            self.update_missing_embeddings()
            relevant_chunks = self.get_strictly_relevant_chunks(query)

        # 3. Bağlam Oluşturma
        if relevant_chunks:
            context_text = ""
            for idx, chunk in enumerate(relevant_chunks, 1):
                context_text += f"\n[DAYANAK {idx}]: {chunk.document.title}\n{chunk.content}\n"
        else:
            context_text = "Sorulan özel konuda veritabanında direkt karar eşleşmesi bulunamadı. Genel Türk Hukuku (TBK, TMK vb.) mevzuat hükümlerine göre yanıtla."

        prompt = f"""
        Sen uzman bir Türk Hukuku Yapay Zeka Danışmanısın.
        Aşağıda sana verilen dayanak metinleri ve Türk Hukuk Mevzuatını (TBK, TMK vb.) dikkate alarak kullanıcının sorusunu yanıtla.

        Kurallar:
        1. Kullanıcının sorusunu (Örn: Taşınmaz Satış Vaadi) Türk Borçlar Kanunu ve Medeni Kanun çerçevesinde detaylıca açıkla.
        2. Şekil şartları, noter zorunluluğu, tapuya şerh gibi kritik noktaları maddeler halinde yaz.
        3. Dili resmi, net ve profesyonel tut.

        [DAYANAK METİNLER]:
        {context_text}

        [KULLANICI SORUSU]:
        {query}
        """

        answer_text = self._generate_ai_response(prompt)

        return {
            "answer": answer_text,
            "sources": [
                {
                    "title": c.document.title,
                    "url": c.document.source_url,
                    "excerpt": c.content[:150] + "..."
                } for c in relevant_chunks
            ]
        }