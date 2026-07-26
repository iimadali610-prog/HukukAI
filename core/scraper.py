import httpx
from bs4 import BeautifulSoup
import re


class LiveLegalScraper:
    """
    Sorulan konuya özel canlı mevzuat ve yargıtay kararı özetlerini çeker.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch_legal_info(self, query: str) -> list[dict]:
        results = []
        try:
            # Hukuki terimleri öne çıkaran net arama sorgusu
            search_term = f"{query} mevzuat maddesi yargıtay kararı"
            url = f"https://html.duckduckgo.com/html/?q={search_term}"

            response = httpx.get(url, headers=self.headers, timeout=8.0, follow_redirects=True)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.find_all('div', class_='result__body', limit=4)

                for idx, item in enumerate(search_results, 1):
                    title_elem = item.find('a', class_='result__url')
                    snippet_elem = item.find('a', class_='result__snippet')

                    if snippet_elem:
                        title = title_elem.get_text(strip=True) if title_elem else f"İlgili Hukuki Kaynak {idx}"
                        snippet = snippet_elem.get_text(strip=True)

                        clean_text = re.sub(r'\s+', ' ', snippet)

                        # Eğer çekilen metin gerçekten anlamlıysa ekle
                        if len(clean_text) > 40:
                            results.append({
                                "title": f"Mevzuat / İçtihat Dayanağı: {title[:60]}...",
                                "url": "https://mevzuat.gov.tr",
                                "content": clean_text
                            })

        except Exception as e:
            print(f"Scraper hatası: {e}")

        return results