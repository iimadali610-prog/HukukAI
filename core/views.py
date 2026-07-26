from django.shortcuts import render
from django.http import JsonResponse
from .services import LegalAIService


def index(request):
    """Ana Arama Sayfasını Yükler."""
    return render(request, 'index.html')


def legal_search_api(request):
    """
    Ön yüzden (Frontend) gelen soruyu alır, LegalAIService'e iletir
    ve sonucu JSON olarak döndürür. Sayfa yenilenmeden çalışır.
    """
    if request.method == "POST":
        query = request.POST.get("query", "").strip()
        if not query:
            return JsonResponse({"error": "Lütfen hukuki bir soru veya olay anlatımı giriniz."}, status=400)

        try:
            service = LegalAIService()
            result = service.answer_query(query)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": f"Sorgu işlenirken bir hata oluştu: {str(e)}"}, status=500)

    return JsonResponse({"error": "Geçersiz istek türü."}, status=400)