import sqlite3
import hashlib
import os

DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Spēlētāju tabula
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
    """)
    # Rezultātu tabula
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            level INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password: str, salt: str = None):
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pwd_hash, salt