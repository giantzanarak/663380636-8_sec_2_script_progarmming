import time
import json
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

def save_data_to_json(data, filename, directory='data'):
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to {filepath}")
        return True
    except IOError as e:
        print(f"Error saving data to JSON file: {e}")
        return False

def wait_for_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        WebDriverWait(driver, timeout).until(
            EC.visibility_of(element)
        )
        return element
    except (TimeoutException, NoSuchElementException):
        return None

def robust_click(driver, by, value, max_attempts=3, delay_between_attempts=2):
    for attempt in range(max_attempts):
        try:
            element = wait_for_element(driver, by, value)
            if element:
                element.click()
                return True
        except WebDriverException as e:
            if attempt < max_attempts - 1:
                time.sleep(delay_between_attempts)
    return False

def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
