"""
database.py
------------
All local storage for Shiv lives in one SQLite file: shiv.db
No internet, no external service — just a file on your laptop.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shiv.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,          -- 'voice' or 'web'
            command_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            intent TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            remind_at TEXT NOT NULL,       -- ISO datetime string
            content TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()

    # sensible defaults, only inserted once
    defaults = {
        "user_name": "Rajshree",
        "assistant_name": "Shiv",
        "default_city": "Jaipur",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO preferences (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


# ---------------- commands_log ----------------
def log_command(source, command_text, response_text, intent=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO commands_log (timestamp, source, command_text, response_text, intent) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), source, command_text, response_text, intent),
    )
    conn.commit()
    conn.close()


def get_history(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM commands_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- notes ----------------
def add_note(content):
    conn = get_connection()
    conn.execute(
        "INSERT INTO notes (timestamp, content) VALUES (?, ?)",
        (datetime.now().isoformat(timespec="seconds"), content),
    )
    conn.commit()
    conn.close()


def get_notes(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_note(note_id):
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


# ---------------- reminders ----------------
def add_reminder(remind_at_iso, content):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reminders (created_at, remind_at, content, done) VALUES (?, ?, ?, 0)",
        (datetime.now().isoformat(timespec="seconds"), remind_at_iso, content),
    )
    conn.commit()
    conn.close()


def get_due_reminders():
    """Reminders whose time has passed and are not yet marked done."""
    conn = get_connection()
    now_iso = datetime.now().isoformat(timespec="seconds")
    rows = conn.execute(
        "SELECT * FROM reminders WHERE done = 0 AND remind_at <= ? ORDER BY remind_at ASC",
        (now_iso,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_reminders(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reminders ORDER BY remind_at ASC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_reminder_done(reminder_id):
    conn = get_connection()
    conn.execute("UPDATE reminders SET done = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


def delete_reminder(reminder_id):
    conn = get_connection()
    conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


# ---------------- preferences ----------------
def get_preference(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_preference(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO preferences (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_all_preferences():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM preferences").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}
