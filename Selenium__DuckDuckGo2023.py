# main.py
import streamlit as st
import pandas as pd
import time
import numpy as np
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode.
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize the WebDriver using webdriver-manager for automatic driver management.
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_data(driver, media, keywords, dates, progress_callback):
    data = []
    total_steps = len(keywords) * len(media) * len(dates)
    current_step = 0

    for kw in keywords:
        for m in media:
            for d in dates:
                query = f'https://duckduckgo.com/?q=site:https://{m}/+{kw}&va=b&t=hc&df={d}..{d}&ia=web'
                driver.get(query)
                time.sleep(2)  # Allow the page to load. Adjust as necessary or implement explicit waits.

                try:
                    links = driver.find_elements(By.XPATH, '//ol/li//h2/a')
                    urls_text = [link.get_attribute('href') for link in links if link.get_attribute('href')]
                except Exception as e:
                    urls_text = []
                
                for url in urls_text:
                    data.append({"Url": url, "Media": m, "Date": d})
                
                current_step += 1
                progress_callback(current_step / total_steps)

    dfTot = pd.DataFrame(data)
    return dfTot

def extract_titles(driver, df, progress_callback):
    headers = []
    total_urls = len(df)
    for i, url in enumerate(df['Url'], 1):
        try:
            driver.get(url)
            time.sleep(1)  # Allow the page to load. Adjust as necessary or implement explicit waits.
            h1_elements = driver.find_elements(By.TAG_NAME, 'h1')
            h1_text = [h.text.strip() for h in h1_elements if h.text.strip()]
            title = max(h1_text, key=len) if h1_text else "No H1 Found"
            headers.append(title)
        except Exception as e:
            headers.append("Error")
        progress_callback(i / total_urls)
    df['Title'] = headers
    return df

def main():
    st.set_page_config(page_title="Selenium Scraper with Streamlit", layout="wide")
    st.title("Selenium Scraper with Streamlit")
    st.write("""
        Upload your input files (Media, Keywords, Date) and run the scraper to collect URLs and their titles from DuckDuckGo.
    """)

    # File Uploads
    st.sidebar.header("Upload Input Files")
    media_file = st.sidebar.file_uploader("Upload Media.csv", type=["csv"])
    keywords_file = st.sidebar.file_uploader("Upload Keywords.csv", type=["csv"])
    dates_file = st.sidebar.file_uploader("Upload Date.csv", type=["csv"])

    if st.sidebar.button("Run Scraper"):
        if media_file and keywords_file and dates_file:
            try:
                # Read uploaded files
                media_df = pd.read_csv(media_file)
                keywords_df = pd.read_csv(keywords_file)
                dates_df = pd.read_csv(dates_file)

                # Validate columns
                if 'Media' not in media_df.columns:
                    st.error("Media.csv must contain a 'Media' column.")
                    return
                if 'KW' not in keywords_df.columns:
                    st.error("Keywords.csv must contain a 'KW' column.")
                    return
                if 'Date' not in dates_df.columns:
                    st.error("Date.csv must contain a 'Date' column.")
                    return

                media = media_df["Media"].dropna().tolist()
                keywords = keywords_df["KW"].dropna().tolist()
                dates = dates_df["Date"].dropna().tolist()

                if not media or not keywords or not dates:
                    st.error("One of the input files is empty or missing required columns.")
                    return

                # Initialize WebDriver
                with st.spinner('Initializing WebDriver...'):
                    driver = initialize_driver()

                # Scrape Data
                st.header("Scraping Data...")
                progress_bar = st.progress(0)
                dfTot = scrape_data(driver, media, keywords, dates, lambda x: progress_bar.progress(x))

                # Extract Titles
                st.header("Extracting Titles from URLs...")
                progress_bar_titles = st.progress(0)
                dfTot = extract_titles(driver, dfTot, lambda x: progress_bar_titles.progress(x))

                # Close the driver
                driver.quit()

                st.success("Scraping Completed Successfully!")

                # Display Data
                st.subheader("Collected Data")
                st.dataframe(dfTot)

                # Download Option
                csv = dfTot.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name='scraped_data.csv',
                    mime='text/csv',
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please upload all three input files (Media.csv, Keywords.csv, Date.csv).")

if __name__ == "__main__":
    main()
