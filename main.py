import pandas as pd
import logging
import config
import utils
from scraper import DuckDuckGoScraper
import os

def main():
    utils.setup_logging()
    utils.ensure_output_dir(config.OUTPUT_DIR)
    
    logging.info("Starting DuckDuckGo Scraper Refactored")
    
    # 1. Load Inputs
    media_list = utils.read_input_file(config.MEDIA_FILE)
    keywords_list = utils.read_input_file(config.KEYWORDS_FILE)
    dates_df = utils.read_date_file(config.DATE_FILE)
    
    if not media_list or not keywords_list or dates_df.empty:
        logging.error("Missing input data. Please check Media.txt, Keywords.txt, and Date.txt")
        return

    logging.info(f"Loaded {len(media_list)} media sites, {len(keywords_list)} keywords, and {len(dates_df)} date ranges.")

    scraper = DuckDuckGoScraper()
    all_search_results = []

    try:
        # 2. Search Scraping Phase
        logging.info("--- Starting Search Scraping Phase ---")
        
        # Initialize search results file with headers if not exists
        if not os.path.exists(config.SEARCH_RESULTS_FILE):
            pd.DataFrame(columns=["Media", "Url", "Date"]).to_csv(config.SEARCH_RESULTS_FILE, index=False)

        for media in media_list:
            for keyword in keywords_list:
                for index, row in dates_df.iterrows():
                    start_date = row.get('start_date') or row.get('date')
                    end_date = row.get('end_date')
                    
                    if not start_date or not end_date:
                        continue
                        
                    start_date = str(start_date).split()[0]
                    end_date = str(end_date).split()[0]

                    try:
                        url = scraper.generate_search_url(media, keyword, start_date, end_date)
                        scraper.search(url)
                        scraper.load_more_results()
                        
                        results = scraper.extract_search_results(media)
                        
                        if results:
                            # Append to CSV immediately
                            df_chunk = pd.DataFrame(results)
                            df_chunk.to_csv(config.SEARCH_RESULTS_FILE, mode='a', header=False, index=False)
                            logging.info(f"Saved {len(results)} results to {config.SEARCH_RESULTS_FILE}")
                            
                    except Exception as e:
                        logging.error(f"Error searching for {media} - {keyword}: {e}")
                        # Try to restart driver if it crashed
                        try:
                            scraper.driver.current_url
                        except:
                            logging.info("Driver seems dead, restarting...")
                            scraper.close()
                            scraper = DuckDuckGoScraper()

        logging.info("Search scraping complete.")
        
        # 3. Article Scraping Phase
        logging.info("--- Starting Article Scraping Phase ---")
        
        if not os.path.exists(config.SEARCH_RESULTS_FILE):
            logging.warning("No search results file found.")
            return

        # Read all search results
        df_search = pd.read_csv(config.SEARCH_RESULTS_FILE)
        
        # Initialize articles file if not exists
        if not os.path.exists(config.ARTICLES_FILE):
            pd.DataFrame(columns=["Media", "Url", "Date", "Title"]).to_csv(config.ARTICLES_FILE, index=False)
            scraped_urls = set()
        else:
            # Read already scraped URLs to avoid duplicates/resume
            try:
                df_existing = pd.read_csv(config.ARTICLES_FILE)
                scraped_urls = set(df_existing['Url'].tolist())
            except:
                scraped_urls = set()

        for index, row in df_search.iterrows():
            url = row['Url']
            
            if url in scraped_urls:
                continue

            logging.info(f"Scraping article ({index+1}/{len(df_search)}): {url}")
            
            try:
                title = scraper.get_article_title(url)
                
                # Create a single row dataframe
                row_data = row.to_dict()
                row_data['Title'] = title
                
                pd.DataFrame([row_data]).to_csv(config.ARTICLES_FILE, mode='a', header=False, index=False)
                scraped_urls.add(url)
                
            except Exception as e:
                logging.error(f"Error scraping article {url}: {e}")
                # Restart driver if needed
                try:
                    scraper.driver.current_url
                except:
                    logging.info("Driver seems dead, restarting...")
                    scraper.close()
                    scraper = DuckDuckGoScraper()
        
        logging.info(f"All done! Results saved to {config.ARTICLES_FILE}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
