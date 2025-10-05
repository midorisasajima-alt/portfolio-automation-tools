import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db import get_conn, delete_candidate, get_candidate
from msal_auth import get_access_token
from graph_client import create_event_from_candidate

st.set_page_config(page_title="Candidate List", layout="wide")
st.title("Candidate List")

# --- CSS (add once at the top) ---
st.markdown(
    """
<style>
a.btn-jump {
  display:inline-block; padding:6px 10px; border:1px solid #3b82f6;
  border-radius:6px; text-decoration:none;
  font-size:0.9rem;
}
a.btn-jump:hover { background:#eef5ff; }
</style>
""",
    unsafe_allow_html=True,
)

# --- Internal page jump link (?page=...&date=...) ---
from urllib.parse import urlencode

PAGE_NAME = "1_Schedule"  # Match the displayed name of the actual file (e.g., pages/1_Schedule.py)
def _mk_jump(datestr: str) -> str:
    qs = urlencode({"page": PAGE_NAME, "date": datestr})
    href = f"?{qs}"  # No leading slash (safe on deployed subpaths)
    return f'<a href="{href}" class="btn-jump" target="_self">Go to Schedule</a>'

# --- 1) Filter UI ---
today = date.today()
col = st.columns([2, 2, 2, 2, 2])
with col[0]:
    dfrom = st.date_input("Start Date", today)
with col[1]:
    dto = st.date_input("End Date", today + timedelta(days=14))
with col[2]:
    q = st.text_input("Keyword", "")
with col[3]:
    sort_key = st.selectbox("Sort Key", ["date", "start_time", "title"])
with col[4]:
    asc = st.toggle("Ascending", value=True)

if dfrom > dto:
    st.error("Start date exceeds end date.")
    st.stop()

# --- 2) Fetch data (select directly without changing db.py) ---
params = [dfrom.isoformat(), dto.isoformat()]
where = ["date BETWEEN ? AND ?"]
if q.strip():
    where.append("(title LIKE ? OR IFNULL(info_url,'') LIKE ?)")
    like = f"%{q.strip()}%"
    params.extend([like, like])

order = f"ORDER BY {sort_key} {'ASC' if asc else 'DESC'}, id ASC"
sql = f"""
SELECT id, date, title, start_time, end_time, info_url
FROM candidate
WHERE {' AND '.join(where)}
{order}
"""

with get_conn() as conn:
    cur = conn.cursor()
    rows = [dict(r) for r in cur.execute(sql, params).fetchall()]

# --- 3) Shape DataFrame (render once) ---
def _mk_link(u: str | None) -> str:
    if not u:
        return ""
    safe = u.replace('"', "%22")
    return f'<a href="{safe}" target="_blank">link</a>'

df = pd.DataFrame(rows)
if df.empty:
    st.info("No matching candidates found.")
else:
    df["time_span"] = df["start_time"].astype(str) + "–" + df["end_time"].astype(str)
    df["link"] = df["info_url"].apply(_mk_link)

    df_view = df[["id", "date", "time_span", "title", "link"]].rename(
        columns={
            "id": "ID",
            "date": "Date",
            "time_span": "Time",
            "title": "Title",
            "link": "Info",
        }
    )
    st.caption(f"Count: {len(df_view)}")

    # Rightmost column "Action" → jump to Schedule page
    df_view["Action"] = df["date"].apply(_mk_jump)
    df_view = df_view[["ID", "Date", "Time", "Title", "Info", "Action"]]

    st.write(df_view.to_html(escape=False, index=False), unsafe_allow_html=True)

# --- 4) Row actions (single) ---
st.subheader("Row Actions")
aid = st.number_input("Enter target ID", min_value=0, step=1, value=0)
c1, c2 = st.columns([1, 1])

with c1:
    if st.button("Add to Outlook", use_container_width=True, disabled=(aid <= 0)):
        cand = get_candidate(aid)
        if not cand:
            st.error("Target ID not found.")
        else:
            try:
                token = get_access_token()
                res = create_event_from_candidate(
                    token,
                    cand["date"],
                    cand["title"],
                    cand["start_time"],
                    cand["end_time"],
                )
                if res:
                    st.success(
                        f"Created: {res.get('subject')} ({cand['date']} {cand['start_time']}–{cand['end_time']})"
                    )
                    st.toast("Successfully created in Outlook", icon="✅")
            except Exception as e:
                st.error(f"Error while creating: {e}")

with c2:
    if st.button(
        "Move to Trash (Delete)",
        type="secondary",
        use_container_width=True,
        disabled=(aid <= 0),
    ):
        cnt = delete_candidate(aid)
        if cnt == 1:
            st.success(f"Moved ID {aid} to Trash.")
            st.toast("Deleted (moved to Trash)", icon="🗑️")
            st.rerun()
        else:
            st.warning("Target ID not found.")

# --- 5) Bulk operations (optional) ---
st.subheader("Bulk Operations (Optional)")
ids_str = st.text_input("Comma-separated IDs (e.g., 12,13,20)", "")
b1, b2 = st.columns([1, 1])

def _parse_ids(s: str) -> list[int]:
    if not s.strip():
        return []
    out = []
    for t in s.split(","):
        t = t.strip()
        if t.isdigit():
            out.append(int(t))
    return out

with b1:
    if st.button("Create in Outlook (Bulk)", disabled=(not ids_str.strip())):
        token = get_access_token()
        ok, ng = 0, 0
        for cid in _parse_ids(ids_str):
            cand = get_candidate(cid)
            if not cand:
                ng += 1
                continue
            try:
                res = create_event_from_candidate(
                    token,
                    cand["date"],
                    cand["title"],
                    cand["start_time"],
                    cand["end_time"],
                )
                ok += 1 if res else 0
            except Exception:
                ng += 1
        st.info(f"Creation  Success: {ok}  Failure: {ng}")

with b2:
    if st.button("Move to Trash (Bulk)", type="secondary", disabled=(not ids_str.strip())):
        ok, ng = 0, 0
        ids = _parse_ids(ids_str)
        for cid in ids:
            ok += delete_candidate(cid)
        ng = len(ids) - ok
        st.info(f"Delete  Success: {ok}  Failure: {ng}")
        st.rerun()
