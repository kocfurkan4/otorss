import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

def haberleri_cek():
    options = Options()
    # --- HAYALET MOD AYARLARI ---
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Siteye baglaniliyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(10)
        
        # 1. Sayfayi parca parca asagi kaydir (Daha fazla haber icin)
        print("Sayfa kaydiriliyor...")
        for i in range(1, 5):
            driver.execute_script(f"window.scrollTo(0, {i * 1000});")
            time.sleep(2)

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')

        # 2. ONCE VERILERI TOPLA (Stale Element Hatasini Onlemek Icin)
        # Elementleri direkt islemek yerine, link ve basliklari listeye aliyoruz.
        ham_elementler = driver.find_elements(By.TAG_NAME, "a")
        haber_verileri = []
        
        print(f"Toplam {len(ham_elementler)} ham link bulundu. Veriler aliniyor...")

        for el in ham_elementler:
            try:
                # Link ve basligi metin olarak alip hafizaya atiyoruz
                url = el.get_attribute('href')
                baslik = el.get_attribute('innerText').strip() # innerText bazen text'ten daha iyidir
                
                # Title attribute kontrolu (Resim linkleri icin)
                if not baslik:
                    baslik = el.get_attribute('title')
                
                if url and "/savunma/" in url:
                    haber_verileri.append({"link": url, "baslik": baslik})
            except:
                continue # Hatalı elementi atla

        # 3. VERILERI ISLE VE RSS OLUSTUR
        print(f"{len(haber_verileri)} aday haber isleniyor...")
        
        eklenen = 0
        gorulenler = set()

        for veri in haber_verileri:
            link = veri['link']
            baslik = veri['baslik']

            # Filtreler
            if not link or link == "https://gdh.digital/savunma" or link in gorulenler:
                continue
            
            # Baslik kontrolu (Bos veya cok kisa ise atla)
            if not baslik or len(baslik) < 15 or "°" in baslik:
                continue

            fe = fg.add_entry()
            fe.id(link)
            fe.title(baslik)
            fe.link(href=link)
            fe.description(baslik)
            
            gorulenler.add(link)
            eklenen += 1
            
            # 30 habere ulasinca dur
            if eklenen >= 30: break

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"ISLEM TAMAM: {eklenen} haber RSS dosyasina basariyla yazildi.")

    except Exception as e:
        print(f"HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
