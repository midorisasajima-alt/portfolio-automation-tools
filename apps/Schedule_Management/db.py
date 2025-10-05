import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("data.sqlite3")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        # イベントに紐づくメタ情報（情報リンク・根拠ファイルパス）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS event_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                event_date TEXT NOT NULL,
                info_url TEXT,
                proof_path TEXT
            );
            """
        )
        # 候補（ドラフト予定）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                info_url TEXT
            );
            """
        )
        # 最近削除（候補のゴミ箱）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_trash (
                id INTEGER PRIMARY KEY,
                date TEXT,
                title TEXT,
                start_time TEXT,
                end_time TEXT,
                info_url TEXT,
                deleted_at TEXT
            );
            """
        )
        # 体（能率）スケジュール
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS efficiency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                efficiency REAL NOT NULL,
                repeat INTEGER NOT NULL DEFAULT 0, -- 0 once, 1 repeat
                interval_days INTEGER -- 周期（日）
            );
            """
        )
        # 生活時間（定期ルーチン）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS routine (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                hours REAL NOT NULL,
                period_days INTEGER NOT NULL
            );
            """
        )
        # 課題
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                due_time TEXT NOT NULL,
                required_hours REAL NOT NULL,
                info_url TEXT,
                progress REAL NOT NULL DEFAULT 0 -- 0.0-1.0
            );
            """
        )
        # 完了証拠（アップロードパスなど）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS task_proof (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                proof_path TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES task(id)
            );
            """
        )

# クエリ関数（候補）

def insert_candidate(date, title, start_time, end_time, info_url):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO candidate(date, title, start_time, end_time, info_url) VALUES (?,?,?,?,?)",
            (date, title, start_time, end_time, info_url)
        )
        return cur.lastrowid

def list_candidates_by_date(date):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM candidate WHERE date = ? ORDER BY start_time ASC",
            (date,)
        )
        return [dict(r) for r in cur.fetchall()]

def get_candidate(cid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate WHERE id = ?", (cid,))
        r = cur.fetchone()
        return dict(r) if r else None

def update_candidate(cid, date, title, start_time, end_time, info_url):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE candidate
            SET date=?, title=?, start_time=?, end_time=?, info_url=?
            WHERE id=?
            """,
            (date, title, start_time, end_time, info_url, cid)
        )
        return cur.rowcount

def delete_candidate(cid):
    # ゴミ箱へ移動
    import datetime as dt
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate WHERE id = ?", (cid,))
        r = cur.fetchone()
        if not r:
            return 0
        r = dict(r)
        cur.execute(
            "INSERT INTO candidate_trash(id, date, title, start_time, end_time, info_url, deleted_at) VALUES (?,?,?,?,?,?,?)",
            (r["id"], r["date"], r["title"], r["start_time"], r["end_time"], r["info_url"], dt.datetime.utcnow().isoformat())
        )
        cur.execute("DELETE FROM candidate WHERE id = ?", (cid,))
        return 1

def list_trash(limit=50):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate_trash ORDER BY deleted_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def restore_from_trash(cid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate_trash WHERE id = ?", (cid,))
        r = cur.fetchone()
        if not r:
            return 0
        r = dict(r)
        cur.execute(
            "INSERT INTO candidate(id, date, title, start_time, end_time, info_url) VALUES (?,?,?,?,?,?)",
            (r["id"], r["date"], r["title"], r["start_time"], r["end_time"], r["info_url"])
        )
        cur.execute("DELETE FROM candidate_trash WHERE id = ?", (cid,))
        return 1

# メタ情報（イベント紐づけ）

def upsert_event_meta(event_id, event_date, info_url=None, proof_path=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM event_meta WHERE event_id=? AND event_date=?", (event_id, event_date))
        r = cur.fetchone()
        if r:
            cur.execute(
                "UPDATE event_meta SET info_url=?, proof_path=? WHERE id=?",
                (info_url, proof_path, r[0])
            )
        else:
            cur.execute(
                "INSERT INTO event_meta(event_id, event_date, info_url, proof_path) VALUES (?,?,?,?)",
                (event_id, event_date, info_url, proof_path)
            )
        return True

def get_event_meta_by_date(event_date):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM event_meta WHERE event_date = ?", (event_date,))
        return [dict(r) for r in cur.fetchall()]

# 課題系

def insert_task(title, due_date, due_time, required_hours, info_url, progress=0.0):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO task(title, due_date, due_time, required_hours, info_url, progress) VALUES (?,?,?,?,?,?)",
            (title, due_date, due_time, required_hours, info_url, progress)
        )
        return cur.lastrowid

def list_tasks(active=True):
    """
    active=True  : 未完了（proofが無い）を表示。progressは無視。
    active=False : 完了（proofがある）を表示。progressは無視。
    戻り値は両方とも completed_at を列に含む（未完了側は None）。
    """
    with get_conn() as conn:
        cur = conn.cursor()
        if active:
            # 未完了＝ task_proof が存在しない
            cur.execute(
                """
                SELECT
                    t.*,
                    NULL AS completed_at
                FROM task AS t
                WHERE NOT EXISTS (
                    SELECT 1 FROM task_proof AS p
                    WHERE p.task_id = t.id
                )
                ORDER BY t.due_date ASC, t.due_time ASC, t.id ASC
                """
            )
        else:
            # 完了＝ task_proof が1件以上ある（最新completed_atでソート）
            cur.execute(
                """
                SELECT
                    t.*,
                    (
                        SELECT MAX(p.completed_at)
                        FROM task_proof AS p
                        WHERE p.task_id = t.id
                    ) AS completed_at
                FROM task AS t
                WHERE EXISTS (
                    SELECT 1 FROM task_proof AS p
                    WHERE p.task_id = t.id
                )
                ORDER BY completed_at DESC, t.id DESC
                """
            )
        return [dict(r) for r in cur.fetchall()]

def get_task(tid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM task WHERE id = ?", (tid,))
        r = cur.fetchone()
        return dict(r) if r else None

def update_task(tid, title, due_date, due_time, required_hours, info_url, progress):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE task SET title=?, due_date=?, due_time=?, required_hours=?, info_url=?, progress=?
            WHERE id=?
            """,
            (title, due_date, due_time, required_hours, info_url, progress, tid)
        )
        return cur.rowcount

def delete_task(tid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM task WHERE id=?", (tid,))
        return cur.rowcount

def insert_task_proof(task_id: int, file_path: str, uploaded_iso: str):
    cols = _get_columns("task_proof")
    path_candidates = ["path", "file_path", "filepath", "proof_path", "uri"]
    path_col = next((c for c in path_candidates if c in cols), None)

    # ★ ここを修正：completed_at を候補に含める
    ts_candidates = ["uploaded_at", "created_at", "created", "timestamp", "completed_at"]
    ts_col = next((c for c in ts_candidates if c in cols), None)

    if not path_col:
        raise RuntimeError("task_proof テーブルにパス列（path/file_path 等）が見つかりません。")

    if not ts_col:
        # ★ ここは「タイムスタンプ列が存在しない」場合のみ通る。
        #   現在のスキーマには completed_at が NOT NULL で存在するため、通常は通らない。
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO task_proof(task_id, {path_col}) VALUES (?, ?)",
                (task_id, file_path),
            )
            return cur.lastrowid

    # ★ タイムスタンプ列あり（completed_at を含む）→ その列へ uploaded_iso を入れる
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO task_proof(task_id, {path_col}, {ts_col}) VALUES (?, ?, ?)",
            (task_id, file_path, uploaded_iso),
        )
        return cur.lastrowid

# 体（能率）・生活

def insert_efficiency(start_date, end_date, efficiency, repeat, interval_days):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO efficiency(start_date, end_date, efficiency, repeat, interval_days) VALUES (?,?,?,?,?)",
            (start_date, end_date, efficiency, repeat, interval_days)
        )
        return cur.lastrowid

def list_efficiency():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM efficiency ORDER BY start_date DESC")
        return [dict(r) for r in cur.fetchall()]

def insert_routine(title, hours, period_days):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO routine(title, hours, period_days) VALUES (?,?,?)", (title, hours, period_days))
        return cur.lastrowid

def update_efficiency(eff_id, start_date, end_date, efficiency, repeat, interval_days):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE efficiency
               SET start_date = ?, end_date = ?, efficiency = ?,
                   repeat = ?, interval_days = ?
             WHERE id = ?
            """,
            (start_date, end_date, efficiency, repeat, interval_days, eff_id),
        )
        return cur.rowcount  # 1 が期待値

def delete_efficiency(eff_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM efficiency WHERE id = ?", (eff_id,))
        return cur.rowcount  # 1 が期待値


def list_routine():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM routine ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

def update_routine(rid, title, hours, period_days):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE routine SET title=?, hours=?, period_days=? WHERE id=?", (title, hours, period_days, rid))
        return cur.rowcount

def delete_routine(rid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM routine WHERE id=?", (rid,))
        return cur.rowcount
def list_task_proofs(task_id: int):
    cols = _get_columns("task_proof")
    path_candidates = ["path", "file_path", "filepath", "proof_path", "uri"]
    path_col = next((c for c in path_candidates if c in cols), None)

    # ★ ここを修正：completed_at を候補に含める
    ts_candidates = ["uploaded_at", "created_at", "created", "timestamp", "completed_at"]
    ts_col = next((c for c in ts_candidates if c in cols), None)

    select_cols = ["id", "task_id"]
    select_cols.append(f"{path_col} AS path" if path_col else "NULL AS path")
    select_cols.append(f"{ts_col} AS uploaded_at" if ts_col else "NULL AS uploaded_at")

    sql = f"SELECT {', '.join(select_cols)} FROM task_proof WHERE task_id = ? ORDER BY {ts_col or 'id'} DESC"

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, (task_id,))
        return [dict(r) for r in cur.fetchall()]

def _get_columns(table: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cur.fetchall()}  # {colname, ...}

# =============================
# msal_auth.py（Microsoft サインイン）
# -----------------------------
import os
import streamlit as st
import msal

AUTHORITY = f"https://login.microsoftonline.com/{st.secrets.get('AZURE_TENANT_ID', os.environ.get('AZURE_TENANT_ID','common'))}"
CLIENT_ID = st.secrets.get('AZURE_CLIENT_ID', os.environ.get('AZURE_CLIENT_ID',''))
CLIENT_SECRET = st.secrets.get('AZURE_CLIENT_SECRET', os.environ.get('AZURE_CLIENT_SECRET',''))
SCOPES = ["User.Read", "Calendars.ReadWrite", "offline_access"]
REDIRECT_URI = st.secrets.get('REDIRECT_URI', os.environ.get('REDIRECT_URI','http://localhost:8501/'))


def _app():
    return msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET or None
    )


def get_access_token():
    if "token" in st.session_state and st.session_state["token"].get("access_token"):
        return st.session_state["token"]["access_token"]

    code = st.query_params.get("code", [None])[0]
    cca = _app()
    if not code:
        auth_url = cca.get_authorization_request_url(scopes=SCOPES, redirect_uri=REDIRECT_URI, prompt="select_account")
        st.link_button("Sign in with Microsoft", auth_url)
        st.stop()
    result = cca.acquire_token_by_authorization_code(code=code, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    if "access_token" not in result:
        st.error(f"Auth error: {result.get('error_description')}")
        st.stop()
    st.session_state["token"] = result
    return result["access_token"]

# =============================
# graph_client.py（Outlook カレンダーAPI）
# -----------------------------
import requests
import streamlit as st
from datetime import datetime, timedelta

GRAPH = "https://graph.microsoft.com/v1.0"


def list_events(access_token, date_iso: str):
    """指定日のイベントを取得（ローカル日付の 00:00〜23:59）"""
    dt = datetime.fromisoformat(date_iso)
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end = (dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()

    params = {
        "$orderby": "start/dateTime",
        "$top": 50,
        "$filter": None,
        # 期間指定のクエリは calendarView を使用
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    r = requests.get(
        f"{GRAPH}/me/calendarview?startdatetime={start}Z&enddatetime={end}Z",
        headers=headers,
        params=params,
    )
    if r.status_code != 200:
        st.warning(f"Graph list_events error: {r.status_code} {r.text}")
        return []
    return r.json().get("value", [])


def create_event_from_candidate(access_token, date, title, start_time, end_time):
    body = {
        "subject": title,
        "start": {"dateTime": f"{date}T{start_time}", "timeZone": "Europe/London"},
        "end":   {"dateTime": f"{date}T{end_time}",   "timeZone": "Europe/London"},
    }
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    r = requests.post(f"{GRAPH}/me/events", headers=headers, json=body)
    if r.status_code not in (200, 201):
        st.error(f"Create event failed: {r.status_code} {r.text}")
        return None
    return r.json()

from datetime import date, datetime

def today_iso():
    return date.today().isoformat()


def hhmm_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h)*60 + int(m)

# ----- ゴミ箱（候補） -----

def list_trash(limit_days: int | None = 30, limit_rows: int | None = 200):
    """candidate_trash から最近削除を取得。期間・件数で絞り込み。"""
    with get_conn() as conn:
        cur = conn.cursor()
        sql = """
            SELECT id, title, date, start_time, end_time, info_url, deleted_at
              FROM candidate_trash
        """
        params = []
        where = []
        if limit_days is not None:
            where.append("deleted_at >= datetime('now', ?)")
            params.append(f"-{limit_days} days")
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY deleted_at DESC"
        if limit_rows is not None:
            sql += " LIMIT ?"
            params.append(limit_rows)
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

def restore_from_trash(item_id: int, *, restore_table: str = "candidates"):
    """
    candidate_trash から元テーブルへ復元。
    既定では candidates(id, title, date, start_time, end_time, info_url) へ挿入。
    """
    with get_conn() as conn:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT id, title, date, start_time, end_time, info_url FROM candidate_trash WHERE id = ?",
            (item_id,)
        ).fetchone()
        if not row:
            return 0
        r = dict(row)

        # 復元先スキーマに合わせて列を調整（必要なら try/except で存在確認を追加）
        cur.execute(
            f"""
            INSERT OR REPLACE INTO {restore_table}
                (id, title, date, start_time, end_time, info_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (r["id"], r["title"], r["date"], r["start_time"], r["end_time"], r["info_url"])
        )
        cur.execute("DELETE FROM candidate_trash WHERE id = ?", (item_id,))
        return cur.rowcount
    
def delete_from_trash(item_id: int) -> int:
    """candidate_trash から当該行を完全削除（復元不可）。戻り値は削除件数。"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM candidate_trash WHERE id = ?", (item_id,))
        return cur.rowcount



