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
        print("1. ADIM: Site taranıyor...")
        driver.get("https://gdh.digital/savunma")
        time.sleep(8)
        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(4)

        # LINKLERI TOPLA
        ham_elementler = driver.find_elements(By.TAG_NAME, "a")
        haber_linkleri = []
        for el in ham_elementler:
            try:
                url = el.get_attribute('href')
                # Sadece makaleler (/haber/)
                if url and "/haber/" in url and url not in haber_linkleri:
                    haber_linkleri.append(url)
            except:
                continue
        
        print(f"Toplam {len(haber_linkleri)} makale bulundu. İçerik çekiliyor...")

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Tam Metin')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma haberleri')

        eklenen = 0
        
        # 2. ADIM: ICERIK CEKME (KONTEYNER YONTEMI)
        for link in haber_linkleri[:12]:
            try:
                driver.get(link)
                time.sleep(3) 
                
                # --- BAŞLIK ---
                try:
                    baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                except:
                    continue

                # --- RESİM ---
                resim_html = ""
                try:
                    # Haberin en büyük resmini bulmaya çalış
                    img_elem = driver.find_element(By.CSS_SELECTOR, "article img, main img, figure img")
                    img_src = img_elem.get_attribute("src")
                    if img_src:
                        resim_html = f'<img src="{img_src}" style="width:100%; display:block;"/><br/><br/>'
                except:
                    pass

                # --- TAM METİN (YENİ YÖNTEM: GÖVDE TARAMA) ---
                full_text = ""
                try:
                    # 1. Haberin ana gövdesini bul (article veya main etiketi)
                    # Gdh muhtemelen 'article' veya belirli bir ID kullanıyor
                    govde = None
                    try:
                        govde = driver.find_element(By.TAG_NAME, "article")
                    except:
                        try:
                            govde = driver.find_element(By.TAG_NAME, "main")
                        except:
                            # Hicbiri yoksa body'den alacagiz (Son care)
                            govde = driver.find_element(By.TAG_NAME, "body")

                    # 2. Gövdenin içindeki TÜM GÖRÜNÜR METNİ al (.text özelliği)
                    # Bu özellik HTML taglerini siler, sadece kullanıcıya görünen yazıyı verir.
                    ham_metin = govde.text 
                    
                    # 3. Metni satır satır temizle
                    satirlar = ham_metin.split('\n')
                    temiz_satirlar = []
                    
                    for satir in satirlar:
                        satir = satir.strip()
                        # FILTRELEME:
                        # - Başlık ile aynı olan satırı atla
                        # - Çok kısa satırları (Menü, Tarih, Yazar, Reklam) atla
                        # - 'Abone ol', 'Takip et' gibi gereksizleri atla
                        if len(satir) > 50 and satir != baslik and "Haberler" not in satir and "Abone" not in satir:
                            temiz_satirlar.append(satir)
                    
                    # 4. Satırları HTML paragrafı (<br><br>) ile birleştir
                    full_text = "<br/><br/>".join(temiz_satirlar)

                except Exception as e:
                    print(f"Metin hatası: {e}")

                # Eğer hala metin boşsa
                if len(full_text) < 50:
                    full_text = "Haber metni çekilemedi, lütfen kaynağa gidin."

                # --- KAYDET ---
                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                fe.description(f"{resim_html}{full_text}")
                
                print(f"Eklendi: {baslik[:30]}...")
                eklenen += 1

            except Exception as e:
                print(f"Hata: {e}")
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} haber eklendi.")

    except Exception as e:
        print(f"GENEL HATA: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
