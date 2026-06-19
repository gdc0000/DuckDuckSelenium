# DuckDuckSearch — Motore di ricerca parametrizzato

Tool CLI per cercare su **DuckDuckGo** via API (nessun browser), salvare risultati in **SQLite** ed estrarre articoli con **trafilatura**.

## Installazione

```bash
pip install -r requirements.txt
```

## Uso rapido

```bash
# Ricerca one-shot
python main.py search "Ucraina AND guerra" --site repubblica.it --region it-it --max 30

# Ricerca senza salvare (solo stdout)
python main.py search "Python" --max 5 --no-save

# Eseguire profili da config.yaml
python main.py init                          # crea config.yaml di esempio
python main.py run --all                     # esegue tutti i profili
python main.py run ucraina-repubblica        # esegue un profilo specifico

# Gestione risultati
python main.py list                          # elenca ricerche fatte
python main.py list results --search-id 1    # risultati di una ricerca
python main.py list articles --search-id 1   # articoli estratti

# Scraping articoli (da risultati già salvati)
python main.py scrape --search-id 1          # estrai articoli per una ricerca

# Esportazione
python main.py export --search-id 1 --format csv
python main.py export --search-id 1 --format json
```

## Configurazione (`config.yaml`)

```yaml
searches:
  - name: ucraina-repubblica
    keywords: "Ucraina AND guerra"
    media_sites: [repubblica.it]
    region: it-it
    safesearch: moderate
    timelimit: null           # d, w, m, y o null
    max_results: 50
    extract_articles: true
```

## Architettura

```
config.yaml → main.py (CLI) → searcher.py (DDGS) → db.py (SQLite)
                                → scraper.py (trafilatura)
```

- `searcher.py`: wrapper per la libreria `ddgs` (nessun browser, retry automatico)
- `scraper.py`: estrazione contenuto articoli via `trafilatura` (titolo, autore, testo, data)
- `db.py`: layer SQLite con ricerca, risultati e articoli in relazione
- `cli.py`: interfaccia argparse con subcomandi

## Dipendenze

- `ddgs` — API DuckDuckGo (senza browser)
- `trafilatura` — estrazione testo articoli
- `pyyaml` — configurazione
- `rich` — formattazione terminale

## License

MIT
