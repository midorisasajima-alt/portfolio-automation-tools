# -*- coding: utf-8 -*-
import sqlite3
from contextlib import closing
from typing import Iterable, Tuple, Optional, List, Dict, Any

from config import DB_PATH

SCHEMA = '''
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS walking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                 -- YYYY-MM-DD
    steps INTEGER NOT NULL,
    step_length_m REAL NOT NULL,        -- m/step
    speed_m_per_min REAL NOT NULL,      -- m/min
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                 -- YYYY-MM-DD
    activity_type TEXT NOT NULL,
    mets REAL NOT NULL,
    minutes REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
'''

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()

# CRUD utilities
def insert_walking(date_str: str, steps: int, step_length_m: float, speed_m_per_min: float) -> int:
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO walking_records(date, steps, step_length_m, speed_m_per_min) VALUES (?,?,?,?)",
            (date_str, steps, step_length_m, speed_m_per_min)
        )
        conn.commit()
        return cur.lastrowid

def insert_activity(date_str: str, activity_type: str, mets: float, minutes: float) -> int:
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO activity_records(date, activity_type, mets, minutes) VALUES (?,?,?,?)",
            (date_str, activity_type, mets, minutes)
        )
        conn.commit()
        return cur.lastrowid

def list_walking(start: Optional[str]=None, end: Optional[str]=None):
    q = "SELECT * FROM walking_records"
    params = []
    if start and end:
        q += " WHERE date BETWEEN ? AND ?"
        params = [start, end]
    q += " ORDER BY date DESC, id DESC"
    with closing(get_conn()) as conn:
        return [dict(r) for r in conn.execute(q, params)]

def list_activity(start: Optional[str]=None, end: Optional[str]=None):
    q = "SELECT * FROM activity_records"
    params = []
    if start and end:
        q += " WHERE date BETWEEN ? AND ?"
        params = [start, end]
    q += " ORDER BY date DESC, id DESC"
    with closing(get_conn()) as conn:
        return [dict(r) for r in conn.execute(q, params)]

def update_walking(rec_id: int, date_str: str, steps: int, step_length_m: float, speed_m_per_min: float):
    with closing(get_conn()) as conn:
        conn.execute(
            "UPDATE walking_records SET date=?, steps=?, step_length_m=?, speed_m_per_min=?, updated_at=datetime('now') WHERE id=?",
            (date_str, steps, step_length_m, speed_m_per_min, rec_id)
        )
        conn.commit()

def update_activity(rec_id: int, date_str: str, activity_type: str, mets: float, minutes: float):
    with closing(get_conn()) as conn:
        conn.execute(
            "UPDATE activity_records SET date=?, activity_type=?, mets=?, minutes=?, updated_at=datetime('now') WHERE id=?",
            (date_str, activity_type, mets, minutes, rec_id)
        )
        conn.commit()

def delete_walking(rec_id: int):
    with closing(get_conn()) as conn:
        conn.execute("DELETE FROM walking_records WHERE id=?", (rec_id,))
        conn.commit()

def delete_activity(rec_id: int):
    with closing(get_conn()) as conn:
        conn.execute("DELETE FROM activity_records WHERE id=?", (rec_id,))
        conn.commit()
