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
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Site taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(5) 

        haber_linkleri = []
        
        # 1. LINKLERI TOPLA
        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue
        
        # Link azsa kaydır
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

                # --- İçerik ---
                full_text = ""
                yayin_tarihi = None 

                try:
                    try: govde = driver.find_element(By.TAG_NAME, "article")
                    except: govde = driver.find_element(By.TAG_NAME, "main")

                    tum_icerik = govde.find_elements(By.CSS_SELECTOR, "p, h2, h3, h4, li")
                    
                    temiz_satirlar = []
                    tarih_bulundu = False
                    
                    # --- GENİŞLETİLMİŞ KARA LİSTE ---
                    # Bu kelimelerden birini gördüğü AN haberi keser.
                    bitis_kelimeleri = [
                        "takip edebilirsiniz", 
                        "gdh digital", 
                        "sosyal medya", 
                        "------",
                        "uygulamasını indir",     # XML'deki hatayı çözen kısım
                        "gelişmelerden anında",   # XML'deki hatayı çözen kısım
                        "ilgili haberler",
                        "diğer haberler",
                        "öne çıkan",
                        "etiketler",
                        "abone ol"
                    ]

                    for el in tum_icerik:
                        satir = el.text.strip()
                        tag = el.tag_name.lower()
                        
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

                        # B) Haberi Bitirme (Kara Liste)
                        kucuk_satir = satir.lower()
                        # Eğer satırda yasaklı kelime varsa DÖNGÜYÜ KIR (break)
                        if any(b in kucuk_satir for b in bitis_kelimeleri):
                            break 
                        
                        # C) Gereksizleri Atla (Satır Bazlı)
                        if "Kültür sanat" in satir or "Abone Ol" in satir or satir == baslik: continue

                        # D) FORMATLAMA (Kalın Başlıklar Korunur)
                        if tag in ['h2', 'h3', 'h4']:
                            temiz_satirlar.append(f"<br/><b>{satir}</b>")
                        elif tag == 'li':
                            temiz_satirlar.append(f"• {satir}")
                        else:
                            # 10 karakterden uzunsa al
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
        print(f"KRİTİK HATA: {e}")
        exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
