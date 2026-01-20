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
        # 1. Ana sayfadan haber linklerini topla
        driver.get("https://gdh.digital/savunma")
        time.sleep(12) 
        
        # Sayfayı aşağı kaydır (Haberleri tetiklemek için)
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(5)
        
        elementler = driver.find_elements(By.CSS_SELECTOR, "a[href*='/savunma/']")
        tum_linkler = []
        for el in elementler:
            l = el.get_attribute('href')
            if l and l != "https://gdh.digital/savunma" and "/savunma/" in l:
                if l not in tum_linkler:
                    tum_linkler.append(l)

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Detaylı Besleme')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma sanayii haberleri içerik botu')

        eklenen = 0
        # 2. Her linke girip içeriği doğrula
        for haber_url in tum_linkler[:10]: 
            try:
                driver.get(haber_url)
                time.sleep(4) 
                
                # Gercek basligi h1'den al
                gercek_baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                
                # Filtre: Çok kısa metinleri ve derece sembollerini ele
                if len(gercek_baslik) < 20 or "°" in gercek_baslik:
                    continue

                fe = fg.add_entry()
                fe.id(haber_url)
                fe.title(gercek_baslik)
                fe.link(href=haber_url)
                
                try:
                    img_url = driver.find_element(By.CSS_SELECTOR, "article img, img[class*='featured']").get_attribute('src')
                    fe.description(f'<img src="{img_url}"/><br/>{gercek_baslik}')
                except:
                    fe.description(gercek_baslik)
                
                eklenen += 1
            except:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"Bitti! {eklenen} haber XML'e işlendi.")

    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
