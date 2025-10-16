from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List
import os, json, sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from validation import dump_debug, validate_dataclass


@dataclass
class ProductData:
    url: str
    name: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    sku: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    extras: Dict[str, str] = field(default_factory=dict)


class ProductPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def load(self, url: str):
        self.driver.get(url)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

    def get_name(self) -> Optional[str]:
        selectors = [
            'h1.page-title span[itemprop="name"]',
            'h1.page-title span',
            'h1.product-title'
        ]
        for sel in selectors:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els and els[0].text.strip():
                return els[0].text.strip()
        return None

    def get_price(self) -> Optional[str]:
        # visible price first
        text_sels = [
            'span.price-wrapper .price',
            'span[data-price-type="finalPrice"] .price',
            'span.price'
        ]
        for sel in text_sels:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els and els[0].text.strip():
                return els[0].text.strip()
        # OpenGraph/Meta fallback
        meta_sel = 'meta[property="product:price:amount"]'
        el = self.driver.find_elements(By.CSS_SELECTOR, meta_sel)
        return el[0].get_attribute("content").strip() if el and el[0].get_attribute("content") else None

    def get_currency(self) -> Optional[str]:
        el = self.driver.find_elements(By.CSS_SELECTOR, 'meta[property="product:price:currency"]')
        return el[0].get_attribute("content").strip() if el and el[0].get_attribute("content") else None

    def get_sku(self) -> Optional[str]:
        selectors = [
            'div.product.attribute.sku .value',
            'span[itemprop="sku"]',
            'div.sku .value'
        ]
        for sel in selectors:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                txt = (els[0].text or els[0].get_attribute("content") or "").strip()
                if txt:
                    return txt
        return None

    def get_availability(self) -> Optional[str]:
        # human-readable first
        for sel in [
            'div.stock-display',
            'div.stock-display strong',
            'div.stock.available span',
            'div.stock.unavailable span'
        ]:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els and els[0].text.strip():
                return els[0].text.strip()
        # schema.org link
        el = self.driver.find_elements(By.CSS_SELECTOR, 'link[itemprop="availability"]')
        return el[0].get_attribute("href") or el[0].get_attribute("content") if el else None

    def get_description(self) -> Optional[str]:
        for sel in [
            '.product.attribute.overview .value',
            '#description',
            '.product-info-main .value.description'
        ]:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els and els[0].text.strip():
                return els[0].text.strip()
        return None

    def get_images(self, max_imgs: int = 6) -> List[str]:
        imgs: List[str] = []
        selectors = [
            '.fotorama__stage .fotorama__img',
            '.product.media img'
        ]
        for sel in selectors:
            for el in self.driver.find_elements(By.CSS_SELECTOR, sel):
                src = el.get_attribute("src") or el.get_attribute("data-src")
                if src and src not in imgs:
                    imgs.append(src)
            if imgs:
                break
        return imgs[:max_imgs]

    def get_extras(self) -> Dict[str, str]:
        extras = {}
        rows = self.driver.find_elements(By.CSS_SELECTOR, 'table.data.table.additional-attributes tr')
        for row in rows:
            try:
                k = row.find_element(By.CSS_SELECTOR, 'th').text.strip()
                v = row.find_element(By.CSS_SELECTOR, 'td').text.strip()
                if k and v:
                    extras[k] = v
            except Exception:
                continue
        return extras

    def scrape(self, url: str) -> ProductData:
        return ProductData(
            url=url,
            name=self.get_name(),
            price=self.get_price(),
            currency=self.get_currency(),
            sku=self.get_sku(),
            availability=self.get_availability(),
            description=self.get_description(),
            images=self.get_images(),
            extras=self.get_extras()
        )


def make_driver(headless: bool = True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,1600")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


if __name__ == "__main__":
    url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://www.bcracingeu.com/bc-6kg-taper-spring-95-62-180-006v-0033777.html"
    )
    driver = make_driver(headless=True)
    try:
        page = ProductPage(driver)
        page.load(url)
        data = page.scrape(url)
        print(json.dumps(asdict(data), indent=2, ensure_ascii=False))

        # validate data
        validate_dataclass(data, required=["price", "sku", "availability"], file_path=__file__)

    except Exception as e:
        dump_debug(os.path.basename(__file__), driver, e)
        raise

    finally:
        driver.quit()
