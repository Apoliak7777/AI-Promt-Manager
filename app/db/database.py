"""SQLite pripojenie, inicializácia schémy a seed default platforiem.

Používame jednu funkciu ``get_connection()``, ktorá vytvorí spojenie na aktuálnu
cestu k DB (z :mod:`app.config`). Cudzie kľúče sú zapnuté, ``row_factory`` vracia
``sqlite3.Row`` (prístup ku stĺpcom podľa mena).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_platforms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    color      TEXT    NOT NULL,
    icon       TEXT,
    is_custom  INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS prompts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id      INTEGER REFERENCES ai_platforms(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    content    TEXT    NOT NULL,
    tags       TEXT    DEFAULT '',
    note       TEXT    DEFAULT '',
    favorite   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id            INTEGER REFERENCES ai_platforms(id) ON DELETE CASCADE,
    name             TEXT    NOT NULL,
    content_md       TEXT    DEFAULT '',
    status           TEXT    NOT NULL DEFAULT 'Nápad',
    linked_prompt_id INTEGER REFERENCES prompts(id) ON DELETE SET NULL,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_ai   ON prompts(ai_id);
CREATE INDEX IF NOT EXISTS idx_projects_ai  ON projects(ai_id);
"""


def get_connection() -> sqlite3.Connection:
    """Vytvorí nové spojenie na aktuálnu DB (cesta z configu)."""
    db_path = config.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Context manager — automatický commit/rollback a close."""
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
    """Vytvorí schému (ak neexistuje) a naseeduje default platformy."""
    with connection() as conn:
        conn.executescript(SCHEMA)
        _seed_default_platforms(conn)
        _seed_default_settings(conn)


def _seed_default_platforms(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM ai_platforms").fetchone()[0]
    if existing:
        return
    rows = [
        (name, color, icon, 0, order)
        for order, (name, color, icon) in enumerate(config.DEFAULT_PLATFORMS)
    ]
    conn.executemany(
        "INSERT INTO ai_platforms (name, color, icon, is_custom, sort_order) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def _seed_default_settings(conn: sqlite3.Connection) -> None:
    defaults = {
        "appearance_mode": "dark",     # dark | light | system
        "accent_color": config.DEFAULT_ACCENT,
        "sort_order": "Obľúbené prvé",
        "auto_backup": "off",          # off | daily | weekly
        "last_backup": "",
        "last_ai_id": "",
    }
    for key, value in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


def reset_connection_target() -> None:
    """Po zmene cesty k DB (v Nastaveniach) znovu inicializuje schému."""
    init_db()
