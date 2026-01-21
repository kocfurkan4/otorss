import time
from datetime import datetime
import pytz 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

# --- YAPAY ZEKA KÜTÜPHANELERİ ---
import newspaper
from newspaper import Article
import nltk

# NLTK Hatasını önlemek için gerekli veriyi indiriyoruz
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

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
        print("Site taranıyor (AI Modu)...")
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

        print(f"Toplam {len(haber_linkleri)} link bulundu. AI analizi başlıyor...")

        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma Haberleri')
        fg.language('tr')

        eklenen = 0
        
        # 2. YAPAY ZEKA İLE İÇERİK OKUMA
        for link in haber_linkleri[:15]: 
            try:
                # Selenium ile sayfayı aç (Cloudflare'i geçmek için)
                driver.get(link)
                time.sleep(2)
                
                # Sayfanın HTML kaynağını alıp AI'ya veriyoruz
                html_kaynagi = driver.page_source
                
                # --- AI Analizi Başlıyor ---
                makale = Article(link)
                makale.set_html(html_kaynagi) # HTML'i elle veriyoruz
                makale.parse() # İçeriği ayrıştır
                # makale.nlp() # Özet çıkarmak istersen bu satırı açabilirsin (biraz yavaşlatır)

                baslik = makale.title
                resim_url = makale.top_image
                ham_metin = makale.text # AI'nın temizlediği metin

                # --- SON TEMİZLİK ---
                # AI bazen en alttaki "takip edin" yazılarını içerik sanabilir.
                # Onları manuel olarak temizliyoruz.
                satirlar = ham_metin.split('\n')
                temiz_satirlar = []
                
                bitis_kelimeleri = [
                    "takip edebilirsiniz", "gdh digital", "sosyal medya", "------",
                    "uygulamasını indir", "ilgili haberler", "etiketler", "abone ol"
                ]
                
                for satir in satirlar:
                    satir = satir.strip()
                    if not satir: continue
                    
                    # Kara Liste Kontrolü
                    kucuk_satir = satir.lower()
                    if any(k in kucuk_satir for k in bitis_kelimeleri):
                        break # Haberi burada kes
                    
                    if "Kültür sanat" in satir: continue
                    if satir == baslik: continue

                    # Metni Ekle
                    if len(satir) > 10:
                        temiz_satirlar.append(satir)

                full_text = "<br/><br/>".join(temiz_satirlar)
                
                # Tarih (AI bulamazsa şimdiki zaman)
                try:
                    tarih = makale.publish_date
                    if tarih:
                        if tarih.tzinfo is None:
                            tarih = pytz.timezone('Europe/Istanbul').localize(tarih)
                    else:
                        tarih = datetime.now(pytz.timezone('Europe/Istanbul'))
                except:
                    tarih = datetime.now(pytz.timezone('Europe/Istanbul'))

                # Resim HTML
                resim_html = ""
                if resim_url:
                    resim_html = f'<img src="{resim_url}" style="width:100%; display:block;"/><br/><br/>'

                if len(full_text) < 20: full_text = "İçerik okunamadı."

                # --- RSS KAYDI ---
                fe = fg.add_entry()
                fe.id(link)
                fe.link(href=link)
                fe.title(baslik)
                fe.published(tarih)
                fe.description(f"{resim_html}{full_text}")
                
                print(f"Eklendi (AI): {baslik}")
                eklenen += 1

            except Exception as e:
                print(f"Hata ({link}): {e}")
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"İŞLEM TAMAM: {eklenen} haber analiz edildi.")

    except Exception as e:
        print(f"KRİTİK HATA: {e}")
        exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
