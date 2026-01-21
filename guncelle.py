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
        
        # 1. LINK TOPLAMA (Manşet + Liste)
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
        
        print(f"Toplam {len(haber_linkleri)} makale bulundu.")

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')
        fg.language('tr')

        eklenen = 0
        
        # 2. DETAYLI İÇERİK ANALİZİ
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

                # --- GELİŞMİŞ METİN TOPLAYICI ---
                full_text = ""
                yayin_tarihi = None 

                try:
                    # Gövdeyi bul
                    govde = None
                    try: govde = driver.find_element(By.TAG_NAME, "article")
                    except: govde = driver.find_element(By.TAG_NAME, "main")

                    # BURASI YENİ: Sadece düz yazı değil, HTML elemanlarını türüne göre topluyoruz.
                    # p: Paragraf, h2-h3: Ara başlıklar, li: Liste maddeleri, blockquote: Alıntılar
                    elementler = govde.find_elements(By.CSS_SELECTOR, "p, h2, h3, h4, li, blockquote, div.content-text")
                    
                    temiz_satirlar = []
                    
                    # Bitiş Kelimeleri (Görünce haberi kes)
                    bitis_kelimeleri = ["takip edebilirsiniz", "takip edin", "gdh digital", "sosyal medya", "------"]

                    tarih_bulundu = False

                    for el in elementler:
                        # Metni al
                        satir = el.text.strip()
                        satir_kucuk = satir.lower()
                        
                        if not satir: continue

                        # A) TARİH (Varsa al ve metne ekleme)
                        if "Son Güncelleme" in satir:
                            if not tarih_bulundu: # Sadece ilk bulduğunu al
                                try:
                                    tarih_str = satir.replace("Son Güncelleme:", "").strip()
                                    dt = datetime.strptime(tarih_str, "%d.%m.%Y - %H:%M")
                                    tz = pytz.timezone('Europe/Istanbul')
                                    yayin_tarihi = tz.localize(dt)
                                    tarih_bulundu = True
                                except: pass
                            continue 

                        # B) BİTİRİCİ (Haberi Kes)
                        if any(kelime in satir_kucuk for kelime in bitis_kelimeleri):
                            # Eğer bu satır çok kısaysa (sadece imza ise) direk bitir.
                            # Eğer uzun bir paragrafın içindeyse (bazen oluyor), o paragrafı alma ve bitir.
                            break
                        
                        # C) FİLTRELER (Gereksizleri At)
                        if "Kültür sanat" in satir: continue
                        if "Abone Ol" in satir: continue
                        if "İlgili Haberler" in satir: continue
                        if satir == baslik: continue 

                        # D) EKRANA YAZDIRMA KURALI
                        # Başlık etiketleri (h2, h3) ise kalın yazdır
                        tag_name = el.tag_name.lower()
                        
                        if tag_name in ['h2', 'h3', 'h4']:
                            temiz_satirlar.append(f"<b>{satir}</b>")
                        elif tag_name == 'li':
                            temiz_satirlar.append(f"• {satir}")
                        else:
                            # Normal paragraf - Karakter sınırını 15'e indirdik!
                            if len(satir) > 15:
                                temiz_satirlar.append(satir)
                    
                    full_text = "<br/><br/>".join(temiz_satirlar)

                except Exception as e:
                    pass

                if len(full_text) < 20:
                    full_text = "Haber detayı için kaynağa gidiniz."

                # --- KAYIT ---
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
