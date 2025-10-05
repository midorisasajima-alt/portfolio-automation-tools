import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

DB_PATH = Path("nutrition.db")

SCHEMA = {
    "goals": """
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY CHECK (id=1),
            energy REAL NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            carbohydrate REAL NOT NULL
        );
    """,
    "items": """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genre TEXT NOT NULL,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            energy REAL NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            carbohydrate REAL NOT NULL
        );
    """,
    "records": """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,                -- YYYY-MM-DD
            meal_index INTEGER NOT NULL,       -- 1,2,3...
            item_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
        );
    """,
}

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    for sql in SCHEMA.values():
        cur.execute(sql)
    conn.commit()
    conn.close()


def ensure_seed_goals(goals: Dict[str, float]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM goals")
    c = cur.fetchone()[0]
    if c == 0:
        cur.execute(
            "INSERT INTO goals (id, energy, protein, fat, carbohydrate) VALUES (1, ?, ?, ?, ?)",
            (goals["Energy"], goals["Protein"], goals["Fat"], goals["Carbohydrate"]) 
        )
        conn.commit()
    conn.close()

# --- goals ---

def read_goals() -> Dict[str, float]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT energy, protein, fat, carbohydrate FROM goals WHERE id=1")
    row = cur.fetchone()
    conn.close()
    if row:
        return {"Energy": row[0], "Protein": row[1], "Fat": row[2], "Carbohydrate": row[3]}
    return {}


def update_goals(goals: Dict[str, float]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE goals SET energy=?, protein=?, fat=?, carbohydrate=? WHERE id=1",
        (goals["Energy"], goals["Protein"], goals["Fat"], goals["Carbohydrate"]) 
    )
    conn.commit()
    conn.close()

# --- items ---

def list_genres() -> List[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT genre FROM items ORDER BY genre")
    arr = [r[0] for r in cur.fetchall()]
    conn.close()
    return arr


def list_items_by_genre(genre: str) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE genre=? ORDER BY name", (genre,))
    rows = cur.fetchall()
    conn.close()
    return rows


def list_items(keyword: Optional[str] = None, genre: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    if keyword and genre:
        cur.execute(
            "SELECT * FROM items WHERE genre=? AND name LIKE ? ORDER BY name",
            (genre, f"%{keyword}%")
        )
    elif keyword:
        cur.execute("SELECT * FROM items WHERE name LIKE ? ORDER BY name", (f"%{keyword}%",))
    elif genre:
        cur.execute("SELECT * FROM items WHERE genre=? ORDER BY name", (genre,))
    else:
        cur.execute("SELECT * FROM items ORDER BY genre, name")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_item(item_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    return row


def insert_item(d: Dict[str, Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO items (genre, name, unit, energy, protein, fat, carbohydrate)
        VALUES (?,?,?,?,?,?,?)
        """ ,
        (d["genre"], d["name"], d["unit"], d["energy"], d["protein"], d["fat"], d["carbohydrate"]) 
    )
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return item_id


def update_item(item_id: int, d: Dict[str, Any]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE items SET genre=?, name=?, unit=?, energy=?, protein=?, fat=?, carbohydrate=?
        WHERE id=?
        """ ,
        (d["genre"], d["name"], d["unit"], d["energy"], d["protein"], d["fat"], d["carbohydrate"], item_id)
    )
    conn.commit()
    conn.close()


def delete_item(item_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

# --- records ---

def insert_record(date: str, meal_index: int, item_id: int, quantity: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO records (date, meal_index, item_id, quantity) VALUES (?,?,?,?)",
        (date, meal_index, item_id, quantity)
    )
    conn.commit()
    conn.close()


def list_records(date: Optional[str]=None, meal_index: Optional[int]=None, genre: Optional[str]=None) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    base = """
        SELECT r.id, r.date, r.meal_index, r.quantity, i.id as item_id, i.genre, i.name, i.unit,
               i.energy, i.protein, i.fat, i.carbohydrate
        FROM records r JOIN items i ON r.item_id=i.id
    """
    conds, params = [], []
    if date:
        conds.append("r.date=?"); params.append(date)
    if meal_index is not None:
        conds.append("r.meal_index=?"); params.append(meal_index)
    if genre:
        conds.append("i.genre=?"); params.append(genre)
    if conds:
        base += " WHERE " + " AND ".join(conds)
    base += " ORDER BY r.date, r.meal_index, i.genre, i.name"
    cur.execute(base, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def update_record(record_id: int, *, date: Optional[str]=None, meal_index: Optional[int]=None, item_id: Optional[int]=None, quantity: Optional[float]=None):
    fields, params = [], []
    if date is not None:
        fields.append("date=?"); params.append(date)
    if meal_index is not None:
        fields.append("meal_index=?"); params.append(meal_index)
    if item_id is not None:
        fields.append("item_id=?"); params.append(item_id)
    if quantity is not None:
        fields.append("quantity=?"); params.append(quantity)
    if not fields:
        return
    params.append(record_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE records SET {', '.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()


def delete_record(record_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

# --- analytics ---

def aggregate_between(start: str, end: str) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.date, i.name, i.genre,
               SUM(r.quantity*i.energy) AS energy,
               SUM(r.quantity*i.protein) AS protein,
               SUM(r.quantity*i.fat) AS fat,
               SUM(r.quantity*i.carbohydrate) AS carbohydrate
        FROM records r JOIN items i ON r.item_id=i.id
        WHERE r.date BETWEEN ? AND ?
        GROUP BY r.date, i.name, i.genre
        ORDER BY r.date
        """ ,
        (start, end)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def daily_totals_between(start: str, end: str) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.date,
               SUM(r.quantity*i.energy) AS energy,
               SUM(r.quantity*i.protein) AS protein,
               SUM(r.quantity*i.fat) AS fat,
               SUM(r.quantity*i.carbohydrate) AS carbohydrate
        FROM records r JOIN items i ON r.item_id=i.id
        WHERE r.date BETWEEN ? AND ?
        GROUP BY r.date
        ORDER BY r.date
        """ ,
        (start, end)
    )
    rows = cur.fetchall()
    conn.close()
    return rows
