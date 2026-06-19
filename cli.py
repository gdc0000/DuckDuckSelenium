import argparse
import csv
import json
import logging
import os
import sys

import yaml
from rich.console import Console
from rich.table import Table
from rich import box

import db
import searcher
import scraper

logger = logging.getLogger(__name__)
console = Console()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="duckducksearch",
        description="DuckDuckSearch — Motore di ricerca DuckDuckGo con SQLite",
    )
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Ricerca one-shot")
    p_search.add_argument("keywords", help="Parole chiave")
    p_search.add_argument("--site", help="Filtra per sito (es. repubblica.it)")
    p_search.add_argument("--region", default="wt-wt", help="Regione (es. it-it, us-en)")
    p_search.add_argument("--safesearch", choices=["on", "moderate", "off"], default="moderate")
    p_search.add_argument("--timelimit", choices=["d", "w", "m", "y"], default=None)
    p_search.add_argument("--max", type=int, default=20, help="Max risultati")
    p_search.add_argument("--name", help="Nome per la ricerca")
    p_search.add_argument("--extract", action="store_true", help="Estrai articoli dopo la ricerca")
    p_search.add_argument("--no-save", action="store_true", help="Solo stdout, non salvare")

    p_run = sub.add_parser("run", help="Esegue profilo/i da config.yaml")
    p_run.add_argument("profile", nargs="?", help="Nome profilo")
    p_run.add_argument("--all", action="store_true", help="Esegue tutti i profili")

    p_scrape = sub.add_parser("scrape", help="Estrae articoli da risultati esistenti")
    p_scrape.add_argument("--search-id", type=int, help="ID ricerca")
    p_scrape.add_argument("--all", action="store_true", help="Estrae da tutte le ricerche senza articoli")

    p_list = sub.add_parser("list", help="Elenca ricerche, risultati o articoli")
    p_list.add_argument("what", nargs="?", choices=["searches", "results", "articles"], default="searches")
    p_list.add_argument("--search-id", type=int, help="Filtra per ID ricerca")

    p_export = sub.add_parser("export", help="Esporta risultati/articoli")
    p_export.add_argument("--search-id", type=int, required=True, help="ID ricerca")
    p_export.add_argument("--format", choices=["csv", "json"], default="csv")
    p_export.add_argument("--output", help="File di output (default: stdout per JSON, export_<id>.csv)")

    sub.add_parser("init", help="Crea config.yaml di esempio")

    return parser


def cmd_search(args):
    kw = dict(keywords=args.keywords, site=args.site, region=args.region,
              safesearch=args.safesearch, timelimit=args.timelimit, max_results=args.max)

    if not args.no_save:
        search_id = db.insert_search(
            name=args.name or args.keywords[:50],
            keywords=args.keywords,
            media_site=args.site,
            region=args.region,
            safesearch=args.safesearch,
            timelimit=args.timelimit,
            max_results=args.max,
        )
        console.print(f"[dim]Search #{search_id} started[/dim]")

    results = searcher.search_ddg(**kw)

    if not results:
        console.print("[yellow]Nessun risultato[/yellow]")
        if not args.no_save:
            db.update_search_status(search_id, "failed")
        return

    table = Table(title=f"Risultati: {args.keywords}", box=box.SIMPLE)
    table.add_column("#", style="dim")
    table.add_column("Titolo")
    table.add_column("URL", style="blue")
    table.add_column("Snippet", style="dim", no_wrap=False)

    for i, r in enumerate(results, 1):
        title = r.get("title", "")[:60]
        href = r.get("href", "")[:70]
        body = r.get("body", "")[:80]
        table.add_row(str(i), title, href, body)

    console.print(table)

    if not args.no_save:
        count = 0
        for pos, r in enumerate(results, 1):
            if db.insert_result(search_id, r, pos):
                count += 1
        db.update_search_status(search_id, "completed")
        console.print(f"[green]Salvati {count} risultati (search #{search_id})[/green]")

        if args.extract:
            cmd_scrape_internal(search_id)
    else:
        print("\n" + json.dumps(results, indent=2, ensure_ascii=False))


def cmd_run(args):
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        console.print("[red]config.yaml non trovato. Lancia 'python main.py init' per crearne uno.[/red]")
        return

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    profiles = cfg.get("searches", [])
    if not profiles:
        console.print("[yellow]Nessun profilo in config.yaml[/yellow]")
        return

    if args.profile:
        profiles = [p for p in profiles if p.get("name") == args.profile]
        if not profiles:
            console.print(f"[red]Profilo '{args.profile}' non trovato[/red]")
            return

    for profile in profiles:
        name = profile.get("name", "unnamed")
        console.print(f"\n[bold]Esecuzione profilo: {name}[/bold]")

        kw = {
            "site": None,
            "region": "wt-wt",
            "safesearch": "moderate",
            "timelimit": None,
            "max_results": 20,
        }

        sites = profile.get("media_sites", [])
        primary_site = sites[0] if sites else None

        kw.update({
            "keywords": profile["keywords"],
            "site": primary_site,
            "region": profile.get("region", "wt-wt"),
            "safesearch": profile.get("safesearch", "moderate"),
            "timelimit": profile.get("timelimit"),
            "max_results": profile.get("max_results", 20),
        })

        search_id = db.insert_search(
            name=name,
            keywords=profile["keywords"],
            media_site=primary_site,
            region=kw["region"],
            safesearch=kw["safesearch"],
            timelimit=kw["timelimit"],
            date_start=profile.get("date_from"),
            date_end=profile.get("date_to"),
            max_results=kw["max_results"],
        )

        results = searcher.search_ddg(**kw)

        if not results:
            console.print("[yellow]  Nessun risultato[/yellow]")
            db.update_search_status(search_id, "completed")
            continue

        count = 0
        for pos, r in enumerate(results, 1):
            if db.insert_result(search_id, r, pos):
                count += 1

        db.update_search_status(search_id, "completed")
        console.print(f"  [green]{count} risultati salvati (search #{search_id})[/green]")

        if profile.get("extract_articles", False) and count > 0:
            cmd_scrape_internal(search_id)


def cmd_scrape_internal(search_id):
    console.print(f"[bold]Estrazione articoli per search #{search_id}...[/bold]")
    results = db.get_unscraped_results()
    results = [r for r in results if r["search_id"] == search_id]

    if not results:
        console.print("[yellow]  Nessun risultato da estrarre[/yellow]")
        return

    articles = scraper.scrape_results(results)
    saved = 0
    for result_id, article in articles:
        if db.insert_article(result_id, article):
            saved += 1

    console.print(f"[green]{saved}/{len(articles)} articoli salvati[/green]")


def cmd_scrape(args):
    if args.all:
        db.init_db()
        results = db.get_unscraped_results()
        if not results:
            console.print("[yellow]Nessun risultato senza articolo[/yellow]")
            return
        by_search = {}
        for r in results:
            by_search.setdefault(r["search_id"], []).append(r)
        for sid, reslist in by_search.items():
            console.print(f"[bold]Search #{sid}: {len(reslist)} risultati da estrarre[/bold]")
            articles = scraper.scrape_results(reslist)
            saved = 0
            for rid, article in articles:
                if db.insert_article(rid, article):
                    saved += 1
            console.print(f"[green]  {saved}/{len(articles)} salvati[/green]")
    elif args.search_id:
        cmd_scrape_internal(args.search_id)
    else:
        console.print("Usa --search-id <id> o --all")


def cmd_list(args):
    db.init_db()

    if args.what == "searches":
        rows = db.get_searches()
        if not rows:
            console.print("[yellow]Nessuna ricerca[/yellow]")
            return
        table = Table(title="Ricerche", box=box.SIMPLE)
        table.add_column("ID")
        table.add_column("Nome")
        table.add_column("Keywords")
        table.add_column("Sito")
        table.add_column("Risultati")
        table.add_column("Stato")
        table.add_column("Data")
        for r in rows:
            cnt = db.result_count(r["id"])
            table.add_row(str(r["id"]), r["name"] or "", r["keywords"] or "",
                          r["media_site"] or "", str(cnt), r["status"] or "",
                          str(r["created_at"])[:19])
        console.print(table)

    elif args.what == "results":
        sid = args.search_id or console.input("[bold]Search ID: [/bold]")
        rows = db.get_results(int(sid))
        if not rows:
            console.print("[yellow]Nessun risultato[/yellow]")
            return
        table = Table(title=f"Risultati search #{sid}", box=box.SIMPLE)
        table.add_column("ID")
        table.add_column("Titolo")
        table.add_column("URL")
        table.add_column("Pubblicato")
        for r in rows:
            table.add_row(str(r["id"]), (r["title"] or "")[:60],
                          (r["url"] or "")[:60], r["published"] or "")
        console.print(table)

    elif args.what == "articles":
        sid = args.search_id or console.input("[bold]Search ID: [/bold]")
        rows = db.get_articles(int(sid))
        if not rows:
            console.print("[yellow]Nessun articolo[/yellow]")
            return
        table = Table(title=f"Articoli search #{sid}", box=box.SIMPLE)
        table.add_column("ID")
        table.add_column("Titolo")
        table.add_column("Autore")
        table.add_column("Data")
        table.add_column("Lingua")
        for r in rows:
            table.add_row(str(r["id"]), (r["scraped_title"] or "")[:60],
                          r["author"] or "", r["date"] or "", r["language"] or "")
        console.print(table)


def cmd_export(args):
    db.init_db()
    search = db.get_search(args.search_id)
    if not search:
        console.print(f"[red]Search #{args.search_id} non trovata[/red]")
        return

    results = db.get_results(args.search_id)
    articles = {a["result_id"]: a for a in db.get_articles(args.search_id)}

    data = []
    for r in results:
        item = {
            "title": r["title"],
            "url": r["url"],
            "snippet": r["snippet"],
            "published": r["published"],
            "position": r["position"],
        }
        a = articles.get(r["id"])
        if a:
            item.update({
                "article_title": a["scraped_title"],
                "article_author": a["author"],
                "article_date": a["date"],
                "article_language": a["language"],
                "article_text": a["text_content"][:500],
            })
        data.append(item)

    output = args.output
    if args.format == "csv":
        if not output:
            output = f"export_{args.search_id}.csv"
        with open(output, "w", newline="", encoding="utf-8") as f:
            if not data:
                f.write("")
            else:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        console.print(f"[green]Esportati {len(data)} risultati in {output}[/green]")
    else:
        if not output:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Esportati {len(data)} risultati in {output}[/green]")


def cmd_init(_args=None):
    example = {
        "searches": [
            {
                "name": "ucraina-repubblica",
                "keywords": "Ucraina AND guerra",
                "media_sites": ["repubblica.it"],
                "region": "it-it",
                "safesearch": "moderate",
                "timelimit": None,
                "date_from": None,
                "date_to": None,
                "max_results": 50,
                "extract_articles": True,
            },
            {
                "name": "intelligenza-artificiale",
                "keywords": "intelligenza artificiale",
                "media_sites": [],
                "region": "wt-wt",
                "safesearch": "moderate",
                "timelimit": "m",
                "date_from": None,
                "date_to": None,
                "max_results": 20,
                "extract_articles": False,
            },
        ]
    }
    if os.path.exists("config.yaml"):
        try:
            overwrite = console.input("[yellow]config.yaml esiste. Sovrascrivere? (s/N): [/yellow]")
            if overwrite.lower() != "s":
                console.print("[dim]Annullato[/dim]")
                return
        except (EOFError, OSError):
            pass

    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(example, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print("[green]config.yaml creato![/green]")
    console.print("Personalizzalo con i tuoi profili, poi lancia:")
    console.print("  python main.py run --all")
