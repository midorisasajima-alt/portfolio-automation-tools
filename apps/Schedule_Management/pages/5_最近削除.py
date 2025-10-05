# =============================
# pages/5_最近削除.py
# -----------------------------
import streamlit as st
from db import list_trash, restore_from_trash,delete_from_trash

st.title("5) 最近削除した項目（候補）")

def _rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()

period = st.selectbox("表示期間", ["7日", "30日", "90日", "全件"], index=1)
days = {"7日": 7, "30日": 30, "90日": 90, "全件": None}[period]

trash = list_trash(limit_days=days, limit_rows=200)

if not trash:
    st.info("該当データはありません。")
else:
    for t in trash:
        colL, colR = st.columns([4, 1])
        with colL:
            info_url = t.get("info_url")
            lines = [
                f"{t['title']}",
                f"- **日時**: {t['date']} {t['start_time']} → {t['end_time']}",
            ]
            if info_url:
                lines.append(f"- **情報**: {info_url}")
            lines.append(f"- **削除**: {t['deleted_at']}")
            st.markdown("\n".join(lines))

        with colR:
            rid = str(t["id"])
            restore_confirm_key = f"confirm_restore_{rid}"
            purge_confirm_key   = f"confirm_purge_{rid}"

            restore_confirm = st.session_state.get(restore_confirm_key, False)
            purge_confirm   = st.session_state.get(purge_confirm_key, False)

            # 1) 復元の確認フロー
            if restore_confirm:
                st.warning("復元します。よろしいですか？")
                b1, b2 = st.columns(2)  # ← colR 内で columns は常に1段だけ
                with b1:
                    if st.button("はい", key=f"restore_ok_{rid}"):
                        restore_from_trash(int(t["id"]))
                        st.session_state.pop(restore_confirm_key, None)
                        st.success("復元しました。")
                        _rerun()
                with b2:
                    if st.button("取消", key=f"restore_ng_{rid}"):
                        st.session_state.pop(restore_confirm_key, None)
                        _rerun()

            # 2) 完全削除の確認フロー
            elif purge_confirm:
                delete_from_trash(int(t["id"]))
                st.session_state.pop(purge_confirm_key, None)
                st.success("削除しました。")
                _rerun()

            # 3) 通常表示（復元／完全削除）
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("復元", key=f"restore_{rid}"):
                        st.session_state[restore_confirm_key] = True
                with b2:
                    if st.button("削除", key=f"purge_{rid}"):
                        st.session_state[purge_confirm_key] = True
