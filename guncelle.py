import time
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
        print("1. ADIM: Siteye giriliyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(5) # Sayfanın ilk yüklenişi

        haber_linkleri = []
        
        # --- DÜZELTME 1: MANŞETLERİ KAÇIRMAMAK İÇİN İKİ AŞAMALI TARAMA ---
        
        # A) Önce HİÇ kaydırmadan en tepedeki (Manşet/Slider) linkleri al
        print("   Manşetler taranıyor...")
        linkler_tepe = driver.find_elements(By.TAG_NAME, "a")
        for el in linkler_tepe:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except:
                continue

        # B) Şimdi sayfayı aşağı kaydır ve listenin geri kalanını al
        print("   Aşağı iniliyor (Liste haberleri)...")
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(3)
        
        linkler_alt = driver.find_elements(By.TAG_NAME, "a")
        for el in linkler_alt:
            try:
                url = el.get_attribute('href')
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except:
                continue
        
        print(f"Toplam {len(haber_linkleri)} benzersiz haber bulundu. İçerik çekiliyor...")

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Tam Kapsam')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma haberleri')

        eklenen = 0
        
        # 2. ADIM: İÇERİK ÇEKME
        for link in haber_linkleri[:15]: # İlk 15 haberi al (Manşetler dahil)
            try:
                driver.get(link)
                time.sleep(2) 
                
                # Başlık
                try:
                    baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except:
                    continue

                # Resim
                resim_html = ""
                try:
                    img_elem = driver.find_element(By.CSS_SELECTOR, "article img, main img")
                    img_src = img_elem.get_attribute("src")
                    if img_src:
                        resim_html = f'<img src="{img_src}" style="width:100%; display:block;"/><br/><br/>'
                except:
                    pass

                # --- DÜZELTME 2: KARAKTER SINIRI GEVŞETİLDİ ---
                full_text = ""
                try:
                    # Gövdeyi bul
                    govde = None
                    try:
                        govde = driver.find_element(By.TAG_NAME, "article")
                    except:
                        govde = driver.find_element(By.TAG_NAME, "main")

                    ham_metin = govde.text 
                    satirlar = ham_metin.split('\n')
                    temiz_satirlar = []
                    
                    for satir in satirlar:
                        satir = satir.strip()
                        # ESKİ KOD: if len(satir) > 50 (Çok agresifti)
                        # YENİ KOD: if len(satir) > 25 (Kısa cümleleri de alır)
                        if len(satir) > 25 and satir != baslik:
                            # Yasaklı kelimeler (reklam/menu vb.)
                            if "Abone Ol" not in satir and "Takip Et" not in satir:
                                temiz_satirlar.append(satir)
                    
                    full_text = "<br/><br/>".join(temiz_satirlar)

                except Exception as e:
                    pass

                if len(full_text) < 20:
                    full_text = "Haber metni okunamadı."

                # Kaydet
                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                fe.description(f"{resim_html}{full_text}")
                
                print(f"Eklendi: {baslik}")
                eklenen += 1

            except Exception as e:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} haber başarıyla eklendi.")

    except Exception as e:
        print(f"HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
