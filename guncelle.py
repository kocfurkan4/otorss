import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

def haberleri_cek():
    options = Options()
    # --- HAYALET MOD (Guvenlik Duvari Asici) ---
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # 1. ADIM: LINKLERI TOPLA
        print("Ana sayfa taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(8)
        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(3)

        # Sadece linkleri toplayalim
        ham_elementler = driver.find_elements(By.CSS_SELECTOR, "a[href*='/savunma/']")
        haber_linkleri = []
        for el in ham_elementler:
            try:
                url = el.get_attribute('href')
                if url and url not in haber_linkleri and url != "https://gdh.digital/savunma":
                    haber_linkleri.append(url)
            except:
                continue

        print(f"Toplam {len(haber_linkleri)} link bulundu. Detaylı tarama başlıyor...")

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Tam İçerik')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma haberleri tam metin akışı')

        eklenen = 0
        
        # 2. ADIM: HER LINKIN ICINE GIR (Deep Crawl)
        # Performans icin son 10 haberi cekiyoruz (Sayiyi artirabilirsin)
        for link in haber_linkleri[:10]:
            try:
                driver.get(link)
                time.sleep(3) # Sayfanin iceriginin yuklenmesi icin bekle
                
                # --- BASLIK BULMA ---
                try:
                    baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except:
                    # h1 yoksa title'dan al
                    baslik = driver.title.split('|')[0].strip()

                if not baslik or len(baslik) < 10:
                    continue

                # --- RESIM BULMA ---
                resim_html = ""
                try:
                    # Makalenin ana resmini bulmaya calis
                    img_elem = driver.find_element(By.CSS_SELECTOR, "article img, .post-content img, figure img")
                    img_src = img_elem.get_attribute("src")
                    if img_src:
                        resim_html = f'<img src="{img_src}" style="width:100%;"/><br/><br/>'
                except:
                    pass

                # --- TUM METNI BULMA (Paragraf Birlestirme) ---
                # Burasi cok onemli: Aradaki resimleri/sesleri atlayip sadece <p> etiketlerini alir
                full_text = ""
                try:
                    # Makale govdesindeki tum paragraflari bul
                    paragraflar = driver.find_elements(By.CSS_SELECTOR, "article p, .content p, .post-body p, main p")
                    
                    text_parts = []
                    for p in paragraflar:
                        text = p.text.strip()
                        # Bos veya cok kisa (reklam/tarih vb.) paragraflari alma
                        if len(text) > 20:
                            text_parts.append(text)
                    
                    # Paragraflari birlestir
                    full_text = "<br/><br/>".join(text_parts)
                except:
                    full_text = "Icerik alinamadi."

                # Eger metin cekemediysek RSS'e ekleme
                if len(full_text) < 50:
                    continue

                # RSS KAYDI
                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                # Resim + Tam Metin seklinde kaydet
                fe.description(f"{resim_html}{full_text}")
                
                print(f"Eklendi: {baslik[:30]}...")
                eklenen += 1

            except Exception as e:
                print(f"Hata ({link}): {e}")
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"ISLEM TAMAM: {eklenen} tam içerikli haber oluşturuldu.")

    except Exception as e:
        print(f"GENEL HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
