import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import get_settings


def _sqlite_path() -> Path:
    database_url = get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        raise RuntimeError("This backend currently supports sqlite:/// DATABASE_URL only.")
    return Path(database_url.replace("sqlite:///", "", 1))


def get_connection() -> sqlite3.Connection:
    db_path = _sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT NOT NULL UNIQUE,
              display_name TEXT NOT NULL,
              password_hash TEXT NOT NULL,
              password_salt TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              token_hash TEXT NOT NULL UNIQUE,
              expires_at TEXT NOT NULL,
              revoked_at TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS interests (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              keyword TEXT NOT NULL,
              description TEXT NOT NULL,
              lookback_days INTEGER NOT NULL DEFAULT 3,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS hidden_keywords (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              interest_id INTEGER NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
              keyword TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(interest_id, keyword)
            );

            CREATE TABLE IF NOT EXISTS articles (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              source TEXT NOT NULL,
              url TEXT NOT NULL UNIQUE,
              description TEXT NOT NULL,
              published_at TEXT NOT NULL,
              raw_payload TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS candidate_articles (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              interest_id INTEGER NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
              article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
              matched_keywords TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(interest_id, article_id)
            );

            CREATE TABLE IF NOT EXISTS ai_decisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              candidate_article_id INTEGER NOT NULL REFERENCES candidate_articles(id) ON DELETE CASCADE,
              accepted INTEGER NOT NULL,
              reason TEXT NOT NULL,
              summary TEXT NOT NULL,
              bullet_points TEXT NOT NULL,
              ai_mode TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS article_reads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
              read_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(user_id, article_id)
            );

            CREATE TABLE IF NOT EXISTS article_scraps (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              candidate_article_id INTEGER NOT NULL REFERENCES candidate_articles(id) ON DELETE CASCADE,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(user_id, candidate_article_id)
            );

            CREATE TABLE IF NOT EXISTS ai_jobs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              job_type TEXT NOT NULL,
              status TEXT NOT NULL,
              payload TEXT NOT NULL,
              result TEXT,
              error_message TEXT,
              locked_by TEXT,
              locked_at TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS ai_workers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              worker_id TEXT NOT NULL UNIQUE,
              status TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              current_job_id INTEGER,
              processed_count INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _add_column_if_missing(conn, "interests", "lookback_days", "INTEGER NOT NULL DEFAULT 3")


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
