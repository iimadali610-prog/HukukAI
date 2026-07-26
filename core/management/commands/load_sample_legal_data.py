from django.core.management.base import BaseCommand
from core.models import LegalDocument, DocumentChunk, DocumentType

class Command(BaseCommand):
    help = "Örnek mevzuat ve yargıtay kararlarını veritabanına yükler ve parçalar."

    def handle(self, *args, **options):
        self.stdout.write("Veriler yükleniyor ve parçalanıyor...")

        # Test için gerçekçi bir Yargıtay Kararı Örneği
        sample_data = [
            {
                "title": "Yargıtay 9. HD., E. 2021/4512 K. 2021/8954",
                "doc_type": DocumentType.YARGITAY,
                "url": "https://karararama.yargitay.gov.tr/example/1",
                "content": """
                ÖZET: Mesai saatleri içerisinde sürekli olarak kişisel sosyal medya hesabı kullanılması ve 
                hatırlatmalara rağmen bu durumun alışkanlık haline getirilmesi, işverene 4857 sayılı İş Kanunu'nun 
                25/II-h maddesi uyarınca haklı fesih imkanı tanır.

                KARAR DETAYI: Davacı işçi, kıdem ve ihbar tazminatı alacağı istemiyle dava açmıştır. 
                Davalı işveren ise işçinin mesai saatlerinde işini aksatacak düzeyde cep telefonu ile sosyal medyada 
                vakit geçirdiğini, yapılan yazılı uyarılara rağmen bu eylemine devam ettiğini savunmuştur. 
                Tanık beyanları ve bilgisayar kayıtları incelendiğinde; davacının günün önemli bir kısmını 
                işle ilgili olmayan internet sitelerinde geçirdiği tespit edilmiştir. İşçinin sadakat borcu 
                ve iş görme edimini ihlal ettiği sabittir. Bu nedenle feshin haklı nedene dayandığı kabul edilerek 
                kıdem tazminatı talebinin reddi gerekmiştir.
                """
            },
            {
                "title": "4857 Sayılı İş Kanunu - Madde 25",
                "doc_type": DocumentType.KANUN,
                "url": "https://mevzuat.gov.tr/mevzuat?MevzuatNo=4857&Madde=25",
                "content": """
                İşverenin derhal fesih hakkı:
                Süresi belirli olsun veya olmasın işveren, aşağıda yazılı hallerde sözleşmeyi süresinden önce 
                veya bildirim süresini beklemeksizin feshedebilir:
                I- Sağlık sebepleri
                II- Ahlak ve iyi niyet kurallarına uymayan haller ve benzerleri:
                a) İş sözleşmesi yapıldığı sırada bu sözleşmenin esaslı noktalarından biri için gerekli vasıflar 
                veya şartlar kendisinde bulunmadığı halde bunların kendisinde bulunduğunu ileri sürerek, 
                yahut gerçeğe uygun olmayan bilgiler veya sözler söyleyerek işçinin işvereni yanıltması.
                h) İşçinin yapmakla ödevli bulunduğu görevleri kendisine hatırlatıldığı halde yapmamakta ısrar etmesi.
                """
            }
        ]

        for item in sample_data:
            # 1. Ana Dokümanı Kaydet (Varsa güncelle, yoksa oluştur)
            doc, created = LegalDocument.objects.get_or_create(
                source_url=item["url"],
                defaults={
                    "title": item["title"],
                    "doc_type": item["doc_type"],
                    "raw_content": item["content"]
                }
            )

            if created:
                self.stdout.write(f"Yeni doküman eklendi: {doc.title}")
                # 2. Metni Parçala (Chunking) ve Kaydet
                self.create_chunks_for_document(doc)

        self.stdout.write(self.style.SUCCESS("Veriler başarıyla işlendi!"))

    def create_chunks_for_document(self, document, chunk_size=400, overlap=100):
        """
        Metni belirlenen karakter uzunluğunda ve örtüşmeli olarak parçalar.
        """
        text = document.raw_content
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            # Parçayı veritabanına kaydet
            DocumentChunk.objects.create(
                document=document,
                chunk_index=chunk_index,
                content=chunk_text.strip()
            )

            chunk_index += 1
            # Örtüşme (overlap) kadar geri giderek bir sonraki parçayı başlat
            start = end - overlap if end < len(text) else len(text)