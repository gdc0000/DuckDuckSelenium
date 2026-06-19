import json
import logging
import time
import trafilatura

logger = logging.getLogger(__name__)


def extract_article(url, timeout=15):
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning(f"Failed to download {url}")
            return None

        result = trafilatura.extract(
            downloaded,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
            include_formatting=False,
        )

        if not result:
            return None

        data = json.loads(result)
        return {
            "scraped_title": data.get("title") or "",
            "author": data.get("author") or "",
            "text_content": data.get("text") or "",
            "date": data.get("date") or "",
            "language": data.get("language") or "",
        }

    except Exception as e:
        logger.error(f"Error extracting {url}: {e}")
        return None


def scrape_results(results, delay=1):
    articles = []
    total = len(results)
    for i, row in enumerate(results):
        url = row["url"]
        logger.info(f"Scraping article ({i+1}/{total}): {url}")
        article = extract_article(url)
        if article:
            articles.append((row["id"], article))
            logger.info(f"  -> Title: {article['scraped_title'][:80]}")
        time.sleep(delay)
    return articles
