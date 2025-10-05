# graph_client.py の list_events を置換
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

GRAPH = "https://graph.microsoft.com/v1.0"
LONDON = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")

def list_events(access_token, date_iso: str):
    # 指定日の 00:00〜24:00（ロンドン時刻）を UTC に変換してクエリ
    d = datetime.fromisoformat(date_iso).replace(tzinfo=LONDON)
    start_utc = d.astimezone(UTC).isoformat().replace("+00:00", "Z")
    end_utc = (d + timedelta(days=1)).astimezone(UTC).isoformat().replace("+00:00", "Z")

    headers = {
        "Authorization": f"Bearer {access_token}",
        'Prefer': 'outlook.timezone="Europe/London"',  # ← レスポンスも London で返させる
    }
    r = requests.get(
        f"{GRAPH}/me/calendarview",
        headers=headers,
        params={
            "startdatetime": start_utc,
            "enddatetime": end_utc,
            "$orderby": "start/dateTime",
            "$top": 50,
        },
    )
    if r.status_code != 200:
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
        return None
    return r.json()
