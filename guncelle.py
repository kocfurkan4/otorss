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
        # 1. Ana sayfadan haber linklerini ayıkla
        driver.get("https://gdh.digital/savunma")
        time.sleep(12) 
        
        # Sayfayı haberlerin yüklenmesi için aşağı kaydır
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(5)
        
        elementler = driver.find_elements(By.CSS_SELECTOR, "a[href*='/savunma/']")
        tum_linkler = []
        for el in elementler:
            l = el.get_attribute('href')
            # Kategori linkini ve tekrarları ele
            if l and l != "https://gdh.digital/savunma" and "/savunma/" in l:
                if l not in tum_linkler:
                    tum_linkler.append(l)

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Tam Besleme')
        fg.link(href='https://gdh.digital/savunma', rel='alternate')
        fg.description('Savunma sanayii haberleri botu')

        eklenen = 0
        # 2. Tespit edilen haberlerin içine girip gerçek başlığı al
        for haber_url in tum_linkler[:10]: # Performans için son 10 haberi tara
            try:
                driver.get(haber_url)
                time.sleep(4) 
                
                # Gerçek başlık genellikle h1 etiketindedir
                gercek_baslik = driver.find_element(By.TAG_NAME, "h1").text.strip()
                
                # "5°" gibi verileri ve çok kısa başlıkları filtrele
                if len(gercek_baslik) < 20 or "°" in gercek_baslik:
                    continue

                fe = fg.add_entry()
                fe.id(haber_url)
                fe.title(gercek_baslik)
                fe.link(href=haber_url)
                
                # Öne çıkan görseli bulmaya çalış
                try:
                    img_url = driver.find_element(By.CSS_SELECTOR, "article img, .post-content img, img[class*='featured']").get_attribute('src')
                    fe.description(f'<img src="{img_url}"/><br/>{gercek_baslik}')
                except:
                    fe.description(gercek_baslik)
                
                eklenen += 1
            except:
                continue

        # XML Dosyasını Oluştur
        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"Bitti! {eklenen} haber başarıyla XML'e eklendi.")

    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek()
