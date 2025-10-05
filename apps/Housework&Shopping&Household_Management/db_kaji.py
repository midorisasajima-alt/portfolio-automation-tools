# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from datetime import date
from typing import List, Tuple, Optional

DB_PATH = Path(__file__).parent / "kaji_tasks.db"
BASE_DATE = date(2025, 9, 7)  # 起点

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        mod INTEGER NOT NULL CHECK(mod > 0),
        remainder INTEGER NOT NULL
    );
    """)
    # 同一家事に対して繰越は一意（重複作成を防止）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS carryovers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chore_id INTEGER NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(chore_id) REFERENCES chores(id) ON DELETE CASCADE
    );
    """)
    # その日の「完了」を記録して当日の再表示を抑制（必要に応じて参照）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS done_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chore_id INTEGER NOT NULL,
        done_date TEXT NOT NULL,                 -- 'YYYY-MM-DD'（ローカル日付）
        UNIQUE(chore_id, done_date),
        FOREIGN KEY(chore_id) REFERENCES chores(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_done_date ON done_log(done_date)")
    conn.commit(); conn.close()

def ensure_chore(name: str, mod: int, remainder: int) -> int:
    name = (name or "").strip()
    if not name: raise ValueError("家事名は必須です。")
    if not isinstance(mod, int) or mod <= 0: raise ValueError("mod は正の整数です。")
    if not isinstance(remainder, int) or not (0 <= remainder < mod):
        raise ValueError("余りは 0 以上 mod 未満の整数です。")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO chores(name, mod, remainder) VALUES(?,?,?)", (name, mod, remainder))
    conn.commit()
    cur.execute("SELECT id FROM chores WHERE name=?", (name,))
    row = cur.fetchone(); conn.close()
    if not row: raise RuntimeError("家事の作成/取得に失敗しました。")
    return row[0]

def list_chores() -> List[Tuple[int, str, int, int]]:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, name, mod, remainder FROM chores ORDER BY name COLLATE NOCASE")
    rows = cur.fetchall(); conn.close(); return rows

def update_chore(chore_id: int, name: str, mod: int, remainder: int):
    name = (name or "").strip()
    if not name: raise ValueError("家事名は空にできません。")
    if mod <= 0: raise ValueError("mod は正の整数です。")
    if not (0 <= remainder < mod): raise ValueError("余りは 0 以上 mod 未満。")
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE chores SET name=?, mod=?, remainder=? WHERE id=?", (name, mod, remainder, chore_id))
        if cur.rowcount == 0: raise ValueError("対象が見つかりません。")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback(); raise ValueError("同名の家事が既に存在します。")
    finally:
        conn.close()

def delete_chore(chore_id: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM chores WHERE id=?", (chore_id,))
    if cur.rowcount == 0:
        conn.close(); raise ValueError("対象が見つかりません。")
    conn.commit(); conn.close()

def add_carryover(chore_id: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO carryovers(chore_id) VALUES(?)", (chore_id,))
    conn.commit(); conn.close()

def list_carryovers() -> List[Tuple[int, int, str, int, int]]:
    """戻り値: [(carry_id, chore_id, name, mod, remainder)]"""
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT c.id, ch.id, ch.name, ch.mod, ch.remainder
        FROM carryovers c
        JOIN chores ch ON ch.id = c.chore_id
        ORDER BY c.id ASC
    """)
    rows = cur.fetchall(); conn.close(); return rows

def complete_carryover(carry_id: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM carryovers WHERE id=?", (carry_id,))
    conn.commit(); conn.close()

def mark_done_today(chore_id: int, today_str: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO done_log(chore_id, done_date) VALUES(?,?)", (chore_id, today_str))
    conn.commit(); conn.close()

def is_done_today(chore_id: int, today_str: str) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM done_log WHERE chore_id=? AND done_date=?", (chore_id, today_str))
    ok = cur.fetchone() is not None
    conn.close(); return ok

def days_since_base(d: Optional[date] = None) -> int:
    d = d or date.today()
    return (d - BASE_DATE).days

def todays_chores(d: Optional[date] = None) -> List[Tuple[int, str, int, int]]:
    """
    carryover に載っているものは除外。
    done_log で当日完了済みのものも除外。
    戻り値: [(chore_id, name, mod, remainder)]
    """
    d = d or date.today()
    daycnt = days_since_base(d)
    today_str = d.strftime("%Y-%m-%d")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, name, mod, remainder FROM chores")
    all_rows = cur.fetchall()
    cur.execute("SELECT chore_id FROM carryovers")
    carry_ids = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT chore_id FROM done_log WHERE done_date=?", (today_str,))
    done_ids = {r[0] for r in cur.fetchall()}
    conn.close()
    out = []
    for cid, nm, m, rmd in all_rows:
        if cid in carry_ids or cid in done_ids:
            continue
        if m > 0 and (daycnt % m) == rmd:
            out.append((cid, nm, m, rmd))
    # 表示順は名前昇順
    out.sort(key=lambda x: x[1].lower())
    return out
