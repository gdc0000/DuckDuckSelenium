# DuckDuckSearch — Parameterized search engine

CLI tool to search **DuckDuckGo** via API (no browser), save results in **SQLite** and extract articles with **trafilatura**.

## Installation

```bash
pip install -r requirements.txt
```

## Quick start

```bash
# One-shot search
python main.py search "Ucraina AND guerra" --site repubblica.it --region it-it --max 30

# Dry run (stdout only, no DB)
python main.py search "Python" --max 5 --no-save

# Run profiles from config.yaml
python main.py init                          # creates example config.yaml
python main.py run --all                     # runs all profiles
python main.py run ucraina-repubblica        # runs a specific profile

# Manage results
python main.py list                          # lists saved searches
python main.py list results --search-id 1    # results of a search
python main.py list articles --search-id 1   # extracted articles

# Article extraction (from saved results)
python main.py scrape --search-id 1          # extract articles for a search

# Export
python main.py export --search-id 1 --format csv
python main.py export --search-id 1 --format json
```

## Configuration (`config.yaml`)

```yaml
searches:
  - name: ucraina-repubblica
    keywords: "Ucraina AND guerra"
    media_sites: [repubblica.it]
    region: it-it
    safesearch: moderate
    timelimit: null           # d, w, m, y or null
    max_results: 50
    extract_articles: true
```

## Architecture

```
config.yaml → main.py (CLI) → searcher.py (DDGS) → db.py (SQLite)
                                → scraper.py (trafilatura)
```

- `searcher.py`: wrapper around the `ddgs` library (no browser, automatic retry)
- `scraper.py`: article content extraction via `trafilatura` (title, author, text, date)
- `db.py`: SQLite layer linking searches, results, and articles
- `cli.py`: argparse interface with subcommands

## Dependencies

- `ddgs` — DuckDuckGo API (no browser)
- `trafilatura` — article text extraction
- `pyyaml` — configuration
- `rich` — terminal formatting

## License

MIT
