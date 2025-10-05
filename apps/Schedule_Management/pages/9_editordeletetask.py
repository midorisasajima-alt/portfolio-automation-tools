import streamlit as st
import datetime as dt
from pathlib import Path
from db import get_task, update_task, delete_task, insert_task_proof

st.title("9) Edit / Delete / Complete Task")

# --- rerun helper (for compatibility) ---
def _rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()

# --- Retrieve task ID: from URL query or session_state ---
task_id = None

# 1) From URL query (if supported)
qid = None
if hasattr(st, "query_params"):
    q = st.query_params.get("id")
    if isinstance(q, list):
        q = q[0] if q else None
    qid = q

# 2) Fallback: from session_state
if qid is None:
    qid = st.session_state.get("edit_task_id")

# Parse as integer
if qid is not None:
    try:
        task_id = int(qid)
    except Exception:
        task_id = None

if task_id is None:
    st.info("No task ID specified. Please access this page from 7) Task List.")
    st.stop()

t = get_task(task_id)
if not t:
    st.error("Task not found.")
    st.stop()

# --- Progress normalization ---
prog_init = t.get("progress", 0.0) or 0.0
try:
    prog_init_pct = int(round(float(prog_init) * 100))
except Exception:
    prog_init_pct = 0

# --- Edit / Delete form ---
with st.form("task_edit"):
    title = st.text_input("Title", t["title"])
    d = st.text_input("Due Date (YYYY-MM-DD)", t["due_date"])
    tm = st.text_input("Due Time (HH:MM)", t["due_time"])
    hrs = st.number_input("Estimated Hours (h)", min_value=0.0, step=0.5, value=float(t["required_hours"]))
    info = st.text_input("Information (Link)", t.get("info_url", ""))
    prog = st.slider("Progress (%)", 0, 100, prog_init_pct)

    col1, col2, col3 = st.columns(3)
    with col1:
        saved = st.form_submit_button("Save")
    with col2:
        removed = st.form_submit_button("Delete")
    with col3:
        done = st.form_submit_button("Complete (Upload Proof)")

if saved:
    update_task(task_id, title, d, tm, float(hrs), info, prog / 100.0)
    st.success("Saved successfully.")
    _rerun()

if removed:
    delete_task(task_id)
    st.success("Deleted successfully.")
    _rerun()

# --- Completion proof upload mode ---
if done:
    st.session_state["proof_mode"] = True
    _rerun()

if st.session_state.get("proof_mode"):
    st.subheader("Upload Completion Proof")
    with st.form("proof_form"):
        up = st.file_uploader("Completion proof (screenshot, etc.)", type=["png", "jpg", "jpeg", "pdf"])
        c1, c2 = st.columns(2)
        with c1:
            confirm = st.form_submit_button("Upload and Mark as Complete")
        with c2:
            cancel = st.form_submit_button("Cancel")

    if confirm:
        if up is None:
            st.warning("Please select a file first.")
        else:
            up_dir = Path("uploads")
            up_dir.mkdir(parents=True, exist_ok=True)
            safe_name = f"task_{task_id}_{Path(up.name).name}"
            save_to = up_dir / safe_name
            with open(save_to, "wb") as f:
                f.write(up.getbuffer())

            insert_task_proof(task_id, str(save_to), dt.datetime.utcnow().isoformat())
            update_task(task_id, title, d, tm, float(hrs), info, 1.0)
            st.success("Task marked as completed.")
            st.session_state.pop("proof_mode", None)
            _rerun()

    if cancel:
        st.session_state.pop("proof_mode", None)
        _rerun()
