# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

DB_PATH = Path(__file__).parent / "shopping_list.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sl_genres(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sl_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genre_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(genre_id, name),
        FOREIGN KEY(genre_id) REFERENCES sl_genres(id) ON DELETE CASCADE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sl_list_state(
        item_id INTEGER PRIMARY KEY,
        to_buy INTEGER NOT NULL DEFAULT 0,     -- 0/1
        memo TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(item_id) REFERENCES sl_items(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_genre ON sl_items(genre_id)")
    conn.commit(); conn.close()

def seed_example():
    """任意：初期データ（必要なければ呼ばない）"""
    conn = get_conn(); cur = conn.cursor()
    for g in ["Food", "Non-Food"]:
        cur.execute("INSERT OR IGNORE INTO sl_genres(name) VALUES(?)", (g,))
    # Food
    cur.execute("SELECT id FROM sl_genres WHERE name='Food'"); gid_food = cur.fetchone()[0]
    for n in ["milk","eggs","bread","olive oil","salt","sugar"]:
        cur.execute("INSERT OR IGNORE INTO sl_items(genre_id,name) VALUES(?,?)", (gid_food,n))
    # Non-Food
    cur.execute("SELECT id FROM sl_genres WHERE name='Non-Food'"); gid_nf = cur.fetchone()[0]
    for n in ["sponge","trash bags","tissues"]:
        cur.execute("INSERT OR IGNORE INTO sl_items(genre_id,name) VALUES(?,?)", (gid_nf,n))
    conn.commit(); conn.close()

# ── Genres ─────────────────────────────────────────────────────────
def list_genres() -> List[Tuple[int,str]]:
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT id,name FROM sl_genres ORDER BY name COLLATE NOCASE")
    rows=cur.fetchall(); conn.close(); return rows

def ensure_genre(name:str)->int:
    name=(name or "").strip()
    if not name: raise ValueError("ジャンル名は必須です。")
    conn=get_conn(); cur=conn.cursor()
    cur.execute("INSERT OR IGNORE INTO sl_genres(name) VALUES(?)",(name,))
    conn.commit()
    cur.execute("SELECT id FROM sl_genres WHERE name=?",(name,)); gid=cur.fetchone()[0]
    conn.close(); return gid

def update_genre_name(genre_id:int,new_name:str):
    new_name=(new_name or "").strip()
    if not new_name: raise ValueError("ジャンル名は空にできません。")
    conn=get_conn(); cur=conn.cursor()
    cur.execute("UPDATE sl_genres SET name=? WHERE id=?", (new_name,genre_id))
    if cur.rowcount==0: conn.close(); raise ValueError("ジャンルが見つかりません。")
    conn.commit(); conn.close()

def delete_genre(genre_id:int):
    conn=get_conn(); cur=conn.cursor()
    cur.execute("DELETE FROM sl_genres WHERE id=?", (genre_id,))
    if cur.rowcount==0: conn.close(); raise ValueError("ジャンルが見つかりません。")
    conn.commit(); conn.close()

# ── Items ──────────────────────────────────────────────────────────
def list_items_by_genre(genre_id:int)->List[Tuple[int,str]]:
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT id,name FROM sl_items WHERE genre_id=? ORDER BY name COLLATE NOCASE",(genre_id,))
    rows=cur.fetchall(); conn.close(); return rows

def search_items(q:str, genre_id:Optional[int]=None)->List[Tuple[int,int,str]]:
    q=(q or "").strip()
    conn=get_conn(); cur=conn.cursor()
    if genre_id:
        if q:
            cur.execute("""
                SELECT id, genre_id, name FROM sl_items
                WHERE genre_id=? AND name LIKE ?
                ORDER BY name COLLATE NOCASE
            """, (genre_id, f"%{q}%"))
        else:
            cur.execute("SELECT id, genre_id, name FROM sl_items WHERE genre_id=? ORDER BY name COLLATE NOCASE",(genre_id,))
    else:
        if q:
            cur.execute("SELECT id, genre_id, name FROM sl_items WHERE name LIKE ? ORDER BY name COLLATE NOCASE",(f"%{q}%",))
        else:
            cur.execute("SELECT id, genre_id, name FROM sl_items ORDER BY name COLLATE NOCASE")
    rows=cur.fetchall(); conn.close(); return rows

def ensure_item(genre_id:int, name:str)->int:
    name=(name or "").strip()
    if not name: raise ValueError("品目名は必須です。")
    conn=get_conn(); cur=conn.cursor()
    cur.execute("INSERT OR IGNORE INTO sl_items(genre_id,name) VALUES(?,?)",(genre_id,name))
    conn.commit()
    cur.execute("SELECT id FROM sl_items WHERE genre_id=? AND name=?", (genre_id,name))
    row=cur.fetchone(); conn.close()
    if not row: raise RuntimeError("品目の作成/取得に失敗しました。")
    return row[0]

def update_item_name(item_id:int, new_name:str):
    new_name=(new_name or "").strip()
    if not new_name: raise ValueError("品目名は空にできません。")
    conn=get_conn(); cur=conn.cursor()
    cur.execute("UPDATE sl_items SET name=? WHERE id=?", (new_name,item_id))
    if cur.rowcount==0: conn.close(); raise ValueError("品目が見つかりません。")
    conn.commit(); conn.close()

def delete_item(item_id:int):
    conn=get_conn(); cur=conn.cursor()
    cur.execute("DELETE FROM sl_items WHERE id=?", (item_id,))
    if cur.rowcount==0: conn.close(); raise ValueError("品目が見つかりません。")
    conn.commit(); conn.close()

# ── List state (to_buy / memo) ─────────────────────────────────────
def get_state(item_id:int)->Tuple[int,str]:
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT to_buy, memo FROM sl_list_state WHERE item_id=?", (item_id,))
    row=cur.fetchone()
    if not row:
        cur.execute("INSERT OR IGNORE INTO sl_list_state(item_id,to_buy,memo) VALUES(?,0,'')", (item_id,))
        conn.commit()
        row=(0,"")
    conn.close(); return int(row[0]), str(row[1])

def set_to_buy(item_id:int, flag:bool):
    v=1 if flag else 0
    conn=get_conn(); cur=conn.cursor()
    cur.execute("""
        INSERT INTO sl_list_state(item_id,to_buy,memo) VALUES(?,?, '')
        ON CONFLICT(item_id) DO UPDATE SET to_buy=excluded.to_buy
    """,(item_id,v))
    conn.commit(); conn.close()

def set_memo(item_id:int, memo:str):
    memo=(memo or "")
    conn=get_conn(); cur=conn.cursor()
    cur.execute("""
        INSERT INTO sl_list_state(item_id,to_buy,memo) VALUES(?,0,?)
        ON CONFLICT(item_id) DO UPDATE SET memo=excluded.memo
    """,(item_id,memo))
    conn.commit(); conn.close()

def list_to_buy_by_genre(genre_id:int)->List[Tuple[int,str,str]]:
    """戻り値: [(item_id, item_name, memo)] で to_buy=1 のみ"""
    conn=get_conn(); cur=conn.cursor()
    cur.execute("""
        SELECT i.id, i.name, COALESCE(s.memo,'')
        FROM sl_items i
        JOIN sl_list_state s ON s.item_id = i.id
        WHERE i.genre_id=? AND s.to_buy=1
        ORDER BY i.name COLLATE NOCASE
    """,(genre_id,))
    rows=cur.fetchall(); conn.close(); return rows
