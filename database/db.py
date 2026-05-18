import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        if existing["count"] > 0:
            return

        password_hash = generate_password_hash("demo123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash)
        )
        user_id = cursor.lastrowid

        import datetime
        today = datetime.date.today()
        expenses = [
            (user_id, 450.00, "Food", str(today.replace(day=1)), "Breakfast and coffee"),
            (user_id, 1200.00, "Transport", str(today.replace(day=3)), "Monthly metro pass"),
            (user_id, 2500.00, "Bills", str(today.replace(day=5)), "Electricity bill"),
            (user_id, 800.00, "Health", str(today.replace(day=7)), "Medicine and vitamins"),
            (user_id, 600.00, "Entertainment", str(today.replace(day=10)), "Movie tickets"),
            (user_id, 1500.00, "Shopping", str(today.replace(day=12)), "New headphones"),
            (user_id, 350.00, "Food", str(today.replace(day=15)), "Lunch with colleagues"),
            (user_id, 250.00, "Other", str(today.replace(day=18)), "Miscellaneous expense"),
        ]

        for expense in expenses:
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                expense
            )
        conn.commit()
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def get_user_expenses(user_id, limit=10):
    conn = get_db()
    try:
        expenses = conn.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [dict(row) for row in expenses]
    finally:
        conn.close()


def get_expense_stats(user_id):
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT SUM(amount) as total_spent, COUNT(*) as transaction_count FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        top_category_row = conn.execute(
            "SELECT category, SUM(amount) as amount FROM expenses WHERE user_id = ? GROUP BY category ORDER BY amount DESC LIMIT 1",
            (user_id,)
        ).fetchone()

        return {
            "total_spent": result["total_spent"] or 0,
            "transaction_count": result["transaction_count"] or 0,
            "top_category": top_category_row["category"] if top_category_row else "None"
        }
    finally:
        conn.close()


def get_expenses_by_category(user_id):
    conn = get_db()
    try:
        categories = conn.execute(
            "SELECT category as name, SUM(amount) as amount FROM expenses WHERE user_id = ? GROUP BY category ORDER BY amount DESC",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in categories]
    finally:
        conn.close()