from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from feedgen.feed import FeedGenerator
import time

def haberleri_cek_full():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Bazı siteler botları engellemek için user-agent kontrol eder
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        url = "https://gdh.digital/savunma"
        driver.get(url)
        
        # Sayfanın en azından bir haber linki içermesini bekleyelim
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/savunma/']")))
        
        # Dinamik içeriklerin tam yüklenmesi için biraz aşağı kaydıralım ve bekleyelim
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(5)

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Güncel Besleme')
        fg.link(href=url, rel='alternate')
        fg.description('Savunma sanayii son dakika haberleri otomatik besleme')
        fg.language('tr')

        # Haber kartlarını bulmak için daha geniş bir tarama yapıyoruz
        # Sitedeki her bir haber genellikle bir 'article' veya belirli bir 'div' içindedir
        haber_linkleri = driver.find_elements(By.CSS_SELECTOR, "a[href*='/savunma/']")
        
        eklenen_linkler = set() # Tekrar eden haberleri engellemek için

        for link_element in haber_linkleri:
            try:
                link = link_element.get_attribute('href')
                
                # Eğer link ana sayfa veya kategori sayfasıysa atla
                if link == "https://gdh.digital/savunma" or link in eklenen_linkler:
                    continue
                
                # Başlığı bulmak için elementin içindeki metne veya 'title' özniteliğine bak
                baslik = link_element.text.strip()
                if not baslik or len(baslik) < 5:
                    # Eğer metin boşsa içindeki h1, h2, h3 veya span'a bak
                    try:
                        baslik = link_element.find_element(By.XPATH, ".//h2|.//h3|.//span").text.strip()
                    except:
                        continue
                
                if baslik and link:
                    fe = fg.add_entry()
                    fe.id(link)
                    fe.title(baslik)
                    fe.link(href=link)
                    
                    # Görsel bulma denemesi
                    try:
                        img = link_element.find_element(By.TAG_NAME, "img").get_attribute('src')
                        fe.description(f'<img src="{img}"/><br/>{baslik}')
                    except:
                        fe.description(baslik)
                        
                    eklenen_linkler.add(link)
                    if len(eklenen_linkler) >= 15: break # İlk 15 güncel haberi al

            except:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print(f"Başarıyla {len(eklenen_linkler)} haber çekildi.")

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek_full()
