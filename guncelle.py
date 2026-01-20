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
    chrome_options.add_argument("--headless") # Tarayıcıyı gizli modda açar
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        url = "https://gdh.digital/savunma"
        driver.get(url)
        
        # Sayfanın yüklenmesini bekle (Haber kartlarını temsil eden ana div'i bekliyoruz)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/savunma/']")))
        time.sleep(2) # Resimlerin render edilmesi için kısa ek süre

        fg = FeedGenerator()
        fg.title('Gdh Savunma | Detaylı Besleme')
        fg.link(href=url, rel='alternate')
        fg.description('Savunma sanayii son dakika gelişmeleri')

        # Gdh'ın haber kutucuklarını hedef alıyoruz
        # Not: Site yapısı değiştikçe buradaki selector'lar güncellenmelidir.
        haber_kartlari = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or contains(@class, 'item')]") or \
                         driver.find_elements(By.CSS_SELECTOR, "div.grid a[href*='/savunma/']")

        for kart in haber_kartlari[:10]: # Son 10 güncel haber
            try:
                # Link ve Başlık çekme
                link = kart.get_attribute('href')
                # Eğer kartın kendisi link değilse içine bak
                if not link:
                    link = kart.find_element(By.TAG_NAME, "a").get_attribute('href')
                
                baslik = kart.text.split('\n')[0] # Genelde ilk satır başlıktır
                
                # Resim Çekme (img etiketinden src alıyoruz)
                try:
                    resim_url = kart.find_element(By.TAG_NAME, "img").get_attribute('src')
                except:
                    resim_url = ""

                fe = fg.add_entry()
                fe.id(link)
                fe.title(baslik)
                fe.link(href=link)
                
                # RSS İçeriği (Resim + Başlık)
                content = f'<img src="{resim_url}" style="width:100%;"/><br/>{baslik}'
                fe.description(content)
                
            except:
                continue

        fg.rss_file('gdh_savunma_detayli.xml')
        print("RSS Başarıyla Oluşturuldu: gdh_savunma_detayli.xml")

    finally:
        driver.quit()

if __name__ == "__main__":
    haberleri_cek_full()