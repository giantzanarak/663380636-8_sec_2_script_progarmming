import time
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from driver_manager import DriverManager
from data_models import Product
from utils import wait_for_element, robust_click, save_data_to_json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ScraperAgent:
    def __init__(self, config, browser='chrome', headless=True):
        self.config = config
        self.driver_manager = DriverManager(browser_name=browser, headless=headless)
        self.driver = None
        self.scraped_products = []
        self.max_pages = config.get("max_pages", 5)

    def _get_element_text(self, parent_element, selector, selector_type=By.CSS_SELECTOR):
        if not selector:
            return None
        try:
            element = parent_element.find_element(selector_type, selector)
            return element.text.strip()
        except (NoSuchElementException, StaleElementReferenceException, Exception):
            return None

    def _get_element_attribute(self, parent_element, selector, attribute, selector_type=By.CSS_SELECTOR):
        if not selector:
            return None
        try:
            element = parent_element.find_element(selector_type, selector)
            return element.get_attribute(attribute)
        except (NoSuchElementException, StaleElementReferenceException, Exception):
            return None

    def _parse_product_data(self, item_element):
        selectors = self.config["item_data_selectors"]
        
        # สำหรับ site books.toscrape ดึงชื่อจาก attribute 'title' ถ้ามี
        name_selector = selectors.get("name")
        name = self._get_element_attribute(item_element, name_selector, "title")
        if not name:
            name = self._get_element_text(item_element, name_selector)

        price = self._get_element_text(item_element, selectors.get("price"))
        description = self._get_element_text(item_element, selectors.get("description"))
        url = self._get_element_attribute(item_element, selectors.get("url"), "href")
        image_url = self._get_element_attribute(item_element, selectors.get("image_url"), "src")

        if name and price:
            return Product(name=name, price=price, description=description, url=url, image_url=image_url)
        return None

    def scrape_page(self):
        logging.info(f"Scraping page: {self.driver.current_url}")
        try:
            item_elements = self.driver.find_elements(By.CSS_SELECTOR, self.config["item_container_selector"])
            if not item_elements:
                item_elements = self.driver.find_elements(By.XPATH, self.config["item_container_selector"])
            
            logging.info(f"Found {len(item_elements)} potential product items on this page.")
            parsed_count = 0
            for item_element in item_elements:
                product = self._parse_product_data(item_element)
                if product:
                    self.scraped_products.append(product.to_dict())
                    parsed_count += 1
            logging.info(f"Successfully scraped {parsed_count} items from current page.")
        except Exception as e:
            logging.error(f"Error scraping page items: {e}")

    def run(self):
        logging.info("Initializing WebDriver...")
        self.driver = self.driver_manager.get_driver()
        if not self.driver:
            logging.error("Failed to start WebDriver.")
            return
        try:
            self.driver.get(self.config["start_url"])
            current_page = 1
            while current_page <= self.max_pages:
                logging.info(f"Processing page {current_page} at {self.driver.current_url}")
                self.scrape_page()
                time.sleep(self.config.get("delay_between_pages", 2))

                pagination_selector = self.config["pagination_selector"]
                if pagination_selector:
                    try:
                        next_button = wait_for_element(self.driver, By.CSS_SELECTOR, pagination_selector, timeout=5)
                        if next_button and next_button.is_displayed() and next_button.is_enabled():
                            robust_click(self.driver, By.CSS_SELECTOR, pagination_selector)
                            current_page += 1
                        else:
                            break
                    except (NoSuchElementException, TimeoutException):
                        break
                else:
                    break
        finally:
            self.driver_manager.quit_driver()
            logging.info(f"Scraping finished. Total items: {len(self.scraped_products)}")
            save_data_to_json(self.scraped_products, "scraped_products.json")
