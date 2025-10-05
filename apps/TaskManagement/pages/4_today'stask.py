from __future__ import annotations
import streamlit as st, datetime
from db import list_daily_tasks, set_daily_done_and_sync_task, get_task

st.set_page_config(page_title="Today's Tasks", layout="centered")
st.title("Today's Tasks")

today = datetime.date.today().strftime("%Y-%m-%d")
st.write(f"Date: {today}")

items = list_daily_tasks(today)
if not items:
    st.info("No daily tasks registered for today.")
else:
    for it in items:
        cols = st.columns([5, 1, 1, 1])
        was_done = bool(it["done"])
        task_id = it["task_id"]
        linked = get_task(int(task_id)) if task_id else None

        with cols[0]:
            label = (
                linked["title"]
                if (linked and linked["title"])
                else (it["title"] if it["title"] else "(Untitled)")
            )
            st.write(f"{label} {'(Completed)' if was_done else '(Incomplete)'}")
            if it["notes"]:
                st.caption(it["notes"])

        with cols[1]:
            doc_url = it["url"] if it["url"] else (linked["url"] if (linked and linked["url"]) else None)
            if doc_url:
                st.link_button("Doc", doc_url)

        with cols[2]:
            if was_done:
                if st.button("↩ Mark as Incomplete", key=f"reopen_{it['id']}"):
                    set_daily_done_and_sync_task(int(it["id"]), False)
                    st.rerun()
            else:
                if st.button("✅ Mark as Completed", key=f"done_{it['id']}"):
                    set_daily_done_and_sync_task(int(it["id"]), True)
                    st.rerun()

        with cols[3]:
            if task_id and linked:
                if st.button("Details", key=f"detail_{it['id']}"):
                    st.session_state.search_selected_id = int(task_id)
                    try:
                        st.switch_page("pages/6_Task_Search_and_Edit.py")
                    except Exception:
                        st.rerun()
            else:
                st.button("Details", disabled=True, key=f"detail_{it['id']}")
