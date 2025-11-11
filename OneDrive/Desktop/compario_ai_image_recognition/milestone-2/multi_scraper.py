from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def init_driver():
    """Initialize headless Chrome."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(5)
    return driver

# -------------------- Amazon --------------------
def scrape_amazon(driver, query):
    result = {"Name": "No products found", "Price": "No products found", "Link": "#"}
    try:
        driver.get("https://www.amazon.in")
        driver.delete_all_cookies()
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0"})
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_box.send_keys(query + Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']")))
        product = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")[0]
        result["Name"] = product.find_element(By.TAG_NAME, "h2").text
        try:
            result["Price"] = product.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
        except:
            result["Price"] = "No price"
        result["Link"] = product.find_element(By.TAG_NAME, "a").get_attribute("href")
    except Exception as e:
        print(f"⚠️ Amazon error: {e}")
    return result

# -------------------- Flipkart --------------------
def scrape_flipkart(driver, query):
    result = {"Name": "No products found", "Price": "No products found", "Link": "#"}
    try:
        driver.get("https://www.flipkart.com")
        driver.delete_all_cookies()
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0"})
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='✕']"))).click()
        except:
            pass
        search_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "q")))
        search_box.send_keys(query + Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a._1fQZEK, a.s1Q9rs, a.IRpwTa")))
        product = driver.find_elements(By.CSS_SELECTOR, "a._1fQZEK, a.s1Q9rs, a.IRpwTa")[0]
        result["Name"] = product.text.strip()
        result["Link"] = product.get_attribute("href")
        try:
            result["Price"] = driver.find_element(By.CSS_SELECTOR, "div._30jeq3, div._25b18c span").text.strip()
        except:
            result["Price"] = "No price"
    except Exception as e:
        print(f"⚠️ Flipkart error: {e}")
    return result

# -------------------- Snapdeal --------------------
def scrape_snapdeal(driver, query):
    result = {"Name": "No products found", "Price": "No products found", "Link": "#"}
    try:
        driver.get("https://www.snapdeal.com")
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "inputValEnter")))
        search_box.send_keys(query + Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-tuple-listing")))
        product = driver.find_elements(By.CSS_SELECTOR, "div.product-tuple-listing")[0]
        result["Name"] = product.find_element(By.CSS_SELECTOR, "p.product-title").text
        result["Price"] = product.find_element(By.CSS_SELECTOR, "span.lfloat.product-price").text
        result["Link"] = product.find_element(By.TAG_NAME, "a").get_attribute("href")
    except Exception as e:
        print(f"⚠️ Snapdeal error: {e}")
    return result
