
import streamlit as st
from data_store import load_db, get_collection, update_task, delete_task, propagate, ALL_STATUSES

st.set_page_config(page_title="タスク編集と追加", layout="centered")
st.header("タスク編集と追加")

owner = st.session_state.get("edit_owner")
task_id = st.session_state.get("edit_task_id")

if not owner or not task_id:
    st.warning("編集対象が指定されていません。各ページの「詳細へ」から遷移してください。")
    st.stop()

db = load_db()
col = get_collection(db, owner)
target = next((t for t in col if t["id"] == task_id), None)
if not target:
    st.error("対象タスクが見つかりません。")
    st.stop()

st.write(f"対象：{owner} のタスク")

with st.form("edit_form"):
    name = st.text_input("タスク名", target.get("name",""))
    url = st.text_input("URL", target.get("url",""))
    memo = st.text_area("メモ", target.get("memo",""), height=160)
    status = st.selectbox("状態", ALL_STATUSES, index=ALL_STATUSES.index(target.get("status","アクティブ")))
    submitted = st.form_submit_button("保存")
    if submitted:
        update_task(owner, target["id"], name=name, url=url, memo=memo, status=status)
        st.success("保存しました。")

cols = st.columns([1,1,1])
with cols[0]:
    if st.button("下令（子ノードへ発行＋現タスク完了）", type="primary"):
        propagate(owner, target)
        st.success("下令しました。")
with cols[1]:
    if st.button("削除（確認1回目）", key="del1"):
        st.session_state["confirm_delete"] = True
with cols[2]:
    if st.session_state.get("confirm_delete"):
        if st.button("本当に削除しますか？（2回目）", key="del2"):
            ok = delete_task(owner, target["id"])
            st.success("削除しました。" if ok else "削除に失敗しました。")
            st.session_state.pop("confirm_delete", None)
