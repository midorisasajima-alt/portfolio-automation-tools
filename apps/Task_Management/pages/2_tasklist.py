from __future__ import annotations
import streamlit as st
from db import list_tasks, list_recent_done, all_categories
from db import STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, set_task_status

st.set_page_config(page_title="Task List", layout="wide")
st.title("Task List")

title_filter = st.text_input("Search by task name")
date_filter = st.date_input("Filter by creation date (optional)", value=None)
date_str = date_filter.strftime("%Y-%m-%d") if date_filter else None

with st.expander("Filter by category and importance", expanded=False):
    DEFAULT_CATS = ["Work", "Study", "Relationships", "Life & Health", "Hobbies & Leisure", "Finance"]
    cats = sorted(set((all_categories() or []) + DEFAULT_CATS))
    sel_categories = st.multiselect("Category (multiple selection)", options=cats)
    imp_min, imp_max = st.slider("Importance", 1, 100, (1, 100))

def _match(row) -> bool:
    if sel_categories and (row["category"] not in sel_categories):
        return False
    try:
        imp = int(row["importance"])
    except Exception:
        return False
    return imp_min <= imp <= imp_max

status_map = {"Active": "active", "Inactive": "inactive", "Waiting": "waiting", "Done": "done"}
inv_status_map = {v: k for k, v in status_map.items()}

def _section(label, status_code: str, key_prefix: str):
    st.subheader(label)
    items = list_tasks(search_title=title_filter or None, date_str=date_str, status=status_code)
    items = [t for t in items if _match(t)]
    if not items:
        st.write("No matching tasks.")
        return
    expected_default = status_map[label]
    for t in items:
        cols = st.columns([6, 1, 1, 1])

        with cols[0]:
            st.write(f"• {t['title']} ({t['category']} | Importance: {t['importance']}  Urgency: {t['urgency']})")

        with cols[1]:
            # Current status (if row has no 'status', use section default)
            code = t["status"] if ("status" in t.keys()) else expected_default
            current = inv_status_map.get(code, inv_status_map[expected_default])

            new_status = st.selectbox(
                "Status",
                options=list(status_map.keys()),
                index=list(status_map.keys()).index(current),
                key=f"status_{key_prefix}_{t['id']}",
                label_visibility="collapsed",
            )
            if new_status != current:
                set_task_status(int(t["id"]), status_map[new_status])
                st.rerun()

        with cols[2]:
            if st.button("Details", key=f"{key_prefix}_{t['id']}"):
                st.session_state.search_selected_id = int(t["id"])
                try:
                    st.switch_page("pages/6_Task_Search_and_Edit.py")
                except Exception:
                    st.rerun()

        with cols[3]:
            if t["url"]:
                st.link_button("Doc", t["url"])


_section("Active", STATUS_ACTIVE, "open_active")
st.divider()
_section("Inactive", STATUS_INACTIVE, "open_inactive")
st.divider()
_section("Waiting", STATUS_WAITING, "open_waiting")

st.divider()
st.subheader("Completed (latest 20)")

done = list_recent_done(limit=20)
if not done:
    st.write("No completed tasks yet.")
else:
    status_map = {"Active": "active", "Inactive": "inactive", "Waiting": "waiting", "Done": "done"}
    inv_status_map = {v: k for k, v in status_map.items()}
    for t in done:
        cols = st.columns([6, 1, 1, 1])

        with cols[0]:
            completed_at = t["completed_at"] if ("completed_at" in t.keys()) else "-"
            st.write(f"• {t['title']} (Completed: {completed_at} | {t['category']})")

        with cols[1]:
            # sqlite3.Row does not have .get(), so check key existence
            code = t["status"] if ("status" in t.keys()) else "done"
            current = inv_status_map.get(code, "Done")
            new_status = st.selectbox(
                "Status",
                options=list(status_map.keys()),
                index=list(status_map.keys()).index(current),
                key=f"status_{t['id']}",
                label_visibility="collapsed"
            )
            if new_status != current:
                from db import set_task_status
                set_task_status(int(t["id"]), status_map[new_status])
                st.rerun()  # Immediately refresh the list after status change

        with cols[2]:
            if st.button("Details", key=f"done_{t['id']}"):
                st.session_state.search_selected_id = int(t["id"])
                try:
                    st.switch_page("pages/6_Task_Search_and_Edit.py")
                except Exception:
                    st.rerun()

        with cols[3]:
            if t["url"]:
                st.link_button("Doc", t["url"])
