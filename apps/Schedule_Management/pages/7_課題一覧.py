# =============================
# pages/7_課題一覧.py
# -----------------------------
import streamlit as st
from pathlib import Path
from db import list_tasks, update_task, delete_task, list_task_proofs

st.title("7) 課題一覧")

# --- rerun 互換関数 ---
def _rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()
def render_delete_controls(row_id: int, *, key_prefix: str = ""):
    confirm_key = f"confirm_del_{key_prefix}{row_id}"
    if not st.session_state.get(confirm_key, False):
        # まだ確認前：削除ボタンのみ
        if st.button("🗑️ 削除", key=f"del_{key_prefix}{row_id}"):
            st.session_state[confirm_key] = True
            # ここでは手動rerun不要。押下で自動的に再実行され、下の確認UIが出ます。
    else:
        # 確認表示
        st.warning("本当に削除しますか？この操作は元に戻せません。")
        c_ok, c_ng = st.columns(2)
        with c_ok:
            if st.button("はい、削除する", key=f"del_ok_{key_prefix}{row_id}"):
                delete_task(int(row_id))
                st.session_state.pop(confirm_key, None)
                st.success("削除しました。")
                _rerun()
        with c_ng:
            if st.button("キャンセル", key=f"del_ng_{key_prefix}{row_id}"):
                st.session_state.pop(confirm_key, None)
                _rerun()
                

tab_active, tab_done = st.tabs(["完了前", "完了済み"])

with tab_active:
    tasks = list_tasks(active=True)
    for t in tasks:
        slider_key = f"p_{t['id']}"
        with st.container(border=True):
            st.write(f"📌 {t['title']}  締切: {t['due_date']} {t['due_time']}  所要: {t['required_hours']}h  情報: {t.get('info_url','')}")
            st.slider("達成率", 0, 100, int(t['progress'] * 100), key=slider_key)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 進捗を保存", key=f"save_{t['id']}"):
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
                    st.success("進捗を保存しました。")
            with c2:
                if st.button("✏️ 編集へ", key=f"edit_{t['id']}"):
                    st.session_state["edit_task_id"] = int(t["id"])
                    st.switch_page("pages/9_課題編集削除.py")
            with c3:
                key_base = str(t['id'])
                confirm_key = f"confirm_del_{key_base}"

                if not st.session_state.get(confirm_key, False):
                    # 1回目：確認フラグを立てる
                    if st.button("🗑️ 削除", key=f"del_{key_base}"):
                        st.session_state[confirm_key] = True
                        # ボタン押下で自動的に再実行され、下の確認UIに遷移
                else:
                    # 2回目以降：確認UIを表示
                    st.warning("本当に削除しますか？この操作は元に戻せません。")
                    col_ok, col_cancel = st.columns(2)
                    with col_ok:
                        if st.button("はい、削除する", key=f"del_ok_{key_base}"):
                            delete_task(int(t['id']))
                            st.session_state.pop(confirm_key, None)
                            st.success("削除しました。")
                            _rerun()
                    with col_cancel:
                        if st.button("キャンセル", key=f"del_ng_{key_base}"):
                            st.session_state.pop(confirm_key, None)
                            _rerun()


with tab_done:
    done = list_tasks(active=False)
    for t in done:
        with st.container(border=True):
            st.write(f"✅ {t['title']} | 完了日時: {t.get('completed_at','-')}")

            # 証拠プレビュー（任意：前回の実装に合わせて）
            proofs = list_task_proofs(int(t['id']))
            if proofs:
                st.caption("完了証拠")
                cols = st.columns(3)
                for i, p in enumerate(proofs):
                    path = Path(p.get("path") or "")
                    ts = p.get("uploaded_at", "")
                    col = cols[i % 3]
                    with col:
                        if path and path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"] and path.exists():
                            st.image(str(path), caption=f"{path.name}（{ts}）", use_container_width=True)
                        elif path and path.suffix.lower() == ".pdf" and path.exists():
                            with open(path, "rb") as f:
                                st.download_button(
                                    "📄 PDFをダウンロード",
                                    f,
                                    file_name=path.name,
                                    mime="application/pdf",
                                    key=f"pdf_{t['id']}_{i}",
                                )
                            st.caption(f"{path.name}（{ts}）")
                        elif path:
                            st.write(f"📎 {path.name}（{ts}）")
                        else:
                            st.write("（ファイルなし）")
            else:
                st.caption("完了証拠：なし")

            # 完了済み側にも削除ボタン（確認つき）
            key_base = f"done_{t['id']}"
            confirm_key = f"confirm_del_{key_base}"

            if not st.session_state.get(confirm_key, False):
                if st.button("🗑️ 削除", key=f"del_{key_base}"):
                    st.session_state[confirm_key] = True
            else:
                st.warning("本当に削除しますか？この操作は元に戻せません。")
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("はい、削除する", key=f"del_ok_{key_base}"):
                        delete_task(int(t['id']))
                        st.session_state.pop(confirm_key, None)
                        st.success("削除しました。")
                        _rerun()
                with col_cancel:
                    if st.button("キャンセル", key=f"del_ng_{key_base}"):
                        st.session_state.pop(confirm_key, None)
                        _rerun()
