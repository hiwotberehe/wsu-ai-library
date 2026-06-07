import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import pandas as pd

DB_PATH = "library.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        role TEXT DEFAULT 'student',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login TEXT
    )''')

    # Books table (local additions)
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id TEXT UNIQUE,
        title TEXT NOT NULL,
        authors TEXT,
        publisher TEXT,
        published_date TEXT,
        description TEXT,
        page_count INTEGER,
        categories TEXT,
        average_rating REAL DEFAULT 0,
        ratings_count INTEGER DEFAULT 0,
        language TEXT DEFAULT 'en',
        thumbnail TEXT,
        isbn_13 TEXT,
        isbn_10 TEXT,
        copies_total INTEGER DEFAULT 3,
        copies_available INTEGER DEFAULT 3,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Borrow records
    c.execute('''CREATE TABLE IF NOT EXISTS borrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id TEXT,
        borrow_date TEXT DEFAULT CURRENT_TIMESTAMP,
        due_date TEXT,
        return_date TEXT,
        status TEXT DEFAULT 'borrowed',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # Reservations
    c.execute('''CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id TEXT,
        reserved_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # User reading history (for recommendations)
    c.execute('''CREATE TABLE IF NOT EXISTS reading_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id TEXT,
        categories TEXT,
        viewed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # Book ratings by users
    c.execute('''CREATE TABLE IF NOT EXISTS user_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id TEXT,
        rating INTEGER,
        review TEXT,
        rated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, book_id)
    )''')

    conn.commit()

    # Create default admin
    try:
        c.execute("INSERT INTO users (username, password, full_name, email, role) VALUES (?,?,?,?,?)",
                  ("admin", hash_password("admin123"), "Administrator", "admin@library.wsu.edu", "admin"))
        conn.commit()
    except:
        pass

    # Create demo students
    demo_users = [
        ("student1", hash_password("student123"), "Samual Woticha", "samual@wsu.edu", "student"),
        ("teacher1", hash_password("teacher123"), "Prof. Destaye Ukumo", "destaye@wsu.edu", "teacher"),
        ("librarian1", hash_password("lib123"), "Library Staff", "library@wsu.edu", "librarian"),
    ]
    for u in demo_users:
        try:
            c.execute("INSERT INTO users (username, password, full_name, email, role) VALUES (?,?,?,?,?)", u)
        except:
            pass
    conn.commit()
    conn.close()

# ── User helpers ──────────────────────────────────────────────────────────────
def authenticate_user(username: str, password: str):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    ).fetchone()
    if user:
        conn.execute("UPDATE users SET last_login=? WHERE id=?",
                     (datetime.now().isoformat(), user["id"]))
        conn.commit()
    conn.close()
    return dict(user) if user else None

def register_user(username, password, full_name, email, role="student"):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password, full_name, email, role) VALUES (?,?,?,?,?)",
            (username, hash_password(password), full_name, email, role)
        )
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists."

def get_all_users():
    conn = get_conn()
    users = conn.execute("SELECT id, username, full_name, email, role, created_at, last_login FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]

# ── Book helpers ──────────────────────────────────────────────────────────────
def import_books_from_csv(csv_path: str, limit: int = 500):
    """Import books from CSV into SQLite (first time only)."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if count > 0:
        conn.close()
        return
    df = pd.read_csv(csv_path, nrows=limit)
    df = df.fillna("")
    for _, row in df.iterrows():
        try:
            conn.execute("""INSERT OR IGNORE INTO books
                (book_id, title, authors, publisher, published_date, description,
                 page_count, categories, average_rating, ratings_count, language,
                 thumbnail, isbn_13, isbn_10)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (str(row.get("book_id","")), str(row.get("title","")),
                 str(row.get("authors","")), str(row.get("publisher","")),
                 str(row.get("published_date","")), str(row.get("description","")),
                 int(row["page_count"]) if str(row.get("page_count","")).replace(".","").isdigit() else 0,
                 str(row.get("categories","")), float(row["average_rating"]) if str(row.get("average_rating","")).replace(".","").isdigit() else 0.0,
                 int(row["ratings_count"]) if str(row.get("ratings_count","")).replace(".","").isdigit() else 0,
                 str(row.get("language","en")), str(row.get("thumbnail","")),
                 str(row.get("isbn_13","")), str(row.get("isbn_10","")))
            )
        except Exception:
            pass
    conn.commit()
    conn.close()

def get_books(limit=50, offset=0, search=None, category=None):
    conn = get_conn()
    q = "SELECT * FROM books WHERE 1=1"
    params = []
    if search:
        q += " AND (title LIKE ? OR authors LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if category:
        q += " AND categories LIKE ?"
        params.append(f"%{category}%")
    q += f" LIMIT {limit} OFFSET {offset}"
    books = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(b) for b in books]

def get_book_by_id(book_id: str):
    conn = get_conn()
    book = conn.execute("SELECT * FROM books WHERE book_id=?", (book_id,)).fetchone()
    conn.close()
    return dict(book) if book else None

def get_all_books_df():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    return df

def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT categories FROM books WHERE categories != ''").fetchall()
    conn.close()
    cats = set()
    for r in rows:
        for c in str(r[0]).split(","):
            c = c.strip()
            if c and c != "nan":
                cats.add(c)
    return sorted(list(cats))[:40]

# ── Borrow helpers ────────────────────────────────────────────────────────────
def borrow_book(user_id: int, book_id: str):
    conn = get_conn()
    book = conn.execute("SELECT copies_available FROM books WHERE book_id=?", (book_id,)).fetchone()
    if not book or book["copies_available"] <= 0:
        conn.close()
        return False, "No copies available."
    # check if already borrowed
    existing = conn.execute(
        "SELECT id FROM borrows WHERE user_id=? AND book_id=? AND status='borrowed'",
        (user_id, book_id)
    ).fetchone()
    if existing:
        conn.close()
        return False, "You already have this book borrowed."
    due = (datetime.now() + timedelta(days=14)).isoformat()
    conn.execute("INSERT INTO borrows (user_id, book_id, due_date) VALUES (?,?,?)",
                 (user_id, book_id, due))
    conn.execute("UPDATE books SET copies_available=copies_available-1 WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()
    return True, f"Book borrowed! Due: {due[:10]}"

def return_book(borrow_id: int, book_id: str):
    conn = get_conn()
    conn.execute("UPDATE borrows SET status='returned', return_date=? WHERE id=?",
                 (datetime.now().isoformat(), borrow_id))
    conn.execute("UPDATE books SET copies_available=copies_available+1 WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()

def get_user_borrows(user_id: int):
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.id, b.book_id, b.borrow_date, b.due_date, b.return_date, b.status,
               bk.title, bk.authors, bk.thumbnail
        FROM borrows b JOIN books bk ON b.book_id=bk.book_id
        WHERE b.user_id=?
        ORDER BY b.borrow_date DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_borrows():
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.id, b.book_id, b.borrow_date, b.due_date, b.return_date, b.status,
               u.username, u.full_name, bk.title
        FROM borrows b
        JOIN users u ON b.user_id=u.id
        JOIN books bk ON b.book_id=bk.book_id
        ORDER BY b.borrow_date DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_reading_history(user_id: int, book_id: str, categories: str):
    conn = get_conn()
    conn.execute("INSERT INTO reading_history (user_id, book_id, categories) VALUES (?,?,?)",
                 (user_id, book_id, categories))
    conn.commit()
    conn.close()

def get_user_history_categories(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT categories FROM reading_history WHERE user_id=? ORDER BY viewed_at DESC LIMIT 20",
        (user_id,)
    ).fetchall()
    conn.close()
    cats = []
    for r in rows:
        for c in str(r[0]).split(","):
            c = c.strip()
            if c and c != "nan":
                cats.append(c)
    return cats

# ── Analytics helpers ─────────────────────────────────────────────────────────
def get_analytics():
    conn = get_conn()
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_borrows = conn.execute("SELECT COUNT(*) FROM borrows WHERE status='borrowed'").fetchone()[0]
    available_books = conn.execute("SELECT SUM(copies_available) FROM books").fetchone()[0] or 0

    # Most borrowed
    top_books = conn.execute("""
        SELECT bk.title, COUNT(*) as cnt FROM borrows b
        JOIN books bk ON b.book_id=bk.book_id
        GROUP BY b.book_id ORDER BY cnt DESC LIMIT 10
    """).fetchall()

    # Category distribution
    cat_dist = conn.execute("""
        SELECT categories, COUNT(*) as cnt FROM books
        WHERE categories != '' GROUP BY categories
        ORDER BY cnt DESC LIMIT 15
    """).fetchall()

    # Recent activity (last 30 days)
    monthly = conn.execute("""
        SELECT DATE(borrow_date) as day, COUNT(*) as cnt
        FROM borrows WHERE borrow_date >= date('now','-30 days')
        GROUP BY day ORDER BY day
    """).fetchall()

    conn.close()
    return {
        "total_books": total_books,
        "total_users": total_users,
        "active_borrows": active_borrows,
        "available_books": available_books,
        "top_books": [dict(r) for r in top_books],
        "cat_dist": [dict(r) for r in cat_dist],
        "monthly": [dict(r) for r in monthly],
    }
