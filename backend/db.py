"""Database connection utility for SQLite."""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/agrisight.db")


def get_connection():
    """Return a connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def query(sql, params=()):
    """Run a SELECT query and return list of dicts."""
    conn = get_connection()
    cur = conn.execute(sql, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def query_one(sql, params=()):
    """Run a SELECT query and return a single dict (or None)."""
    conn = get_connection()
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
