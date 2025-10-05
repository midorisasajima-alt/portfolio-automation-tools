import streamlit as st
from db import list_trash, restore_from_trash, delete_from_trash

st.title("5) Recently Deleted Items (Candidates)")

def _rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()

period = st.selectbox("Display period", ["7 days", "30 days", "90 days", "All"], index=1)
days = {"7 days": 7, "30 days": 30, "90 days": 90, "All": None}[period]

trash = list_trash(limit_days=days, limit_rows=200)

if not trash:
    st.info("No deleted records found.")
else:
    for t in trash:
        colL, colR = st.columns([4, 1])
        with colL:
            info_url = t.get("info_url")
            lines = [
                f"{t['title']}",
                f"- **Date & Time**: {t['date']} {t['start_time']} → {t['end_time']}",
            ]
            if info_url:
                lines.append(f"- **Info**: {info_url}")
            lines.append(f"- **Deleted at**: {t['deleted_at']}")
            st.markdown("\n".join(lines))

        with colR:
            rid = str(t["id"])
            restore_confirm_key = f"confirm_restore_{rid}"
            purge_confirm_key   = f"confirm_purge_{rid}"

            restore_confirm = st.session_state.get(restore_confirm_key, False)
            purge_confirm   = st.session_state.get(purge_confirm_key, False)

            # 1) Restore confirmation flow
            if restore_confirm:
                st.warning("Are you sure you want to restore this item?")
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Yes", key=f"restore_ok_{rid}"):
                        restore_from_trash(int(t["id"]))
                        st.session_state.pop(restore_confirm_key, None)
                        st.success("Item restored successfully.")
                        _rerun()
                with b2:
                    if st.button("Cancel", key=f"restore_ng_{rid}"):
                        st.session_state.pop(restore_confirm_key, None)
                        _rerun()

            # 2) Permanent deletion confirmation flow
            elif purge_confirm:
                delete_from_trash(int(t["id"]))
                st.session_state.pop(purge_confirm_key, None)
                st.success("Item permanently deleted.")
                _rerun()

            # 3) Normal display (Restore / Delete)
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Restore", key=f"restore_{rid}"):
                        st.session_state[restore_confirm_key] = True
                with b2:
                    if st.button("Delete Permanently", key=f"purge_{rid}"):
                        st.session_state[purge_confirm_key] = True
