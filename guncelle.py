import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

def haberleri_cek():
    options = Options()
    # --- HAYALET MOD AYARLARI (Dokunmayin) ---
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
        time.sleep(10) # Ilk yukleme icin bekle
        
        # --- YENILIK: COKLU KAYDIRMA (Scroll Loop) ---
        # Sayfayi 5 kez, her seferinde 1000 piksel asagi kaydir
        print("Daha fazla haber icin asagi kaydiriliyor...")
        for i in range(1, 6):
            driver.execute_script(f"window.scrollTo(0, {i * 1200});")
            time.sleep(3) # Her kaydirmada yuklenmesini bekle

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')

        # Tum linkleri topla
        tum_linkler = driver.find_elements(By.TAG_NAME, "a")
        print(f"Toplam {len(tum_linkler)} link bulundu, ayiklaniyor...")

        eklenen = 0
        gorulenler = set()

        for el in tum_linkler:
            try:
                link = el.get_attribute('href')
                baslik = el.text.strip()
                
                # --- FILTRELEME ---
                # 1. Link bos olmamali ve 'savunma' icermeli
                # 2. Daha once eklenmemis olmali
                if not link or "/savunma/" not in link or link in gorulenler:
                    continue
                
                # 3. Baslik cok kisa olmamali (Menuleri eler)
                # 4. Derece isareti (hava durumu) olmamali
                if len(baslik) < 15 or "°" in baslik:
                    # Metin yoksa title'a bak (Bazen resimlerin icindedir)
                    alt_baslik = el.get_attribute('title')
                    if alt_baslik and len(alt_baslik) > 15:
                        baslik = alt_baslik
                    else:
                        continue

                # RSS'e Ekle
                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                
                # Resim bulmaya calis (Opsiyonel)
                try:
                    img = el.find_element(By.TAG_NAME, "img").get_attribute("src")
                    fe.description(f'<img src="{img}"/><br/>{baslik}')
                except:
                    fe.description(baslik)
                
                gorulenler.add(link)
                eklenen += 1
                
                # Limit: 25 habere kadar al
                if eklenen >= 25: break
            except:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"ISLEM TAMAM: {eklenen} haber RSS dosyasina yazildi.")

    except Exception as e:
        print(f"HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
