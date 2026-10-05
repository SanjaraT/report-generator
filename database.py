import sqlite3
import json
import re
from pathlib import Path

DB_PATH = "report.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_rating(rating_text: str) -> int:
    mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    return mapping.get(rating_text, 0)

def parse_availability(availability_text: str) -> int:
    match = re.search(r'\d+', availability_text)
    return int(match.group()) if match else 0

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # books table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            rating INTEGER NOT NULL,
            rating_text TEXT NOT NULL,
            availability INTEGER NOT NULL,
            product_url TEXT,
            source_page INTEGER,
            fetched_at TEXT
        )
    """)

    # reports log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at TEXT NOT NULL,
            file_path TEXT NOT NULL,
            report_date TEXT NOT NULL
        )
    """)

    conn.commit()

    # seed only if empty
    existing = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if existing == 0:
        with open("books.json", encoding="utf-8") as f:
            books = json.load(f)

        for book in books:
            cur.execute("""
                INSERT INTO books (title, price_gbp, rating, rating_text, availability, product_url, source_page, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book["title"],
                book["price_gbp"],
                parse_rating(book["rating_text"]),
                book["rating_text"],
                parse_availability(book["availability_text"]),
                book.get("product_url"),
                book.get("source_page"),
                book.get("fetched_at"),
            ))

        conn.commit()
        print(f"Seeded {len(books)} books into report.db")
    else:
        print(f"Database already has {existing} books — skipping seed")

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully")