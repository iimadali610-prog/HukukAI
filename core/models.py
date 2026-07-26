from django.db import models
from pgvector.django import VectorField


class DocumentType(models.TextChoices):
    """Doküman türlerini belirlediğimiz seçenek listesi."""
    KANUN = 'KANUN', 'Mevzuat / Kanun'
    YARGITAY = 'YARGITAY', 'Yargıtay Kararı'
    AYM = 'AYM', 'Anayasa Mahkemesi Kararı'


class LegalDocument(models.Model):
    """
    Ana Hukuk Dokümanı Tablosu.
    Çektiğimiz kararların ve kanunların üst bilgilerini saklar.
    """
    title = models.CharField(max_length=500, verbose_name="Başlık / Emsal No")
    doc_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.YARGITAY
    )
    source_url = models.URLField(unique=True, verbose_name="Kaynak Adresi")
    raw_content = models.TextField(verbose_name="Ham Metin")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_doc_type_display()}] {self.title}"


class DocumentChunk(models.Model):
    """
    RAG Mimarisi için Parçalanmış Metinler Tablosu.
    Büyük metinler buraya küçük parçalar halinde bölünerek kaydedilir.
    """
    document = models.ForeignKey(
        LegalDocument,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.IntegerField(help_text="Parçanın metin içindeki sırası")
    content = models.TextField(verbose_name="Parça Metni")

    # Gemini 'text-embedding-004' modeli 768 boyutlu vektörler üretir.
    # pgvector bu alanı otomatik olarak sayı dizisi olarak saklar.
    embedding = VectorField(dimensions=768, blank=True, null=True)

    def __str__(self):
        return f"{self.document.title} - Parça {self.chunk_index}"