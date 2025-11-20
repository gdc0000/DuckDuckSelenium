import time
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

import config

class DuckDuckGoScraper:
    def __init__(self):
        self.driver = self.setup_driver()

    def setup_driver(self):
        """Initializes the Chrome driver."""
        options = Options()
        if config.HEADLESS:
            options.add_argument('--headless')
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # Add user agent to avoid detection
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def generate_search_url(self, media, keyword, start_date, end_date):
        """Generates the DuckDuckGo search URL."""
        # Construct the query URL exactly as the user had it, but cleaner
        # Note: The user's original code had hardcoded '2023-12-07' as end date in the loop, 
        # but read 'Date' from file. I will use the passed start/end dates.
        
        # URL encoding should ideally be done with urllib, but keeping it simple to match legacy behavior if it works.
        # However, manual string concatenation is prone to errors.
        # Let's trust the user's structure: site:https://<media>/ <keyword>
        
        base_url = "https://duckduckgo.com/"
        # q = site:https://media/ keyword
        # We need to be careful with encoding.
        
        # Replicating the exact string construction from the legacy code to ensure compatibility
        # query = 'https://duckduckgo.com/?q=site%3Ahttps%3A%2F%2F' + m + "%2F+" + kw + "&va=b&t=hc&df=" + str(d) + ".." + str(end) + "&ia=web"
        
        url = (f"https://duckduckgo.com/?q=site%3Ahttps%3A%2F%2F{media}%2F+{keyword}"
               f"&va=b&t=hc&df={start_date}..{end_date}&ia=web")
        return url

    def search(self, url):
        """Navigates to the search URL."""
        logging.info(f"Navigating to: {url}")
        self.driver.get(url)
        time.sleep(config.PAGE_LOAD_DELAY)

    def load_more_results(self):
        """Clicks the 'More Results' button until it's no longer available."""
        while True:
            try:
                more_btn = self.driver.find_element(By.XPATH, '//*[@id="more-results"]')
                more_btn.click()
                logging.info("Clicked 'More Results'")
                time.sleep(config.CLICK_DELAY)
            except (NoSuchElementException, ElementNotInteractableException):
                logging.info("No more results to load or button not found.")
                break
            except Exception as e:
                logging.warning(f"Error clicking 'More Results': {e}")
                break

    def extract_search_results(self, media):
        """Extracts URLs and dates from the search results page."""
        results = []
        
        # Try to find links
        # Using a more robust XPath than the original if possible, but falling back to the original structure
        # Original: /html/body/div[2]/div[5]/div[4]/div/div/div/div/section[1]/ol/li/article/div[2]/h2/a
        # Better: //article//h2/a
        
        try:
            links = self.driver.find_elements(By.XPATH, '//article//h2/a')
            
            # Updated XPath based on browser inspection
            dates = self.driver.find_elements(By.XPATH, '//article//div/span/span[1]')
            
            if not dates:
                 # Fallback 1: Try looking for result__timestamp class
                 dates = self.driver.find_elements(By.CSS_SELECTOR, '.result__timestamp')
            
            if not dates:
                 # Fallback 2: Look for any span with 202x (heuristic)
                 dates = self.driver.find_elements(By.XPATH, '//article//span[contains(text(), "202")]')
            
            logging.info(f"Found {len(links)} links and {len(dates)} dates.")
            
            # Iterate over links, as they are the primary data
            for i in range(len(links)):
                url = links[i].get_attribute('href')
                
                date_text = "N/A"
                
                # Try to get corresponding date from the list of potential date elements
                if i < len(dates):
                    raw_text = dates[i].text.strip()
                    # Validation: Dates are usually short. Snippets are long.
                    # A valid date should be short (< 50 chars) and contain a year (20\d\d)
                    if len(raw_text) < 50 and re.search(r'20\d\d', raw_text):
                        date_text = raw_text
                
                results.append({
                    "Media": media,
                    "Url": url,
                    "Date": date_text
                })
                
        except Exception as e:
            logging.error(f"Error extracting search results: {e}")
            
        return results

    def get_article_title(self, url):
        """Visits an article URL and extracts the H1 title."""
        try:
            self.driver.get(url)
            time.sleep(config.PAGE_LOAD_DELAY)
            
            h1s = self.driver.find_elements(By.TAG_NAME, 'h1')
            if not h1s:
                return "No H1 Found"
            
            # Return the longest H1 text as the title (heuristic from original code)
            texts = [h.text for h in h1s if h.text]
            if not texts:
                return "Empty H1"
                
            return max(texts, key=len)
            
        except Exception as e:
            logging.error(f"Error extracting title from {url}: {e}")
            return "Error"

    def close(self):
        self.driver.quit()
