import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "duckducksearch.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                keywords TEXT NOT NULL,
                media_site TEXT,
                region TEXT,
                safesearch TEXT DEFAULT 'moderate',
                timelimit TEXT,
                date_start TEXT,
                date_end TEXT,
                max_results INTEGER DEFAULT 20,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
                title TEXT,
                url TEXT NOT NULL,
                snippet TEXT,
                published TEXT,
                position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(search_id, url)
            );

            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL REFERENCES results(id) ON DELETE CASCADE UNIQUE,
                scraped_title TEXT,
                author TEXT,
                text_content TEXT,
                date TEXT,
                language TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def insert_search(**kw):
    cols = ["name", "keywords", "media_site", "region", "safesearch",
            "timelimit", "date_start", "date_end", "max_results", "status"]
    data = {k: kw.get(k) for k in cols if k in kw}
    if "status" not in data:
        data["status"] = "running"
    keys = ", ".join(data)
    vals = ", ".join("?" for _ in data)
    with get_db() as db:
        cur = db.execute(f"INSERT INTO searches ({keys}) VALUES ({vals})", list(data.values()))
        return cur.lastrowid


def update_search_status(search_id, status):
    with get_db() as db:
        db.execute("UPDATE searches SET status = ? WHERE id = ?", (status, search_id))


def get_search(search_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM searches WHERE id = ?", (search_id,)).fetchone()
        return dict(row) if row else None


def get_searches(limit=50):
    with get_db() as db:
        rows = db.execute("SELECT * FROM searches ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def insert_result(search_id, result, position):
    with get_db() as db:
        try:
            db.execute(
                """INSERT OR IGNORE INTO results (search_id, title, url, snippet, published, position)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (search_id, result.get("title", ""), result.get("href", ""),
                 result.get("body", ""), result.get("published", ""), position)
            )
            return True
        except Exception:
            return False


def result_count(search_id):
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) as cnt FROM results WHERE search_id = ?", (search_id,)).fetchone()
        return row["cnt"] if row else 0


def get_results(search_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM results WHERE search_id = ? ORDER BY position", (search_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_unscraped_results(limit=100):
    with get_db() as db:
        rows = db.execute(
            """SELECT r.* FROM results r
               LEFT JOIN articles a ON a.result_id = r.id
               WHERE a.id IS NULL
               ORDER BY r.id
               LIMIT ?""", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def insert_article(result_id, article):
    with get_db() as db:
        try:
            db.execute(
                """INSERT OR IGNORE INTO articles (result_id, scraped_title, author, text_content, date, language)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (result_id, article.get("scraped_title", ""), article.get("author", ""),
                 article.get("text_content", ""), article.get("date", ""), article.get("language", ""))
            )
            return True
        except Exception:
            return False


def get_articles(search_id):
    with get_db() as db:
        rows = db.execute(
            """SELECT a.*, r.title as result_title, r.url
               FROM articles a
               JOIN results r ON r.id = a.result_id
               WHERE r.search_id = ?
               ORDER BY a.id""", (search_id,)
        ).fetchall()
        return [dict(r) for r in rows]
