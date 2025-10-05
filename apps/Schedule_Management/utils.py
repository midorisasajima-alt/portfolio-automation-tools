# utils.py に追加/置換
from datetime import datetime
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")

WINDOWS_TZ_TO_IANA = {
    "GMT Standard Time": "Europe/London",
    "UTC": "UTC",
    # 必要に応じて追加
}

def _to_iana(tz_name: str | None) -> str:
    if not tz_name:
        return "UTC"
    if tz_name in WINDOWS_TZ_TO_IANA:
        return WINDOWS_TZ_TO_IANA[tz_name]
    # 既に IANA 形式（Europe/…）ならそのまま
    return tz_name

def graph_dt_to_london(dt_dict_or_str) -> datetime | None:
    """
    Graph の {'dateTime': '...', 'timeZone': '...'} あるいは dateTime 文字列を
    ロンドン時間の datetime に変換。
    - timeZone が Windows 名でも正しく解釈。
    - 'Z'（UTC）やオフセット付きも考慮。
    """
    if isinstance(dt_dict_or_str, dict):
        dt_str = (dt_dict_or_str or {}).get("dateTime")
        tz_hint = (dt_dict_or_str or {}).get("timeZone")
    else:
        dt_str = dt_dict_or_str
        tz_hint = None

    if not dt_str:
        return None

    # 1) 'Z' or 明示UTC
    if dt_str.endswith("Z") or (tz_hint and tz_hint.upper() == "UTC"):
        dt_utc = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=UTC)
        return dt_utc.astimezone(LONDON)

    # 2) tz_hint がある（Windows/IANA） → そのゾーンとして解釈
    if tz_hint:
        zone = ZoneInfo(_to_iana(tz_hint))
        dt_any = datetime.fromisoformat(dt_str)
        if dt_any.tzinfo is None:
            dt_any = dt_any.replace(tzinfo=zone)
        else:
            dt_any = dt_any.astimezone(zone)
        return dt_any.astimezone(LONDON)

    # 3) tz_hint なし：オフセット付きならそれを尊重、無ければ London とみなす
    dt_any = datetime.fromisoformat(dt_str)
    if dt_any.tzinfo is None:
        dt_any = dt_any.replace(tzinfo=LONDON)
    return dt_any.astimezone(LONDON)

def fmt_ymdhm(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "-"
