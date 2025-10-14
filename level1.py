from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://www.bcracingeu.com/bc-6kg-taper-spring-95-62-180-006v-0033777.html"

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get(url)
    elements = driver.find_elements(By.CSS_SELECTOR, "span[data-price-type='finalPrice'] .price")
    price = None
    if elements and elements[0].text.strip():
        price = elements[0].text.strip()

    print("Price:", price)

finally:
    driver.quit()