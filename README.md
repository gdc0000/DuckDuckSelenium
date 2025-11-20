# Nuclear War Risk Perception: Italian News Media Scraper

A robust Selenium-based web scraper designed to collect news headlines from DuckDuckGo. This tool was originally developed for the study **"Apocalypse now or later? Nuclear war risk perceptions mirroring media coverage and emotional tone shifts in Italian news"** (Judgment and Decision Making, 2024).

## � Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd DuckDuckSelenium
    ```

2.  **Install dependencies**:
    Ensure you have Python 3.8+ and Google Chrome installed.
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Usage

1.  **Configure Input Files**:
    The scraper relies on three text files in the root directory:
    *   `Media.txt`: List of news websites to search (e.g., `repubblica.it`).
    *   `Keywords.txt`: Search terms (e.g., `Ucraina AND guerra`).
    *   `Date.txt`: Date range for the search (format: `YYYY-MM-DD` to `YYYY-MM-DD`).

2.  **Run the Scraper**:
    ```bash
    python main.py
    ```

    The script performs two main phases:
    1.  **Search Scraping**: Queries DuckDuckGo for each media outlet and keyword, saving results to `output/search_results.csv`.
    2.  **Article Scraping**: Visits the collected URLs to extract the full headline (H1), saving to `output/articles_scraped.csv`.

## � Output

*   `output/search_results.csv`: Contains raw search results including URL, date, and snippet.
*   `output/articles_scraped.csv`: Contains the final dataset with the extracted article titles.

**Note**: The tool supports incremental saving and can resume if interrupted.

## 📄 Citation

If you use this tool in your research, please cite:

> Lauriola, M., Di Cicco, G., & Savadori, L. (2024). **Apocalypse now or later? Nuclear war risk perceptions mirroring media coverage and emotional tone shifts in Italian news.** *Judgment and Decision Making*, 19(e7), 1–25. doi:10.1017/jdm.2024.2

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please ensure compliance with the Terms of Service of the websites you scrape.

## 📝 License

MIT License