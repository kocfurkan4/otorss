import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

def haberleri_cek():
    options = Options()
    # --- HAYALET MOD (Cloudflare ve Bot Koruması İçin) ---
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("1. ADIM: Ana sayfa taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(8)
        
        # Sayfayı aşağı kaydır (Haberlerin yüklenmesi için)
        print("   Sayfa kaydırılıyor...")
        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(4)

        # Sadece linkleri toplayalım
        # BURASI KRİTİK: Sadece içinde '/haber/' geçen linkleri alıyoruz.
        ham_elementler = driver.find_elements(By.TAG_NAME, "a")
        haber_linkleri = []
        
        print(f"   Linkler filtreleniyor (Kriter: '/haber/')...")
        
        for el in ham_elementler:
            try:
                url = el.get_attribute('href')
                
                # --- FİLTRELEME ---
                if not url: continue
                
                # 1. Link kesinlikle '/haber/' içermeli (Shorts/Video engeli)
                if "/haber/" not in url:
                    continue
                
                # 2. Ana sayfa veya kategori linki olmamalı
                if url == "https://gdh.digital/haber" or len(url) < 35:
                    continue

                if url not in haber_linkleri:
                    haber_linkleri.append(url)
            except:
                continue

        print(f"   Toplam {len(haber_linkleri)} adet 'haber' formatında makale bulundu.")

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Tam Makale')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma sanayii makaleleri (Tam metin)')

        eklenen = 0
        
        # 2. ADIM: HER HABERİN İÇİNE GİR
        # Performans için son 10 haberi çekiyoruz
        for link in haber_linkleri[:10]:
            try:
                print(f"   Okunuyor: {link}")
                driver.get(link)
                time.sleep(3) # İçeriğin yüklenmesi için bekle
                
                # --- BAŞLIK AL ---
                try:
                    baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except:
                    continue # Başlığı olmayan sayfa bozuktur

                # --- RESİM AL ---
                resim_html = ""
                try:
                    img_elem = driver.find_element(By.CSS_SELECTOR, "article img, .post-content img, figure img")
                    img_src = img_elem.get_attribute("src")
                    if img_src:
                        resim_html = f'<img src="{img_src}" style="width:100%; display:block;"/><br/>'
                except:
                    pass

                # --- TAM METİN AL (Paragraf Birleştirme) ---
                full_text = ""
                try:
                    # 'article' etiketi içindeki tüm 'p' (paragraf) etiketlerini bul
                    paragraflar = driver.find_elements(By.CSS_SELECTOR, "article p, .content p, .post-body p")
                    
                    text_parts = []
                    for p in paragraflar:
                        text = p.text.strip()
                        # Reklam metinlerini veya boş satırları atla
                        if len(text) > 20:
                            text_parts.append(text)
                    
                    # Paragrafları alt alta birleştir
                    full_text = "<br/><br/>".join(text_parts)
                except:
                    pass

                # Eğer metin çekemediysek (Sadece resim varsa) yine de ekle ama kısa olsun
                if not full_text:
                    full_text = "Haber detayı için linke tıklayın."

                # --- RSS KAYDI ---
                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                # Resim + Metin formatında açıklama
                fe.description(f"{resim_html}{full_text}")
                
                eklenen += 1

            except Exception as e:
                print(f"   Hata: {e}")
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} makale başarıyla eklendi.")

    except Exception as e:
        print(f"GENEL HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
