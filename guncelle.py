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
    # --- HAYALET MOD ---
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # WebDriver kontrolünü gizle
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Site taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(5) 

        haber_linkleri = []
        
        # 1. LINKLERI TOPLA
        # Sayfadaki tüm linkleri al ve filtrele
        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue
        
        # Eğer az link varsa sayfayı aşağı kaydırıp tekrar dene
        if len(haber_linkleri) < 5:
            driver.execute_script("window.scrollTo(0, 1500);")
            time.sleep(3)
            elements_alt = driver.find_elements(By.TAG_NAME, "a")
            for el in elements_alt:
                try:
                    url = el.get_attribute('href')
                    if url and "/haber/" in url and url not in haber_linkleri:
                        haber_linkleri.append(url)
                except: continue

        print(f"Toplam {len(haber_linkleri)} link bulundu. İşleniyor...")

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')
        fg.language('tr')

        eklenen = 0
        
        # 2. İÇERİK DETAYLANDIRMA
        for link in haber_linkleri[:15]: 
            try:
                driver.get(link)
                time.sleep(2) 
                
                # --- Başlık ---
                try:
                    baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except: continue

                # --- Resim ---
                resim_html = ""
                try:
                    img_elem = driver.find_element(By.CSS_SELECTOR, "article img, main img, figure img")
                    img_src = img_elem.get_attribute("src")
                    if img_src:
                        resim_html = f'<img src="{img_src}" style="width:100%; display:block;"/><br/><br/>'
                except: pass

                # --- İçerik (Gelişmiş Seçici) ---
                full_text = ""
                yayin_tarihi = None 

                try:
                    # Haberin gövdesini bul
                    try: govde = driver.find_element(By.TAG_NAME, "article")
                    except: govde = driver.find_element(By.TAG_NAME, "main")

                    # KRİTİK NOKTA: Paragrafları (p), Ara Başlıkları (h2, h3) ve Listeleri (li) sırasıyla al
                    tum_icerik = govde.find_elements(By.CSS_SELECTOR, "p, h2, h3, h4, li")
                    
                    temiz_satirlar = []
                    tarih_bulundu = False
                    
                    # Bitirme Kelimeleri
                    bitis_kelimeleri = ["takip edebilirsiniz", "gdh digital", "sosyal medya", "------"]

                    for el in tum_icerik:
                        satir = el.text.strip()
                        tag = el.tag_name.lower() # Etiket türünü öğren (p mi, h2 mi?)
                        
                        if not satir: continue
                        
                        # A) Tarih Kontrolü
                        if "Son Güncelleme" in satir:
                            if not tarih_bulundu:
                                try:
                                    tarih_str = satir.replace("Son Güncelleme:", "").strip()
                                    dt = datetime.strptime(tarih_str, "%d.%m.%Y - %H:%M")
                                    yayin_tarihi = pytz.timezone('Europe/Istanbul').localize(dt)
                                    tarih_bulundu = True
                                except: pass
                            continue

                        # B) Haberi Bitirme Kontrolü
                        kucuk_satir = satir.lower()
                        if any(b in kucuk_satir for b in bitis_kelimeleri):
                            # Eğer satır çok kısaysa (sadece imza ise) bitir
                            if len(satir) < 60: break
                        
                        # C) Gereksizleri Atla
                        if "Kültür sanat" in satir or "Abone Ol" in satir or satir == baslik: continue

                        # D) FORMATLAMA (İşaretlediğin yer burası sayesinde kalın olacak)
                        if tag in ['h2', 'h3', 'h4']:
                            # Başlıkları kalın yap
                            temiz_satirlar.append(f"<br/><b>{satir}</b>")
                        elif tag == 'li':
                            # Listelere nokta koy
                            temiz_satirlar.append(f"• {satir}")
                        else:
                            # Normal paragraflar (Kısa cümleleri de alıyoruz, filtreyi kıstık)
                            if len(satir) > 10: 
                                temiz_satirlar.append(satir)
                    
                    full_text = "<br/><br/>".join(temiz_satirlar)

                except: pass

                if len(full_text) < 20: full_text = "İçerik okunamadı."

                # --- RSS Ekleme ---
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
            except: continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} haber eklendi.")

    except Exception as e:
        # Hata olursa açıkça yazdır ve programı hata koduyla kapat (Böylece GitHub'da Kırmızı Çarpı çıkar)
        print(f"KRİTİK HATA: {e}")
        exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
