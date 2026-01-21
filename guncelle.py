import time
from datetime import datetime
import pytz 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator
from newspaper import Article # AI Kütüphanesi

def haberleri_cek():
    options = Options()
    # --- HAYALET MOD (Cloudflare engelini aşmak için) ---
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Site taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(5) 

        haber_linkleri = []
        
        # 1. LINKLERI TOPLA
        print("Linkler toplanıyor...")
        
        # Manşetler
        linkler_tepe = driver.find_elements(By.TAG_NAME, "a")
        for el in linkler_tepe:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue

        # Aşağı Liste
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(3)
        linkler_alt = driver.find_elements(By.TAG_NAME, "a")
        for el in linkler_alt:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue
        
        print(f"Toplam {len(haber_linkleri)} link bulundu. AI analizi başlıyor...")

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')
        fg.language('tr')

        eklenen = 0
        
        # 2. AI ILE ANALIZ (NEWSPAPER3K)
        for link in haber_linkleri[:15]: 
            try:
                # Once Selenium ile sayfayi ac (Guvenlik duvarini asmak icin)
                driver.get(link)
                time.sleep(2)
                
                # HTML kaynagini alip AI kütüphanesine veriyoruz
                html_kaynagi = driver.page_source
                
                makale = Article(link)
                makale.set_html(html_kaynagi) # Cloudflare'e takilmamak icin Selenium'un actigi kaynagi veriyoruz
                makale.parse() # AI okumaya başlıyor
                
                # Verileri Cek
                baslik = makale.title
                resim_url = makale.top_image
                ham_metin = makale.text # Otomatik temizlenmiş metin
                
                # Ufak bir son temizlik (Takip et yazılarını silmek için)
                temiz_satirlar = []
                for satir in ham_metin.split('\n'):
                    satir = satir.strip()
                    if not satir: continue
                    
                    # AI'ın kaçırabileceği imza kısımlarını elle kesiyoruz
                    kucuk_satir = satir.lower()
                    if "takip edebilirsiniz" in kucuk_satir: break
                    if "gdh digital" in kucuk_satir and len(satir) < 30: break
                    if "------" in kucuk_satir: break
                    
                    temiz_satirlar.append(satir)
                
                full_text = "<br/><br/>".join(temiz_satirlar)

                # Tarih (AI otomatik bulur)
                try:
                    tarih = makale.publish_date
                    if tarih:
                        tarih = tarih.replace(tzinfo=pytz.timezone('Europe/Istanbul'))
                    else:
                        # Bulamazsa şimdiği koy
                        tarih = datetime.now(pytz.timezone('Europe/Istanbul'))
                except:
                    tarih = datetime.now(pytz.timezone('Europe/Istanbul'))

                # Resim HTML kodu
                resim_html = ""
                if resim_url:
                     resim_html = f'<img src="{resim_url}" style="width:100%; display:block;"/><br/><br/>'

                # --- KAYIT ---
                fe = fg.add_entry()
                fe.id(link)
                fe.link(href=link)
                fe.title(baslik)
                fe.published(tarih)
                fe.description(f"{resim_html}{full_text}")
                
                print(f"Eklendi (AI): {baslik}")
                eklenen += 1

            except Exception as e:
                print(f"Hata: {e}")
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} haber analiz edildi.")

    except Exception as e:
        print(f"HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
