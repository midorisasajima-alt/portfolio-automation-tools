from __future__ import annotations
import streamlit as st, datetime
from db import add_daily_task, list_tasks, STATUS_ACTIVE

st.set_page_config(page_title="Add Daily Task", layout="centered")
st.title("Add Daily Task")

date = st.date_input("Date", value=datetime.date.today())
date_str = date.strftime("%Y-%m-%d")

mode = st.radio("Add mode", ["Link to existing task", "Free input (standalone daily)"], horizontal=True)

if mode == "Link to existing task":
    tasks = list_tasks(status=STATUS_ACTIVE)
    if not tasks:
        st.info("No active tasks available.")
    else:
        options = {
            f"{t['title']} (Importance: {t['importance']}  Urgency: {t['urgency']} | {t['category']})": t["id"]
            for t in tasks
        }
        label = st.selectbox("Select a task", options=list(options.keys()))
        notes = st.text_area("Notes (optional)", placeholder="e.g., specific actions for today")
        if st.button("Add"):
            add_daily_task(
                date_str,
                task_id=int(options[label]),
                title=None,
                notes=notes.strip() if notes else None,
                url=None
            )
            st.success("Task added successfully.")
else:
    title = st.text_input("Title", placeholder="e.g., 30-minute jogging")
    notes = st.text_area("Notes (optional)")
    url = st.text_input("Google Docs URL (optional)")
    if st.button("Add"):
        if not title.strip():
            st.error("Title is required.")
            st.stop()
        add_daily_task(
            date_str,
            task_id=None,
            title=title.strip(),
            notes=notes.strip() if notes else None,
            url=url.strip() if url else None
        )
        st.success("Task added successfully.")
