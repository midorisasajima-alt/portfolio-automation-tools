import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

DB_PATH = Path(__file__).parent / "kaji.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS genres(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genre_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        unit TEXT NOT NULL,
        UNIQUE(genre_id, name),
        FOREIGN KEY(genre_id) REFERENCES genres(id) ON DELETE CASCADE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        store_id INTEGER NOT NULL,
        qty REAL NOT NULL,
        total_amount REAL NOT NULL,
        unit_price REAL NOT NULL,
        payment_id INTEGER NOT NULL,
        FOREIGN KEY(item_id) REFERENCES items(id),
        FOREIGN KEY(store_id) REFERENCES stores(id),
        FOREIGN KEY(payment_id) REFERENCES payments(id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS monthly_genre_summary(
        month TEXT NOT NULL,
        genre_id INTEGER NOT NULL,
        total_amount REAL NOT NULL DEFAULT 0,
        PRIMARY KEY(month, genre_id),
        FOREIGN KEY(genre_id) REFERENCES genres(id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS monthly_genre_items(
        month TEXT NOT NULL,
        genre_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        PRIMARY KEY(month, genre_id, item_id),
        FOREIGN KEY(genre_id) REFERENCES genres(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS monthly_payment_summary(
        month TEXT NOT NULL,
        payment_id INTEGER NOT NULL,
        total_amount REAL NOT NULL DEFAULT 0,
        PRIMARY KEY(month, payment_id),
        FOREIGN KEY(payment_id) REFERENCES payments(id)
    );
    """)
    conn.commit()
    conn.close()
    _init_bs_tables()

def seed_minimal():
    conn = get_conn()
    cur = conn.cursor()
    for g in ["Food"]:
        cur.execute("INSERT OR IGNORE INTO genres(name) VALUES (?)", (g,))
    base_items = [
    ]
    for gname, iname, unit in base_items:
        cur.execute("SELECT id FROM genres WHERE name=?", (gname,))
        row = cur.fetchone()
        if row:
            gid = row[0]
            cur.execute("INSERT OR IGNORE INTO items(genre_id, name, unit) VALUES (?, ?, ?)", (gid, iname, unit))
    for s in []:
        cur.execute("INSERT OR IGNORE INTO stores(name) VALUES (?)", (s,))
    for p in []:
        cur.execute("INSERT OR IGNORE INTO payments(name) VALUES (?)", (p,))
    conn.commit()
    conn.close()

def list_genres() -> List[Tuple[int, str]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM genres ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def list_items_by_genre(genre_id: int) -> List[Tuple[int, str, str]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, unit FROM items WHERE genre_id=? ORDER BY name", (genre_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def list_stores() -> List[Tuple[int, str]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM stores ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def list_payments() -> List[Tuple[int, str]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM payments ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def ensure_store(name: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO stores(name) VALUES (?)", (name,))
    conn.commit()
    cur.execute("SELECT id FROM stores WHERE name=?", (name,))
    sid = cur.fetchone()[0]
    conn.close()
    return sid

def ensure_payment(name: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO payments(name) VALUES (?)", (name,))
    conn.commit()
    cur.execute("SELECT id FROM payments WHERE name=?", (name,))
    pid = cur.fetchone()[0]
    conn.close()
    return pid

def ensure_item(genre_id: int, name: str, unit: str) -> int:
    name = name.strip()
    unit = unit.strip()
    if not name or not unit:
        raise ValueError("品目名と単位は必須です。")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO items(genre_id, name, unit) VALUES (?, ?, ?)", (genre_id, name, unit))
    conn.commit()
    cur.execute("SELECT id FROM items WHERE genre_id=? AND name=?", (genre_id, name))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError("品目の作成または取得に失敗しました。")
    return row[0]

def insert_purchase(item_id: int, date_iso: str, store_id: int, qty: float, total: float, payment_id: int):
    if qty <= 0:
        raise ValueError("数量は正の値が必要です。")
    unit_price = total / qty if qty else 0.0
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO purchases(item_id, date, store_id, qty, total_amount, unit_price, payment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (item_id, date_iso, store_id, qty, total, unit_price, payment_id))

    month = date_iso[:7]
    # genre
    cur.execute("SELECT genre_id FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if not row:
        conn.rollback()
        conn.close()
        raise ValueError("不正な品目です。")
    genre_id = row[0]

    # genre monthly summary
    cur.execute("""
        INSERT INTO monthly_genre_summary(month, genre_id, total_amount)
        VALUES (?, ?, ?)
        ON CONFLICT(month, genre_id) DO UPDATE SET total_amount = total_amount + excluded.total_amount
    """, (month, genre_id, total))

    # membership
    cur.execute("""
        INSERT OR IGNORE INTO monthly_genre_items(month, genre_id, item_id)
        VALUES (?, ?, ?)
    """, (month, genre_id, item_id))

    # payment monthly summary
    cur.execute("""
        INSERT INTO monthly_payment_summary(month, payment_id, total_amount)
        VALUES (?, ?, ?)
        ON CONFLICT(month, payment_id) DO UPDATE SET total_amount = total_amount + excluded.total_amount
    """, (month, payment_id, total))

    conn.commit()
    conn.close()

def get_item_unit(item_id: int) -> Optional[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT unit FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_purchase(purchase_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.item_id, i.name, i.unit, i.genre_id, p.date, p.store_id, s.name,
               p.qty, p.total_amount, p.unit_price, p.payment_id, pay.name
        FROM purchases p
        JOIN items i ON p.item_id = i.id
        JOIN stores s ON p.store_id = s.id
        JOIN payments pay ON p.payment_id = pay.id
        WHERE p.id = ?
    """, (purchase_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_purchases_by_genre_item(genre_id: int, item_id: int | None):
    conn = get_conn()
    cur = conn.cursor()
    if item_id:
        cur.execute("""
            SELECT p.id, p.item_id, i.name, i.unit, p.date, p.store_id, s.name,
                   p.qty, p.total_amount, p.unit_price, p.payment_id, pay.name
            FROM purchases p
            JOIN items i ON p.item_id = i.id
            JOIN stores s ON p.store_id = s.id
            JOIN payments pay ON p.payment_id = pay.id
            WHERE i.genre_id = ? AND i.id = ?
            ORDER BY p.date DESC, p.id DESC
        """, (genre_id, item_id))
    else:
        cur.execute("""
            SELECT p.id, p.item_id, i.name, i.unit, p.date, p.store_id, s.name,
                   p.qty, p.total_amount, p.unit_price, p.payment_id, pay.name
            FROM purchases p
            JOIN items i ON p.item_id = i.id
            JOIN stores s ON p.store_id = s.id
            JOIN payments pay ON p.payment_id = pay.id
            WHERE i.genre_id = ?
            ORDER BY p.date DESC, p.id DESC
        """, (genre_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_purchase(purchase_id: int, date_iso: str, store_id: int, qty: float, total: float, payment_id: int):
    """Update a purchase and maintain monthly summaries accordingly (idempotent, atomic)."""
    if qty <= 0:
        raise ValueError("数量は正の値が必要です。")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")

        # 旧値の取得
        cur.execute("""
            SELECT p.item_id, p.date, p.total_amount, p.payment_id
            FROM purchases p WHERE p.id = ?
        """, (purchase_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("対象レコードが見つかりません。")
        item_id, old_date, old_total, old_payment_id = row
        old_month = old_date[:7]
        new_month = date_iso[:7]

        # 品目のジャンル
        cur.execute("SELECT genre_id FROM items WHERE id=?", (item_id,))
        r = cur.fetchone()
        if not r:
            raise ValueError("不正な品目です。")
        genre_id = r[0]

        # 旧・月×ジャンル サマリを減算（0なら削除）
        cur.execute("SELECT total_amount FROM monthly_genre_summary WHERE month=? AND genre_id=?", (old_month, genre_id))
        r = cur.fetchone()
        if r:
            new_total_amt = max(0.0, float(r[0]) - float(old_total))
            if new_total_amt == 0.0:
                cur.execute("DELETE FROM monthly_genre_summary WHERE month=? AND genre_id=?", (old_month, genre_id))
            else:
                cur.execute("UPDATE monthly_genre_summary SET total_amount=? WHERE month=? AND genre_id=?", (new_total_amt, old_month, genre_id))

        # 旧・月×支払い手段 サマリを減算（0なら削除）
        cur.execute("SELECT total_amount FROM monthly_payment_summary WHERE month=? AND payment_id=?", (old_month, old_payment_id))
        r = cur.fetchone()
        if r:
            new_total_amt = max(0.0, float(r[0]) - float(old_total))
            if new_total_amt == 0.0:
                cur.execute("DELETE FROM monthly_payment_summary WHERE month=? AND payment_id=?", (old_month, old_payment_id))
            else:
                cur.execute("UPDATE monthly_payment_summary SET total_amount=? WHERE month=? AND payment_id=?", (new_total_amt, old_month, old_payment_id))

        # 購入レコードの更新
        unit_price = total / qty
        cur.execute("""
            UPDATE purchases
            SET date=?, store_id=?, qty=?, total_amount=?, unit_price=?, payment_id=?
            WHERE id=?
        """, (date_iso, store_id, qty, total, unit_price, payment_id, purchase_id))

        # 新・月×ジャンル サマリを加算（upsert）
        cur.execute("""
            INSERT INTO monthly_genre_summary(month, genre_id, total_amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, genre_id)
            DO UPDATE SET total_amount = total_amount + excluded.total_amount
        """, (new_month, genre_id, total))

        # 新・月×支払い手段 サマリを加算（upsert）
        cur.execute("""
            INSERT INTO monthly_payment_summary(month, payment_id, total_amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, payment_id)
            DO UPDATE SET total_amount = total_amount + excluded.total_amount
        """, (new_month, payment_id, total))

        # membership の整備
        cur.execute("""
            INSERT OR IGNORE INTO monthly_genre_items(month, genre_id, item_id)
            VALUES (?, ?, ?)
        """, (new_month, genre_id, item_id))

        # 月が変わった場合は旧月の membership を掃除
        if old_month != new_month:
            cur.execute("""
                SELECT COUNT(*) FROM purchases WHERE item_id=? AND substr(date,1,7)=?
            """, (item_id, old_month))
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    DELETE FROM monthly_genre_items WHERE month=? AND genre_id=? AND item_id=?
                """, (old_month, genre_id, item_id))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def delete_purchase(purchase_id: int):
    """Delete a purchase and update monthly summaries/memberships (idempotent)."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")

        # 対象行の取得（無ければ冪等に終了）
        cur.execute("""
            SELECT p.item_id, p.date, p.total_amount, p.payment_id
            FROM purchases p
            WHERE p.id = ?
        """, (purchase_id,))
        row = cur.fetchone()
        if not row:
            cur.execute("ROLLBACK")  # 何もしていないが整合
            return

        item_id, date_iso, total, payment_id = row
        month = date_iso[:7]

        # 品目のジャンル取得（無ければ冪等に終了）
        cur.execute("SELECT genre_id FROM items WHERE id=?", (item_id,))
        row = cur.fetchone()
        if not row:
            cur.execute("ROLLBACK")
            return
        genre_id = row[0]

        # 月×ジャンル サマリ減算（0 未満防止＆必要なら0行削除）
        cur.execute("""
            SELECT total_amount FROM monthly_genre_summary
            WHERE month=? AND genre_id=?
        """, (month, genre_id))
        r = cur.fetchone()
        if r:
            new_total = max(0.0, float(r[0]) - float(total))
            if new_total == 0.0:
                # 方針1: 0 行は削除
                cur.execute("""
                    DELETE FROM monthly_genre_summary
                    WHERE month=? AND genre_id=?
                """, (month, genre_id))
            else:
                cur.execute("""
                    UPDATE monthly_genre_summary
                    SET total_amount=?
                    WHERE month=? AND genre_id=?
                """, (new_total, month, genre_id))

        # 月×支払い手段 サマリ減算（同様）
        cur.execute("""
            SELECT total_amount FROM monthly_payment_summary
            WHERE month=? AND payment_id=?
        """, (month, payment_id))
        r = cur.fetchone()
        if r:
            new_total = max(0.0, float(r[0]) - float(total))
            if new_total == 0.0:
                # 方針1: 0 行は削除（方針2として残す場合は UPDATE に置換）
                cur.execute("""
                    DELETE FROM monthly_payment_summary
                    WHERE month=? AND payment_id=?
                """, (month, payment_id))
            else:
                cur.execute("""
                    UPDATE monthly_payment_summary
                    SET total_amount=?
                    WHERE month=? AND payment_id=?
                """, (new_total, month, payment_id))

        # 購入レコード削除
        cur.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))

        # monthly_genre_items の整合
        cur.execute("""
            SELECT COUNT(*)
            FROM purchases
            WHERE item_id=? AND substr(date,1,7)=?
        """, (item_id, month))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                DELETE FROM monthly_genre_items
                WHERE month=? AND genre_id=? AND item_id=?
            """, (month, genre_id, item_id))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_item_unit(item_id: int, new_unit: str):
    new_unit = (new_unit or "").strip()
    if not new_unit:
        raise ValueError("単位は空にできません。")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE items SET unit=? WHERE id=?", (new_unit, item_id))
    conn.commit()
    conn.close()
    
def change_item_genre(item_id: int, new_genre_id: int):
    conn = get_conn()
    cur = conn.cursor()

    # old genre
    cur.execute("SELECT genre_id FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("品目が見つかりません。")
    old_genre = row[0]
    if old_genre == new_genre_id:
        conn.close()
        return

    # For each purchase: transfer monthly totals old->new
    cur.execute("""
        SELECT date, total_amount FROM purchases WHERE item_id=?
    """, (item_id,))
    rows = cur.fetchall()
    # decrement old
    for (date_iso, total) in rows:
        month = date_iso[:7]
        cur.execute("SELECT total_amount FROM monthly_genre_summary WHERE month=? AND genre_id=?", (month, old_genre))
        r = cur.fetchone()
        if r:
            current = r[0]
            cur.execute("UPDATE monthly_genre_summary SET total_amount=? WHERE month=? AND genre_id=?",
                        (max(0.0, current - total), month, old_genre))
        # increment new
        cur.execute("""
            INSERT INTO monthly_genre_summary(month, genre_id, total_amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, genre_id) DO UPDATE SET total_amount = total_amount + excluded.total_amount
        """, (month, new_genre_id, total))
        # membership
        cur.execute("""
            INSERT OR IGNORE INTO monthly_genre_items(month, genre_id, item_id)
            VALUES (?, ?, ?)
        """, (month, new_genre_id, item_id))
        # cleanup old membership if no other purchases remain for old genre in that month for this item
        cur.execute("""
            SELECT COUNT(*) FROM purchases p
            JOIN items i ON p.item_id = i.id
            WHERE p.item_id=? AND substr(p.date,1,7)=? AND i.genre_id=?
        """, (item_id, month, old_genre))
        cnt = cur.fetchone()[0]
        if cnt == 0:
            cur.execute("""
                DELETE FROM monthly_genre_items WHERE month=? AND genre_id=? AND item_id=?
            """, (month, old_genre, item_id))

    # finally update item genre
    cur.execute("UPDATE items SET genre_id=? WHERE id=?", (new_genre_id, item_id))

    conn.commit()
    conn.close()
    
def ensure_genre(name: str) -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("ジャンル名は必須です。")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO genres(name) VALUES (?)", (name,))
    conn.commit()
    cur.execute("SELECT id FROM genres WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError("ジャンルの作成または取得に失敗しました。")
    return row[0]

def get_item_timeseries(item_id: int):
    """Return list of (date_iso, qty, unit_price) ordered by date."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, qty, unit_price
        FROM purchases
        WHERE item_id=?
        ORDER BY date ASC, id ASC
    """, (item_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_item_timeseries_by_store(item_id: int):
    """
    戻り値: [(date_iso, store_name, qty_sum, unit_price_avg), ...] を日付昇順で。
    """
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    SELECT p.date, s.name, SUM(p.qty) AS qty_sum, AVG(p.unit_price) AS unit_price_avg
    FROM purchases p
    JOIN stores s ON s.id = p.store_id
    WHERE p.item_id = ?
    GROUP BY p.date, s.name
    ORDER BY p.date ASC, s.name ASC
    """, (item_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_available_months():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT substr(date,1,7) AS month FROM purchases ORDER BY month ASC
    """)
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def get_month_total(month: str) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(total_amount),0) FROM purchases WHERE substr(date,1,7)=?
    """, (month,))
    row = cur.fetchone()
    conn.close()
    return float(row[0] or 0.0)

def get_monthly_genre_totals(month: str):
    """Return list of (genre_id, genre_name, total_amount) for the month (only >0)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT g.id, g.name, COALESCE(m.total_amount, 0)
        FROM genres g
        LEFT JOIN monthly_genre_summary m
          ON m.genre_id = g.id AND m.month = ?
        WHERE COALESCE(m.total_amount,0) > 0
        ORDER BY m.total_amount DESC, g.id ASC
    """, (month,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_month_genre_item_totals(month: str, genre_id: int):
    """Return list of (item_name, total_amount) for given month & genre, desc by amount."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.name, SUM(p.total_amount) as total
        FROM purchases p
        JOIN items i ON p.item_id = i.id
        WHERE substr(p.date,1,7)=? AND i.genre_id=?
        GROUP BY i.id, i.name
        HAVING total > 0
        ORDER BY total DESC, i.name ASC
    """, (month, genre_id))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_monthly_payment_totals(month: str):
    """Return list of (payment_id, payment_name, total_amount) for the month (>0)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pay.id, pay.name, COALESCE(m.total_amount,0)
        FROM payments pay
        LEFT JOIN monthly_payment_summary m
        ON m.payment_id = pay.id AND m.month = ?
        WHERE COALESCE(m.total_amount,0) > 0
        ORDER BY m.total_amount DESC, pay.id ASC
        """,
        (month,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_item_and_update_summaries(item_id: int):
    """
    品目に紐づく全購入記録を削除し、
    monthly_genre_summary と monthly_payment_summary、monthly_genre_items を整合させた上で items から品目を削除する。
    """
    conn = get_conn()
    cur = conn.cursor()

    # まず品目のジャンルIDを取得
    cur.execute("SELECT genre_id FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("品目が見つかりません。")
    genre_id = row[0]

    # 当該品目の全購入記録を取得
    cur.execute("""
        SELECT id, date, total_amount, payment_id FROM purchases WHERE item_id=?
    """, (item_id,))
    purchases = cur.fetchall()

    # 1件ずつ、集計を減算し purchase を削除
    for pid, date_iso, total, payment_id in purchases:
        month = date_iso[:7]
        # ジャンル別集計の減算
        cur.execute("SELECT total_amount FROM monthly_genre_summary WHERE month=? AND genre_id=?", (month, genre_id))
        r = cur.fetchone()
        if r:
            current = r[0]
            new_total = max(0.0, current - float(total))
            cur.execute("UPDATE monthly_genre_summary SET total_amount=? WHERE month=? AND genre_id=?", (new_total, month, genre_id))
        # 支払い手段別集計の減算
        cur.execute("SELECT total_amount FROM monthly_payment_summary WHERE month=? AND payment_id=?", (month, payment_id))
        r = cur.fetchone()
        if r:
            current = r[0]
            new_total = max(0.0, current - float(total))
            cur.execute("UPDATE monthly_payment_summary SET total_amount=? WHERE month=? AND payment_id=?", (new_total, month, payment_id))
        # 購入レコード削除
        cur.execute("DELETE FROM purchases WHERE id=?", (pid,))

        # monthly_genre_items の整合（当該月にこの品目の購入がもう無いなら削除）
        cur.execute("SELECT COUNT(*) FROM purchases WHERE item_id=? AND substr(date,1,7)=?", (item_id, month))
        cnt = cur.fetchone()[0]
        if cnt == 0:
            cur.execute("DELETE FROM monthly_genre_items WHERE month=? AND genre_id=? AND item_id=?", (month, genre_id, item_id))

    # 最後に items から品目を削除
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))

    conn.commit()
    conn.close()
    
def delete_genre_and_update_summaries(genre_id: int):
    """
    指定ジャンル配下の品目・購入記録を整合をとりながら削除し、最後にジャンルを削除する。
    影響箇所：
      - purchases（削除）
      - monthly_genre_summary（月×ジャンル合計の減算／該当行削除）
      - monthly_payment_summary（月×支払い手段の減算）
      - monthly_genre_items（該当月の品目会員情報の削除）
      - items（削除）→ genres（削除）
    """
    conn = get_conn()
    cur = conn.cursor()

    # 対象ジャンルの存在確認
    cur.execute("SELECT id FROM genres WHERE id=?", (genre_id,))
    if not cur.fetchone():
        conn.close()
        raise ValueError("ジャンルが見つかりません。")

    # このジャンルの品目一覧
    cur.execute("SELECT id FROM items WHERE genre_id=?", (genre_id,))
    item_ids = [r[0] for r in cur.fetchall()]

    # 品目が無ければ：monthly_genre_summaryの行を削除してジャンルを削除
    if not item_ids:
        # monthly_genre_summary のジャンル行を削除（あれば）
        cur.execute("DELETE FROM monthly_genre_summary WHERE genre_id=?", (genre_id,))
        # 最後にジャンル削除
        cur.execute("DELETE FROM genres WHERE id=?", (genre_id,))
        conn.commit()
        conn.close()
        return

    # 各品目の購入記録を走査して集計を減算しつつ削除
    for item_id in item_ids:
        cur.execute("""
            SELECT id, date, total_amount, payment_id
            FROM purchases
            WHERE item_id=?
        """, (item_id,))
        rows = cur.fetchall()
        for pid, date_iso, total, payment_id in rows:
            month = date_iso[:7]

            # 月×ジャンル 合計の減算（0未満にならないように）
            cur.execute("""
                SELECT total_amount
                FROM monthly_genre_summary
                WHERE month=? AND genre_id=?
            """, (month, genre_id))
            r = cur.fetchone()
            if r:
                new_total = max(0.0, float(r[0]) - float(total))
                if new_total == 0.0:
                    cur.execute("""
                        DELETE FROM monthly_genre_summary
                        WHERE month=? AND genre_id=?
                    """, (month, genre_id))
                else:
                    cur.execute("""
                        UPDATE monthly_genre_summary
                        SET total_amount=?
                        WHERE month=? AND genre_id=?
                    """, (new_total, month, genre_id))

            # 月×支払い手段 合計の減算
            cur.execute("""
                SELECT total_amount
                FROM monthly_payment_summary
                WHERE month=? AND payment_id=?
            """, (month, payment_id))
            r = cur.fetchone()
            if r:
                new_total = max(0.0, float(r[0]) - float(total))
                cur.execute("""
                    UPDATE monthly_payment_summary
                    SET total_amount=?
                    WHERE month=? AND payment_id=?
                """, (new_total, month, payment_id))

            # 購入記録を削除
            cur.execute("DELETE FROM purchases WHERE id=?", (pid,))

            # monthly_genre_items の会員情報を整理
            cur.execute("""
                SELECT COUNT(*)
                FROM purchases
                WHERE item_id=? AND substr(date,1,7)=?
            """, (item_id, month))
            cnt = cur.fetchone()[0]
            if cnt == 0:
                cur.execute("""
                    DELETE FROM monthly_genre_items
                    WHERE month=? AND genre_id=? AND item_id=?
                """, (month, genre_id, item_id))

        # 品目を削除
        cur.execute("DELETE FROM items WHERE id=?", (item_id,))

    # 念のため、このジャンルの monthly_genre_summary の残骸を掃除
    cur.execute("DELETE FROM monthly_genre_summary WHERE genre_id=?", (genre_id,))

    # 最後にジャンルそのものを削除
    cur.execute("DELETE FROM genres WHERE id=?", (genre_id,))

    conn.commit()
    conn.close()

# 追加：名称変更
def update_genre_name(genre_id: int, new_name: str):
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("ジャンル名は空にできません。")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE genres SET name=? WHERE id=?", (new_name, genre_id))
    if cur.rowcount == 0:
        conn.close(); raise ValueError("ジャンルが見つかりません。")
    conn.commit(); conn.close()

def update_store_name(store_id: int, new_name: str):
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("店名は空にできません。")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE stores SET name=? WHERE id=?", (new_name, store_id))
    if cur.rowcount == 0:
        conn.close(); raise ValueError("店が見つかりません。")
    conn.commit(); conn.close()

def update_payment_name(payment_id: int, new_name: str):
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("支払い手段名は空にできません。")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE payments SET name=? WHERE id=?", (new_name, payment_id))
    if cur.rowcount == 0:
        conn.close(); raise ValueError("支払い手段が見つかりません。")
    conn.commit(); conn.close()

# 追加：参照件数
def count_purchases_by_store(store_id: int) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM purchases WHERE store_id=?", (store_id,))
    n = cur.fetchone()[0]; conn.close(); return int(n)

def count_purchases_by_payment(payment_id: int) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM purchases WHERE payment_id=?", (payment_id,))
    n = cur.fetchone()[0]; conn.close(); return int(n)

# 追加：店の再割当（集計影響なし）
def reassign_store_in_purchases(old_store_id: int, new_store_id: int):
    if old_store_id == new_store_id:
        return
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE purchases SET store_id=? WHERE store_id=?", (new_store_id, old_store_id))
    conn.commit(); conn.close()

# 追加：支払い手段の再割当（支払月次集計を月別に移し替え）
def reassign_payment_in_purchases(old_payment_id: int, new_payment_id: int):
    if old_payment_id == new_payment_id:
        return
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("BEGIN")

        # 月別に移動額を計算
        cur.execute("""
            SELECT substr(date,1,7) AS month, SUM(total_amount) AS s
            FROM purchases
            WHERE payment_id=?
            GROUP BY substr(date,1,7)
        """, (old_payment_id,))
        rows = cur.fetchall()  # [(month, sum), ...]

        # 旧 payment 側の月次を減算（0なら削除）
        for month, s in rows:
            s = float(s or 0.0)
            cur.execute("SELECT total_amount FROM monthly_payment_summary WHERE month=? AND payment_id=?", (month, old_payment_id))
            r = cur.fetchone()
            if r:
                new_total = max(0.0, float(r[0]) - s)
                if new_total == 0.0:
                    cur.execute("DELETE FROM monthly_payment_summary WHERE month=? AND payment_id=?", (month, old_payment_id))
                else:
                    cur.execute("UPDATE monthly_payment_summary SET total_amount=? WHERE month=? AND payment_id=?", (new_total, month, old_payment_id))

        # 新 payment 側の月次へ加算（upsert）
        for month, s in rows:
            s = float(s or 0.0)
            cur.execute("""
                INSERT INTO monthly_payment_summary(month, payment_id, total_amount)
                VALUES (?, ?, ?)
                ON CONFLICT(month, payment_id)
                DO UPDATE SET total_amount = total_amount + excluded.total_amount
            """, (month, new_payment_id, s))

        # 購入レコードを再割当
        cur.execute("UPDATE purchases SET payment_id=? WHERE payment_id=?", (new_payment_id, old_payment_id))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 追加：安全な削除（参照がない場合のみ）
def delete_store(store_id: int):
    if count_purchases_by_store(store_id) > 0:
        raise ValueError("この店は購入に参照されています。先に再割当してください。")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM stores WHERE id=?", (store_id,))
    conn.commit(); conn.close()

def delete_payment(payment_id: int):
    if count_purchases_by_payment(payment_id) > 0:
        raise ValueError("この支払い手段は購入に参照されています。先に再割当してください。")
    # 月次支払サマリに残骸があれば掃除
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM monthly_payment_summary WHERE payment_id=?", (payment_id,))
    cur.execute("DELETE FROM payments WHERE id=?", (payment_id,))
    conn.commit(); conn.close()
    
def update_item(item_id: int, new_name: str, new_unit: str):
    new_name = (new_name or "").strip()
    new_unit = (new_unit or "").strip()
    if not new_name:
        raise ValueError("品目名は空にできません。")
    if not new_unit:
        raise ValueError("単位は空にできません。")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        # 存在確認
        cur.execute("SELECT genre_id FROM items WHERE id=?", (item_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("品目が見つかりません。")
        # 更新（同一ジャンル・同名の一意制約に当たると IntegrityError）
        cur.execute("UPDATE items SET name=?, unit=? WHERE id=?", (new_name, new_unit, item_id))
        if cur.rowcount == 0:
            raise ValueError("更新対象が見つかりません。")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("同一ジャンルに同名の品目が既に存在します。")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_purchases_filtered(genre_id: int,item_id: int | None,store_id: int | None,start_date_iso: str | None,end_date_iso: str | None):
    """
    返値は既存と同じ並び：
    (p.id, i.id, i.name, i.unit, p.date, s.id, s.name, p.qty, p.total_amount, p.unit_price, pay.id, pay.name)
    """
    conn = get_conn()
    cur = conn.cursor()
    conds = ["i.genre_id = ?"]
    params = [genre_id]

    if item_id:
        conds.append("i.id = ?")
        params.append(item_id)

    if store_id:
        conds.append("p.store_id = ?")
        params.append(store_id)

    if start_date_iso:
        conds.append("p.date >= ?")
        params.append(start_date_iso)

    if end_date_iso:
        conds.append("p.date <= ?")
        params.append(end_date_iso)

    where_sql = " AND ".join(conds)

    cur.execute(f"""
        SELECT p.id, p.item_id, i.name, i.unit, p.date, p.store_id, s.name,
            p.qty, p.total_amount, p.unit_price, p.payment_id, pay.name
        FROM purchases p
        JOIN items i    ON p.item_id = i.id
        JOIN stores s   ON p.store_id = s.id
        JOIN payments pay ON p.payment_id = pay.id
        WHERE {where_sql}
        ORDER BY p.date DESC, p.id DESC
    """, tuple(params))

    rows = cur.fetchall()
    conn.close()
    return rows

# ====== BS: balance snapshots（口座・現金の実測記録） =======================

def _init_bs_tables():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bs_snapshots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,               -- 'YYYY-MM-DD'
        account_balance REAL NOT NULL,
        cash_balance REAL NOT NULL
    );
    """)
    cur.execute("PRAGMA table_info(bs_snapshots);")
    cols = [r[1] for r in cur.fetchall()]
    if "note" not in cols:
        cur.execute("ALTER TABLE bs_snapshots ADD COLUMN note TEXT;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bs_date ON bs_snapshots(date);")
    conn.commit(); conn.close()

# init_db()呼び出し後に実行されるよう、既存のinit_dbの末尾で呼ぶのが安全。
# 既存init_dbの最後に _init_bs_tables() を1行追加してください。

def bs_insert_record(d, account_balance, cash_balance, note=None):
    if hasattr(d, "isoformat"): d = d.isoformat()
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    INSERT INTO bs_snapshots(date, account_balance, cash_balance, note)
    VALUES(?,?,?,?)
    ON CONFLICT(date) DO UPDATE SET
      account_balance=excluded.account_balance,
      cash_balance=excluded.cash_balance,
      note=COALESCE(excluded.note, note)
    """, (d, float(account_balance or 0.0), float(cash_balance or 0.0), note))
    conn.commit()
    cur.execute("SELECT id FROM bs_snapshots WHERE date=?", (d,))
    rid = cur.fetchone()[0]
    conn.close()
    return rid

def bs_update_record(rec_id, d, account_balance, cash_balance, note=None):
    if hasattr(d, "isoformat"): d = d.isoformat()
    conn = get_conn(); cur = conn.cursor()
    if note is None:
        cur.execute("""
          UPDATE bs_snapshots
          SET date=?, account_balance=?, cash_balance=?
          WHERE id=?
        """, (d, float(account_balance or 0.0), float(cash_balance or 0.0), rec_id))
    else:
        cur.execute("""
          UPDATE bs_snapshots
          SET date=?, account_balance=?, cash_balance=?, note=?
          WHERE id=?
        """, (d, float(account_balance or 0.0), float(cash_balance or 0.0), note, rec_id))
    conn.commit(); conn.close()

def bs_delete_record(rec_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM bs_snapshots WHERE id=?", (rec_id,))
    conn.commit(); conn.close()

def bs_list_records(start=None, end=None):
    conn = get_conn(); cur = conn.cursor()
    sql = "SELECT id,date,account_balance,cash_balance,note FROM bs_snapshots"
    conds, params = [], []
    if start:
        s = start.isoformat() if hasattr(start, "isoformat") else str(start)
        conds.append("date>=?"); params.append(s)
    if end:
        e = end.isoformat() if hasattr(end, "isoformat") else str(end)
        conds.append("date<=?"); params.append(e)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY date ASC, id ASC"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return [{"id":r[0], "date":r[1],
             "account_balance":float(r[2]), "cash_balance":float(r[3]),
             "note": (r[4] if r[4] is not None else "")} for r in rows]

def bs_get_latest_record():
    """dict or None: 最も新しい日付の記録"""
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
      SELECT id,date,account_balance,cash_balance
      FROM bs_snapshots
      ORDER BY date DESC, id DESC
      LIMIT 1
    """)
    r = cur.fetchone()
    conn.close()
    if not r: return None
    return {"id":r[0], "date":r[1], "account_balance":float(r[2]), "cash_balance":float(r[3])}

# ====== 理論値差分の算出（基準日以降の家計簿購入から簡易推定） ==============

def _is_cash_payment_name(name: str) -> bool:
    # 必要に応じて語彙を拡張。正規化（全角半角/大小）等も適宜追加可。
    if not name: return False
    nm = str(name).strip().lower()
    return nm in ("現金", "cash")

def get_balance_deltas_since(date_from):
    """
    返値: {"delta_account": float, "delta_cash": float}
    規則:
      ・支払い手段名が '現金' または 'Cash' → 現金を total_amount 分 減算（負の寄与）
      ・それ以外 → 口座を total_amount 分 減算
    """
    if hasattr(date_from, "isoformat"):
        date_from = date_from.isoformat()
    conn = get_conn(); cur = conn.cursor()
    # date_fromより後（基準日を含めない）の支出を集計
    cur.execute("""
      SELECT pay.name, SUM(p.total_amount)
      FROM purchases p
      JOIN payments pay ON pay.id=p.payment_id
      WHERE p.date > ?
      GROUP BY pay.id, pay.name
    """, (date_from,))
    rows = cur.fetchall()
    conn.close()

    delta_acct, delta_cash = 0.0, 0.0
    for pay_name, s in rows:
        amt = float(s or 0.0)
        if _is_cash_payment_name(pay_name):
            delta_cash -= amt
        else:
            delta_acct -= amt

    return {"delta_account": delta_acct, "delta_cash": delta_cash}

def get_balance_deltas_between(prev_date, curr_date):
    pd = prev_date.isoformat() if hasattr(prev_date, "isoformat") else str(prev_date)
    cd = curr_date.isoformat() if hasattr(curr_date, "isoformat") else str(curr_date)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
      SELECT pay.name, SUM(p.total_amount)
      FROM purchases p
      JOIN payments pay ON pay.id=p.payment_id
      WHERE p.date > ? AND p.date <= ?
      GROUP BY pay.id, pay.name
    """, (pd, cd))
    rows = cur.fetchall()
    conn.close()
    delta_acct, delta_cash = 0.0, 0.0
    for pay_name, s in rows:
        amt = float(s or 0.0)
        if _is_cash_payment_name(pay_name):
            delta_cash -= amt
        else:
            delta_acct -= amt
    return {"delta_account": delta_acct, "delta_cash": delta_cash}
