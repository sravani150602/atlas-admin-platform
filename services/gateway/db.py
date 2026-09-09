import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

def connect():
    path = os.getenv("DATABASE_PATH", "data/atlas.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db

@contextmanager
def transaction():
    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally: db.close()

def initialize():
    with transaction() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('viewer','operator','admin')),
            active INTEGER NOT NULL DEFAULT 1, version INTEGER NOT NULL DEFAULT 1,
            salt TEXT, password_hash TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS sessions (
            digest TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
            csrf TEXT NOT NULL, expires INTEGER NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY, actor_id TEXT NOT NULL REFERENCES users(id),
            target_id TEXT NOT NULL REFERENCES users(id), action TEXT NOT NULL,
            role TEXT NOT NULL, target_version INTEGER NOT NULL,
            reason TEXT NOT NULL, provider TEXT NOT NULL, risk INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', created INTEGER NOT NULL, expires INTEGER NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER NOT NULL,
            actor_id TEXT NOT NULL, action TEXT NOT NULL, target_id TEXT NOT NULL,
            details TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS flags (
            name TEXT PRIMARY KEY, percent INTEGER NOT NULL CHECK(percent BETWEEN 0 AND 100),
            version INTEGER NOT NULL DEFAULT 1)''')
        db.execute("INSERT OR IGNORE INTO flags(name,percent) VALUES ('ai_assistant',100)")
        db.execute("INSERT OR IGNORE INTO flags(name,percent) VALUES ('compact_rows',0)")
        if db.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
            password = os.getenv("ADMIN_PASSWORD", "")
            if len(password) < 14: raise RuntimeError("Set ADMIN_PASSWORD to at least 14 characters")
            salt = secrets.token_hex(16)
            db.execute("INSERT INTO users(id,name,email,role,salt,password_hash) VALUES (?,?,?,?,?,?)",
                ("u-admin", "Workspace administrator", os.getenv("ADMIN_EMAIL", "admin@example.test"),
                 "admin", salt, password_hash(password, salt)))
            if os.getenv("SEED_DEMO", "true") == "true":
                db.executemany("INSERT INTO users(id,name,email,role,active) VALUES (?,?,?,?,?)", [
                    ("u-jordan", "Jordan Lee", "jordan@example.test", "operator", 1),
                    ("u-priya", "Priya Rao", "priya@example.test", "viewer", 1),
                    ("u-morgan", "Morgan Chen", "morgan@example.test", "viewer", 0),
                    ("u-alex", "Alex Rivera", "alex@example.test", "viewer", 1)])
