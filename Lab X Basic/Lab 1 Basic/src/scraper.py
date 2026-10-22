import requests
import json
import os
from bs4 import BeautifulSoup

class SimpleWebScraper:
    def __init__(self, target_url):
        self.target_url = target_url

    def _get_html_content(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.target_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def scrape_main_titles(self):
        html_content = self._get_html_content()
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')

        # Wikipedia Main Page Welcome Banner / Title
        main_header = soup.find('span', id='welcome')
        book_title = main_header.get_text(strip=True) if main_header else "Wikipedia Main Page"

        # Extract main section headings (h2 elements on Wikipedia)
        chapter_titles = []
        headings = soup.find_all('h2')
        for h2 in headings:
            text = h2.get_text(strip=True)
            if text:
                chapter_titles.append(text)

        return {
            "book_title": book_title,
            "chapter_titles": chapter_titles
        }

    def save_to_json(self, data, filename="scraped_output.json"):
        """Saves the scraped data into the 'data' directory."""
        if not data:
            print("No data to save.")
            return

        # กำหนดตำแหน่งโฟลเดอร์ data/
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = os.path.join(data_dir, filename)

        # บันทึกข้อมูลลงไฟล์ JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"\n[Success] Saved scraped data to: {file_path}")
