import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'accounting.db')


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            category_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
    """)

    existing = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing == 0:
        defaults = [
            ('工资', 'income'), ('兼职', 'income'),
            ('餐饮', 'expense'), ('交通', 'expense'),
            ('购物', 'expense'), ('娱乐', 'expense'),
            ('居住', 'expense'), ('其他', 'expense'),
        ]
        conn.executemany(
            "INSERT INTO categories (name, type) VALUES (?, ?)", defaults
        )
        conn.commit()
