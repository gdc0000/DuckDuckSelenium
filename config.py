import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = BASE_DIR  # Input files are in the same directory for now
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Input Files
MEDIA_FILE = os.path.join(INPUT_DIR, "Media.txt")
KEYWORDS_FILE = os.path.join(INPUT_DIR, "Keywords.txt")
DATE_FILE = os.path.join(INPUT_DIR, "Date.txt")

# Output Files
SEARCH_RESULTS_FILE = os.path.join(OUTPUT_DIR, "search_results.csv")
ARTICLES_FILE = os.path.join(OUTPUT_DIR, "articles_scraped.csv")

# Scraper Settings
HEADLESS = False  # Set to True for headless mode
PAGE_LOAD_DELAY = 2
CLICK_DELAY = 1
MAX_RETRIES = 3
