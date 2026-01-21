import time
from datetime import datetime
import pytz 
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
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Site taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(5) 

        haber_linkleri = []
        
        # 1. LINKLERI TOPLA
        # Once tepedeki manşetler
        linkler_tepe = driver.find_elements(By.TAG_NAME, "a")
        for el in linkler_tepe:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue

        # Asagi kaydir ve devamini al
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(3)
        linkler_alt = driver.find_elements(By.TAG_NAME, "a")
        for el in linkler_alt:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue
        
        print(f"Toplam {len(haber_linkleri)} makale bulundu.")

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')
        fg.language('tr')

        eklenen = 0
        
        # 2. ICERIK DETAYLANDIRMA
        for link in haber_linkleri[:15]: 
            try:
                driver.get(link)
                time.sleep(2) 
                
                # --- BAŞLIK ---
                try:
                    baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except: continue

                # --- RESİM ---
                resim_html = ""
                try:
                    img_elem = driver.find_element(By.CSS_SELECTOR, "article img, main img")
                    img_src = img_elem.get_attribute("src")
                    if img_src:
                        resim_html = f'<img src="{img_src}" style="width:100%; display:block;"/><br/><br/>'
                except: pass

                # --- METİN VE TARİH ---
                full_text = ""
                yayin_tarihi = None 

                try:
                    govde = None
                    try: govde = driver.find_element(By.TAG_NAME, "article")
                    except: govde = driver.find_element(By.TAG_NAME, "main")

                    ham_metin = govde.text 
                    satirlar = ham_metin.split('\n')
                    temiz_satirlar = []
                    
                    for satir in satirlar:
                        satir = satir.strip()
                        
                        # A) TARIH AYIKLAMA (Son Güncelleme: XX.XX.XXXX - XX:XX)
                        if "Son Güncelleme" in satir:
                            try:
                                tarih_str = satir.replace("Son Güncelleme:", "").strip()
                                dt = datetime.strptime(tarih_str, "%d.%m.%Y - %H:%M")
                                tz = pytz.timezone('Europe/Istanbul')
                                yayin_tarihi = tz.localize(dt)
                            except: pass
                            continue 

                        # B) KESİCİ (Haber Bitişi)
                        if "takip edebilirsiniz" in satir: 
                            break 
                        
                        # C) FİLTRELER
                        if "Kültür sanat" in satir: continue
                        if "Abone Ol" in satir: continue
                        if satir == baslik: continue 

                        # D) Metni Ekle (Kısa cümleler dahil)
                        if len(satir) > 25:
                            temiz_satirlar.append(satir)
                    
                    full_text = "<br/><br/>".join(temiz_satirlar)

                except Exception as e:
                    pass

                if len(full_text) < 20:
                    full_text = "İçerik detayı için habere gidin."

                # --- RSS KAYDI ---
                fe = fg.add_entry()
                fe.id(link)
                fe.link(href=link)
                fe.title(baslik)
                
                if yayin_tarihi:
                    fe.published(yayin_tarihi)
                else:
                    fe.published(datetime.now(pytz.timezone('Europe/Istanbul')))

                fe.description(f"{resim_html}{full_text}")
                
                print(f"Eklendi: {baslik}")
                eklenen += 1

            except Exception as e:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} haber eklendi.")

    except Exception as e:
        print(f"HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
