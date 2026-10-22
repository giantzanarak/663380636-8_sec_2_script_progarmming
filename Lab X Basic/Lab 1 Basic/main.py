import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from scraper import SimpleWebScraper

def main():
    target_url = "https://en.wikipedia.org/wiki/Main_Page"
    scraper = SimpleWebScraper(target_url)
    
    scraped_data = scraper.scrape_main_titles()
    if scraped_data:
        print("\n--- Scraped Data ---")
        print(f"Book Title: {scraped_data['book_title']}")
        print("\nChapter Titles:")
        if scraped_data['chapter_titles']:
            for i, title in enumerate(scraped_data['chapter_titles']):
                print(f"{i+1}. {title}")
        else:
            print("No chapter titles found.")
        print("--------------------")

        # สั่งบันทึกข้อมูลลงโฟลเดอร์ data/
        scraper.save_to_json(scraped_data)
    else:
        print("Failed to scrape data.")

if __name__ == "__main__":
    main()
