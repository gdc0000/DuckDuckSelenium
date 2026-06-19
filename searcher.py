import logging
import time
from ddgs import DDGS
from ddgs.exceptions import DDGSException

logger = logging.getLogger(__name__)


def search_ddg(keywords, site=None, region="wt-wt", safesearch="moderate",
               timelimit=None, max_results=20, retries=3):
    query = keywords
    if site:
        query = f"site:https://{site}/ {keywords}"

    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = ddgs.text(
                    query=query,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=max_results,
                )
            return list(results)

        except DDGSException as e:
            wait = min(2 ** attempt, 10)
            logger.warning(f"DDGS error: {e} — retrying in {wait}s (attempt {attempt+1}/{retries})")
            time.sleep(wait)

    logger.error(f"Search failed after {retries} attempts")
    return []
