import streamlit as st
from pathlib import Path
from db import list_tasks, update_task, delete_task, list_task_proofs

st.title("7) Task List")

# --- rerun helper (for compatibility) ---
def _rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()

def render_delete_controls(row_id: int, *, key_prefix: str = ""):
    confirm_key = f"confirm_del_{key_prefix}{row_id}"
    if not st.session_state.get(confirm_key, False):
        # Not yet confirmed: show only delete button
        if st.button("🗑️ Delete", key=f"del_{key_prefix}{row_id}"):
            st.session_state[confirm_key] = True
    else:
        # Confirmation prompt
        st.warning("Are you sure you want to delete this task? This action cannot be undone.")
        c_ok, c_ng = st.columns(2)
        with c_ok:
            if st.button("Yes, delete", key=f"del_ok_{key_prefix}{row_id}"):
                delete_task(int(row_id))
                st.session_state.pop(confirm_key, None)
                st.success("Task deleted successfully.")
                _rerun()
        with c_ng:
            if st.button("Cancel", key=f"del_ng_{key_prefix}{row_id}"):
                st.session_state.pop(confirm_key, None)
                _rerun()

tab_active, tab_done = st.tabs(["Active", "Completed"])

# --- Active Tasks ---
with tab_active:
    tasks = list_tasks(active=True)
    for t in tasks:
        slider_key = f"p_{t['id']}"
        with st.container(border=True):
            st.write(
                f"📌 {t['title']}  "
                f"Deadline: {t['due_date']} {t['due_time']}  "
                f"Duration: {t['required_hours']}h  "
                f"Info: {t.get('info_url','')}"
            )
            st.slider("Progress (%)", 0, 100, int(t['progress'] * 100), key=slider_key)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 Save Progress", key=f"save_{t['id']}"):
                    prog_pct = st.session_state.get(slider_key, int(t['progress'] * 100))
                    update_task(
                        int(t['id']),
                        t['title'],
                        t['due_date'],
                        t['due_time'],
                        float(t['required_hours']),
                        t.get('info_url', ''),
                        float(prog_pct) / 100.0,
                    )
                    st.success("Progress saved successfully.")
            with c2:
                if st.button("✏️ Edit", key=f"edit_{t['id']}"):
                    st.session_state["edit_task_id"] = int(t["id"])
                    st.switch_page("pages/9_TaskEditDelete.py")
            with c3:
                key_base = str(t['id'])
                confirm_key = f"confirm_del_{key_base}"

                if not st.session_state.get(confirm_key, False):
                    if st.button("🗑️ Delete", key=f"del_{key_base}"):
                        st.session_state[confirm_key] = True
                else:
                    st.warning("Are you sure you want to delete this task? This action cannot be undone.")
                    col_ok, col_cancel = st.columns(2)
                    with col_ok:
                        if st.button("Yes, delete", key=f"del_ok_{key_base}"):
                            delete_task(int(t['id']))
                            st.session_state.pop(confirm_key, None)
                            st.success("Task deleted successfully.")
                            _rerun()
                    with col_cancel:
                        if st.button("Cancel", key=f"del_ng_{key_base}"):
                            st.session_state.pop(confirm_key, None)
                            _rerun()

# --- Completed Tasks ---
with tab_done:
    done = list_tasks(active=False)
    for t in done:
        with st.container(border=True):
            st.write(f"✅ {t['title']} | Completed at: {t.get('completed_at','-')}")

            # Proof preview (optional)
            proofs = list_task_proofs(int(t['id']))
            if proofs:
                st.caption("Completion Proofs")
                cols = st.columns(3)
                for i, p in enumerate(proofs):
                    path = Path(p.get("path") or "")
                    ts = p.get("uploaded_at", "")
                    col = cols[i % 3]
                    with col:
                        if path and path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"] and path.exists():
                            st.image(str(path), caption=f"{path.name} ({ts})", use_container_width=True)
                        elif path and path.suffix.lower() == ".pdf" and path.exists():
                            with open(path, "rb") as f:
                                st.download_button(
                                    "📄 Download PDF",
                                    f,
                                    file_name=path.name,
                                    mime="application/pdf",
                                    key=f"pdf_{t['id']}_{i}",
                                )
                            st.caption(f"{path.name} ({ts})")
                        elif path:
                            st.write(f"📎 {path.name} ({ts})")
                        else:
                            st.write("(File not found)")
            else:
                st.caption("No completion proofs available.")

            # Delete button with confirmation (for completed tasks)
            key_base = f"done_{t['id']}"
            confirm_key = f"confirm_del_{key_base}"

            if not st.session_state.get(confirm_key, False):
                if st.button("🗑️ Delete", key=f"del_{key_base}"):
                    st.session_state[confirm_key] = True
            else:
                st.warning("Are you sure you want to delete this task? This action cannot be undone.")
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("Yes, delete", key=f"del_ok_{key_base}"):
                        delete_task(int(t['id']))
                        st.session_state.pop(confirm_key, None)
                        st.success("Task deleted successfully.")
                        _rerun()
                with col_cancel:
                    if st.button("Cancel", key=f"del_ng_{key_base}"):
                        st.session_state.pop(confirm_key, None)
                        _rerun()

