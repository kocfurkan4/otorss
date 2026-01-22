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
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("Gdh Savunma taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(5) 

        haber_linkleri = []
        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except: continue
        
        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')
        fg.language('tr')

        # --- FİLTRE AYARLARI ---
        # Bu kelimeler geçiyorsa o satırı XML'den siler ama okumaya devam eder
        ignore_list = ["abone ol", "paylaş", "editör", "a+a-", "son güncelleme", "gdh tv", "gdh haber", "nsosyal"]
        
        # Bu kelimeleri gördüğü an haber bitmiştir, alttaki reklamları almaz
        stop_list = ["etiketler", "ilgili haberler", "gdh uygulamasını", "diğer haberler", "yorumlar"]

        eklenen = 0
        for link in haber_linkleri[:15]: 
            try:
                driver.get(link)
                time.sleep(2) 
                
                try: baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except: continue

                temiz_satirlar = []
                yayin_tarihi = None

                # İçerik alanını bul (Article veya Main içindeki metinler)
                govde = driver.find_element(By.CSS_SELECTOR, "main, article")
                parçalar = govde.find_elements(By.CSS_SELECTOR, "h2, h3, p, li")

                for p in parçalar:
                    metin = p.text.strip()
                    metin_kucuk = metin.lower()
                    tag = p.tag_name.lower()

                    if not metin or metin == baslik: continue

                    # 1. TARİHİ ÇEK (Sadece sistem için, metne yazma)
                    if "son güncelleme" in metin_kucuk:
                        try:
                            t_str = metin.split(":")[-1].strip()
                            dt = datetime.strptime(t_str, "%d.%m.%Y - %H:%M")
                            yayin_tarihi = pytz.timezone('Europe/Istanbul').localize(dt)
                        except: pass
                        continue

                    # 2. DURDURUCU KONTROLÜ (Haberin sonuna gelindi mi?)
                    # "Etiketler" veya "Uygulamayı indir" görünce haberi keser
                    if any(stop in metin_kucuk for stop in stop_list):
                        break

                    # 3. ATLANACAKLAR KONTROLÜ (Editör ismi, Sosyal Medya butonu vb.)
                    if any(ignore in metin_kucuk for ignore in ignore_list):
                        continue

                    # 4. FORMATLAMA (Alt alta ve okunaklı düzen)
                    if tag in ['h2', 'h3']:
                        # Ara başlıkları kalın yap ve önüne boşluk ekle
                        temiz_satirlar.append(f"<br/><b>{metin}</b>")
                    elif tag == 'li':
                        # Liste maddelerini belirgin yap
                        temiz_satirlar.append(f"• {metin}")
                    else:
                        # Normal paragrafları olduğu gibi al
                        if len(metin) > 20: 
                            temiz_satirlar.append(metin)

                # Paragraflar arasına çift boşluk koyarak Defense News tarzı alt alta düzen oluştur
                full_text = "<br/><br/>".join(temiz_satirlar)

                # RSS Girişi
                fe = fg.add_entry()
                fe.id(link)
                fe.link(href=link)
                fe.title(baslik)
                if yayin_tarihi: fe.published(yayin_tarihi)
                else: fe.published(datetime.now(pytz.timezone('Europe/Istanbul')))
                
                # İçeriği alt alta düzenlenmiş metin olarak ekle (Fotoğraf yok)
                fe.description(full_text) 
                
                print(f"Eklendi: {baslik}")
                eklenen += 1
            except: continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İşlem Tamam: {eklenen} haber Defense News tarzı okunaklı hale getirildi.")

    except Exception as e:
        print(f"Hata: {e}")
        exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
