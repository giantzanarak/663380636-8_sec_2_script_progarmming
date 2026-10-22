import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from config_parser import ConfigParser
from scraper_agent import ScraperAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    config_file_path = os.path.join(os.path.dirname(__file__), 'configs', 'example_site_config.json')
    try:
        config_parser = ConfigParser(config_file_path)
        config = config_parser.load_config()
        # เปลี่ยนเป็น headless=False ชั่วคราวเพื่อให้เห็นหน้าจอ Chrome เปิดขึ้นมา
        scraper_agent = ScraperAgent(config, browser='chrome', headless=False)
        scraper_agent.run()
    except Exception as e:
        logging.critical(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
