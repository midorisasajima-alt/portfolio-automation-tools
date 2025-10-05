import streamlit as st
from db import get_candidate, update_candidate, delete_candidate

st.title("4) Edit / Delete Candidate")

# ── Retrieve ID (from session → query string as fallback) ──
def _get_cid() -> int | None:
    cid = st.session_state.get("edit_id")
    if cid is not None:
        try:
            return int(cid)
        except Exception:
            return None
    # Query string (new API → old API fallback)
    try:
        v = st.query_params.get("id")
        if isinstance(v, list):
            v = v[0]
    except Exception:
        qp = st.experimental_get_query_params()
        v = (qp.get("id", [None]) or [None])[0]
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

cid = _get_cid()
if cid is None:
    st.warning("Candidate ID not found. Please access this page from (2) Candidates.")
    st.stop()

# ── Retrieve record ──
c = get_candidate(cid)
if not c:
    st.error(f"Candidate not found (id={cid}).")
    st.stop()

# ── Edit form ──
with st.form("cand_edit"):
    title = st.text_input("Title", c.get("title", ""))
    date_s = st.text_input("Date (YYYY-MM-DD)", c.get("date", ""))
    start = st.text_input("Start Time (HH:MM)", c.get("start_time", ""))
    end   = st.text_input("End Time (HH:MM)", c.get("end_time", ""))
    info  = st.text_input("Information (Link)", c.get("info_url", ""))

    col1, col2 = st.columns(2)
    saved   = col1.form_submit_button("Save")
    removed = col2.form_submit_button("Delete")

if saved:
    update_candidate(cid, date_s, title, start, end, info)
    st.success("Saved successfully.")

if removed:
    delete_candidate(cid)
    st.success("Deleted successfully.")
    # Clear reference in session (for navigation consistency)
    st.session_state.pop("edit_id", None)
