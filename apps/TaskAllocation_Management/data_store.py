
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import uuid

DB_PATH = os.environ.get("TASK_DB_PATH", "data/tasks.json")

STATUS_ORDER = {"アクティブ": 0, "非アクティブ": 1, "待ち": 2, "完了": 3}
ALL_STATUSES = list(STATUS_ORDER.keys())

SIX_MINISTRIES = ["吏", "戸", "礼", "兵", "刑", "工"]
ALL_OWNERS = ["王"] + SIX_MINISTRIES + ["百司", "御史台"]

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ensure_db():
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        empty = {
            "王": [],
            "六部": {k: [] for k in SIX_MINISTRIES},
            "百司": [],
            "御史台": []
        }
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)

def load_db() -> Dict[str, Any]:
    ensure_db()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db: Dict[str, Any]):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def make_task(name: str, memo: str = "", url: str = "", status: str = "アクティブ") -> Dict[str, Any]:
    if status not in STATUS_ORDER:
        status = "アクティブ"
    now = _now()
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "memo": memo,
        "url": url,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "est_hours": None,
        "actual_hours": None
    }

def get_collection(db: Dict[str, Any], owner: str):
    if owner == "王":
        return db["王"]
    elif owner in SIX_MINISTRIES:
        return db["六部"][owner]
    elif owner == "百司":
        return db["百司"]
    elif owner == "御史台":
        return db["御史台"]
    else:
        raise ValueError(f"未知のオーナー: {owner}")

def list_tasks(owner: str) -> List[Dict[str, Any]]:
    db = load_db()
    col = get_collection(db, owner)
    return sorted(col, key=lambda t: (STATUS_ORDER.get(t.get("status", "アクティブ"), 99), t.get("name","")))

def add_task(owner: str, name: str, memo: str = "", url: str = "", status: str = "アクティブ") -> Dict[str, Any]:
    db = load_db()
    task = make_task(name, memo, url, status)
    get_collection(db, owner).append(task)
    save_db(db)
    return task

def update_task(owner: str, task_id: str, **fields):
    db = load_db()
    col = get_collection(db, owner)
    for t in col:
        if t["id"] == task_id:
            t.update({k: v for k, v in fields.items()})
            t["updated_at"] = _now()
            save_db(db)
            return t
    raise KeyError(f"タスクが見つかりません: {task_id}")

def delete_task(owner: str, task_id: str) -> bool:
    db = load_db()
    col = get_collection(db, owner)
    n0 = len(col)
    col[:] = [t for t in col if t["id"] != task_id]
    save_db(db)
    return len(col) < n0

def count_active(owner: str) -> int:
    return sum(1 for t in list_tasks(owner) if t.get("status") == "アクティブ")

def children_of(owner: str):
    if owner == "王":
        return SIX_MINISTRIES
    if owner in SIX_MINISTRIES:
        return ["百司"]
    if owner == "百司":
        return ["御史台"]
    if owner == "御史台":
        return ["王"]
    return []

def propagate(owner: str, task: Dict[str, Any]):
    update_task(owner, task["id"], status="完了")
    ts_memo = f"[{_now()}] " + (task.get("memo") or "")
    for child in children_of(owner):
        add_task(child, name=task["name"], memo=ts_memo, url=task.get("url",""), status="アクティブ")
