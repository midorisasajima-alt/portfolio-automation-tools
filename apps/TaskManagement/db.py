from __future__ import annotations
import sqlite3
from typing import Optional, Iterable, List, Dict, Any

DB_PATH = "tasks.db"

# ---- Status constants ----
STATUS_ACTIVE   = "active"    # アクティブ（一日一回巡回）
STATUS_INACTIVE = "inactive"  # 非アクティブ（今は時間ない）
STATUS_WAITING  = "waiting"   # 待ち（今はやらない）
STATUS_DONE     = "done"      # 完了
VALID_STATUSES = [STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, STATUS_DONE]

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # tasks
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        importance INTEGER NOT NULL,
        urgency INTEGER NOT NULL,
        category TEXT NOT NULL,
        url TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        completed_at TEXT
    );
    """)
    # daily_tasks
    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        task_id INTEGER,
        title TEXT,
        notes TEXT,
        url TEXT,
        done INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    );
    """)
    conn.commit()
    migrate_legacy(conn)

def migrate_legacy(conn: sqlite3.Connection):
    """既存DB（completed列など）を安全に4状態へ移行"""
    cur = conn.cursor()
    # 旧テーブルにstatus列が無ければ追加
    cur.execute("PRAGMA table_info(tasks);")
    cols = [r[1] for r in cur.fetchall()]
    if "status" not in cols:
        cur.execute("ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'active';")
    # 旧completed列があれば、値からstatusを補正
    if "completed" in cols:
        cur.execute("UPDATE tasks SET status='done', completed_at=COALESCE(completed_at, datetime('now')) WHERE completed=1;")
        cur.execute("UPDATE tasks SET status='active' WHERE completed=0 AND (status IS NULL OR status='');")
    conn.commit()

def add_task(title: str, importance: int, urgency: int, category: str, url: Optional[str]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, importance, urgency, category, url, status) VALUES (?, ?, ?, ?, ?, ?)",
        (title, int(importance), int(urgency), category, url, STATUS_ACTIVE)
    )
    conn.commit()
    return cur.lastrowid

def update_task(task_id: int, title: str, importance: int, urgency: int, category: str, url: Optional[str]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title=?, importance=?, urgency=?, category=?, url=? WHERE id=?",
        (title, int(importance), int(urgency), category, url, int(task_id))
    )
    conn.commit()

def set_task_status(task_id: int, status: str):
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    conn = get_conn()
    cur = conn.cursor()
    if status == STATUS_DONE:
        cur.execute("UPDATE tasks SET status=?, completed_at=datetime('now') WHERE id=?", (status, int(task_id)))
    else:
        cur.execute("UPDATE tasks SET status=?, completed_at=NULL WHERE id=?", (status, int(task_id)))
    conn.commit()

def delete_task(task_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_tasks WHERE task_id=?", (int(task_id),))
    cur.execute("DELETE FROM tasks WHERE id=?", (int(task_id),))
    conn.commit()

def get_task(task_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    return cur.execute("SELECT * FROM tasks WHERE id=?", (int(task_id),)).fetchone()

def list_tasks(search_title: Optional[str]=None,
               date_str: Optional[str]=None,
               status: Optional[Iterable[str]]=None) -> list[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if search_title:
        q += " AND title LIKE ?"
        params.append(f"%{search_title}%")
    if date_str:
        # created_atは日時。日付で範囲抽出
        q += " AND date(created_at)=?"
        params.append(date_str)
    if status is not None:
        codes = list(status) if isinstance(status, (list, tuple, set)) else [status]
        placeholders = ",".join(["?"]*len(codes))
        q += f" AND status IN ({placeholders})"
        params.extend(codes)
    q += " ORDER BY CASE status WHEN 'done' THEN 1 ELSE 0 END, datetime(created_at) DESC, id DESC"
    return list(cur.execute(q, params).fetchall())

def list_recent_done(limit: int=20) -> list[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    return list(cur.execute(
        "SELECT * FROM tasks WHERE status='done' ORDER BY datetime(completed_at) DESC LIMIT ?", (int(limit),)
    ).fetchall())

def all_categories() -> list[str]:
    conn = get_conn()
    cur = conn.cursor()
    return [r["category"] for r in cur.execute("SELECT DISTINCT category FROM tasks ORDER BY category").fetchall()]

# --- Daily ---
def add_daily_task(date_str: str, task_id: Optional[int], title: Optional[str], notes: Optional[str], url: Optional[str]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO daily_tasks (date, task_id, title, notes, url) VALUES (?, ?, ?, ?, ?)",
        (date_str, task_id, title, notes, url)
    )
    conn.commit()
    return cur.lastrowid

def list_daily_tasks(date_str: str) -> list[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    return list(cur.execute(
        "SELECT * FROM daily_tasks WHERE date=? ORDER BY done ASC, id DESC", (date_str,)
    ).fetchall())

def set_daily_done_and_sync_task(daily_id: int, done: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE daily_tasks SET done=? WHERE id=?", (1 if done else 0, int(daily_id)))
    # 同期対象
    cur.execute("SELECT task_id FROM daily_tasks WHERE id=?", (int(daily_id),))
    row = cur.fetchone()
    if row and row[0]:
        tid = int(row[0])
        # done -> task=done, reopen -> task=active（運用簡略化）
        if done:
            cur.execute("UPDATE tasks SET status='done', completed_at=COALESCE(completed_at, datetime('now')) WHERE id=?", (tid,))
        else:
            cur.execute("UPDATE tasks SET status='active', completed_at=NULL WHERE id=?", (tid,))
    conn.commit()
