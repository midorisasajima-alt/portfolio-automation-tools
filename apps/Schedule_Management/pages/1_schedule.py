import streamlit as st
from datetime import date
from pathlib import Path
from msal_auth import get_access_token
from graph_client import list_events
from db import get_event_meta_by_date, upsert_event_meta
from utils import graph_dt_to_london, fmt_ymdhm

st.title("1) Schedule (Outlook + Meta Information)")

col_d, col_u = st.columns([1,1])
with col_d:
    d = st.date_input("Date", value=date.today(), format="YYYY-MM-DD")

if "auth_skip" in st.session_state and st.session_state["auth_skip"]:
    st.info("Demo mode: Outlook authentication is skipped.")
    events = []
else:
    token = get_access_token()
    events = list_events(token, d.isoformat())

meta_list = get_event_meta_by_date(d.isoformat())
meta_map = {(m["event_id"], m["event_date"]): m for m in meta_list}

st.subheader(f"Schedule for {d.isoformat()}")
for ev in events:
    ev_id = ev.get("id")
    subj = ev.get("subject") or "(No title)"
    st_dt = graph_dt_to_london(ev.get("start"))
    en_dt = graph_dt_to_london(ev.get("end"))
    with st.expander(f"🟦 {subj} | {fmt_ymdhm(st_dt)} → {fmt_ymdhm(en_dt)}"):
        key = (ev_id, d.isoformat())
        exist = meta_map.get(key, {})
        info_url = st.text_input("Information (Link)", value=exist.get("info_url", ""), key=f"info_{ev_id}")
        proof = st.file_uploader("Evidence (Screenshot, etc.)", type=["png", "jpg", "jpeg", "pdf"], key=f"proof_{ev_id}")
        saved_path = exist.get("proof_path", "")
        if proof is not None:
            up_dir = Path("uploads"); up_dir.mkdir(exist_ok=True)
            save_to = up_dir / f"proof_{ev_id}_{proof.name}"
            with open(save_to, "wb") as f:
                f.write(proof.getbuffer())
            saved_path = str(save_to)
        if st.button("Save", key=f"save_{ev_id}"):
            upsert_event_meta(ev_id, d.isoformat(), info_url, saved_path or None)
            st.success("Saved successfully.")
        if saved_path:
            st.caption(f"Saved file: {saved_path}")
