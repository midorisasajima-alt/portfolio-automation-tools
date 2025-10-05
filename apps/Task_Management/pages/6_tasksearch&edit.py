from __future__ import annotations
import streamlit as st
from db import list_tasks, get_task, update_task, set_task_status, delete_task
from db import STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, STATUS_DONE

st.set_page_config(page_title="Task Search and Edit", layout="centered")
st.title("Task Search and Edit")

if "search_selected_id" not in st.session_state:
    st.session_state.search_selected_id = None

include_done = st.checkbox("Include completed tasks", value=True)
q = st.text_input("Search by task name", placeholder="e.g., Draft proposal, Invoice, etc.")

statuses = [STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING] + ([STATUS_DONE] if include_done else [])
matches = list_tasks(search_title=q.strip() or None, status=statuses)[:50]

if not matches:
    st.info("No matching tasks found.")
    st.stop()

options = {
    f"{t['title']} | Importance: {t['importance']}  Urgency: {t['urgency']} | {t['category']} ({t['status']}) ID:{t['id']}": t["id"]
    for t in matches
}
sel_label = st.selectbox("Select a matching task", options=list(options.keys()))
sel_id = options[sel_label]

if st.button("Confirm"):
    st.session_state.search_selected_id = int(sel_id)

st.divider()
tid = st.session_state.search_selected_id
if tid is None:
    st.caption("Select a task above and click 'Confirm' to open the edit form.")
    st.stop()

row = get_task(int(tid))
if not row:
    st.error("Selected task not found.")
    st.stop()

st.subheader("Task Details (Editable)")

DEFAULT_CATS = ["Work", "Study", "Relationships", "Life & Health", "Hobbies & Leisure", "Finance"]
cats = sorted(set(DEFAULT_CATS + [row["category"]]))

status_map = {"Active": STATUS_ACTIVE, "Inactive": STATUS_INACTIVE, "Waiting": STATUS_WAITING, "Done": STATUS_DONE}
inv_status_map = {v: k for k, v in status_map.items()}
current_status_label = inv_status_map.get(row["status"], "Active")

with st.form("edit_form"):
    title = st.text_input("Task name", value=row["title"])
    importance = st.slider("Importance (1–100)", 1, 100, int(row["importance"]))
    urgency = st.slider("Urgency (1–100)", 1, 100, int(row["urgency"]))
    cat_choice = st.selectbox(
        "Category",
        options=cats,
        index=cats.index(row["category"]) if row["category"] in cats else 0
    )
    url = st.text_input("Google Docs URL (optional)", value=row["url"] or "")
    status_label = st.selectbox("Status (4 categories)", options=list(status_map.keys()),
                                index=list(status_map.keys()).index(current_status_label))

    if st.form_submit_button("Save"):
        if not title.strip():
            st.error("Task name is required.")
        else:
            update_task(
                int(tid),
                title.strip(),
                int(importance),
                int(urgency),
                cat_choice,
                url.strip() if url else None
            )
            set_task_status(int(tid), status_map[status_label])
            st.success("Task updated successfully.")

c1, c2, c3 = st.columns(3)
with c1:
    if row["url"]:
        st.link_button("Open Google Docs", row["url"])
with c2:
    if st.button("Re-select"):
        st.session_state.search_selected_id = None
        st.rerun()
with c3:
    st.empty()

st.divider()
with st.expander("Dangerous action (Delete)", expanded=False):
    st.caption("※ This action cannot be undone. Linked daily tasks will also be deleted.")
    confirm = st.checkbox("I understand and want to permanently delete this task", key="del_confirm")
    if st.button("Delete Task", disabled=not confirm):
        delete_task(int(tid))
        st.success("Task deleted successfully.")
        st.session_state.search_selected_id = None
        st.rerun()
