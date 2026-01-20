import requests
from feedgen.feed import FeedGenerator
from datetime import datetime

def haberleri_cek():
    # Gdh'ın arka planda veri çektiği API adresi (Savunma kategorisi için)
    # Not: Bu URL sitenin mobil/web veri yoludur.
    api_url = "https://gdh.digital/api/posts?category=savunma&limit=15"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=20)
        data = response.json()
        
        fg = FeedGenerator()
        fg.title('Gdh Savunma | Hızlı Besleme')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma sanayii haberleri API botu')
        fg.language('tr')

        eklenen = 0
        # API'den gelen veriyi işle
        # Gdh API yapısına göre 'posts' veya direkt liste dönebilir
        posts = data.get('posts', data) if isinstance(data, dict) else data

        for post in posts:
            try:
                # API'den başlık, link ve resim bilgilerini al
                baslik = post.get('title', '').strip()
                slug = post.get('slug', '')
                link = f"https://gdh.digital/savunma/{slug}"
                resim = post.get('featured_image', '')

                # 5° gibi verileri engellemek için filtre
                if not baslik or len(baslik) < 20 or "°" in baslik:
                    continue

                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                fe.description(f'<img src="{resim}"/><br/>{baslik}')
                
                eklenen += 1
            except:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"API üzerinden {eklenen} haber çekildi.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    haberleri_cek()
