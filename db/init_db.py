"""Initialize the SQLite database and create the products table.

Run once: python db/init_db.py
"""
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/agrisight.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
with open("db/schema.sql", encoding="utf-8") as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print(f"Database initialized at {DB_PATH}")
