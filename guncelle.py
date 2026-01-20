import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

def haberleri_cek():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://gdh.digital/savunma")
        time.sleep(15) # Sayfanın tam yüklenmesi için bekliyoruz
        
        fg = FeedGenerator()
        fg.title('Gdh Savunma')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Gdh Savunma Haberleri')

        # Sadece gerçek haber linklerini hedefle
        haberler = driver.find_elements(By.CSS_SELECTOR, "a[href*='/savunma/']")
        eklenen_sayisi = 0
        gorulen_linkler = set()

        for haber in haberler:
            link = haber.get_attribute('href')
            baslik = haber.text.strip()

            # Filtreleme: 
            # 1. Başlık en az 30 karakter olmalı (Hava durumu ve menüleri eler)
            # 2. İçinde derece sembolü olmamalı
            if not link or link in gorulen_linkler or len(baslik) < 30 or "°" in baslik:
                continue

            fe = fg.add_entry()
            fe.id(link)
            fe.title(baslik)
            fe.link(href=link)
            
            try:
                img_url = haber.find_element(By.TAG_NAME, "img").get_attribute('src')
                fe.description(f'<img src="{img_url}"/><br/>{baslik}')
            except:
                fe.description(baslik)

            gorulen_linkler.add(link)
            eklenen_sayisi += 1
            if eklenen_sayisi >= 15: break

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"Bitti! {eklenen_sayisi} haber eklendi.")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
