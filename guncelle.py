import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

def haberleri_cek():
    options = Options()
    # Headless modu anti-bot sistemleri tarafindan tespit edilebilir, 
    # bu yuzden ekstra gizlilik ayarlari ekliyoruz:
    options.add_argument("--headless=new") # Daha yeni headless modu
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled") # Robot oldugunu gizle
    options.add_argument("--window-size=1920,1080") # Gercek monitor cozunurlugu
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Selenium izlerini temizle
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Navigator.webdriver ozelligini sil (En onemli gizlilik adimi)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Siteye baglaniliyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(15) 
        
        # DEBUG: Siteye gercekten girdik mi? Basligi yazdir.
        sayfa_basligi = driver.title
        print(f"SITE BASLIGI: {sayfa_basligi}")
        
        # Eger baslikta 'Access Denied' veya 'Security' varsa engelleniyoruz demektir.
        
        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(5)
        
        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')

        # Link bulma stratejisini genisletiyoruz (Tum linkleri alip Python'da suzecegiz)
        tum_linkler = driver.find_elements(By.TAG_NAME, "a")
        
        eklenen = 0
        gorulenler = set()

        print(f"Sayfada toplam {len(tum_linkler)} adet link bulundu. Taranıyor...")

        for el in tum_linkler:
            try:
                link = el.get_attribute('href')
                baslik = el.text.strip()
                
                # Linkin gecerliligini kontrol et
                if not link or "savunma" not in link or link in gorulenler:
                    continue
                
                # "5°" gibi kisa basliklari ele
                if len(baslik) < 20 or "°" in baslik:
                    # Baslik yoksa belki resmin altindadir, title attribute'una bak
                    alt_baslik = el.get_attribute('title')
                    if alt_baslik and len(alt_baslik) > 20:
                        baslik = alt_baslik
                    else:
                        continue

                # RSS'e ekle
                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                fe.description(baslik) # Basitlik icin simdilik sadece baslik
                
                gorulenler.add(link)
                eklenen += 1
                
                if eklenen >= 15: break
            except:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"ISLEM TAMAM: {eklenen} haber eklendi.")

    except Exception as e:
        print(f"KRITIK HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
