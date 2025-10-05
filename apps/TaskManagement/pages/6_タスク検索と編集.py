from __future__ import annotations
import streamlit as st
from db import list_tasks, get_task, update_task, set_task_status, delete_task
from db import STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, STATUS_DONE

st.set_page_config(page_title="タスク検索と編集", layout="centered")
st.title("タスク検索と編集")

if "search_selected_id" not in st.session_state:
    st.session_state.search_selected_id = None

include_done = st.checkbox("完了も候補に含める", value=True)
q = st.text_input("タスク名で検索", placeholder="例：企画書ドラフト作成、請求書 など")

statuses = [STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING] + ([STATUS_DONE] if include_done else [])
matches = list_tasks(search_title=q.strip() or None, status=statuses)[:50]

if not matches:
    st.info("該当タスクが見つかりません。")
    st.stop()

options = {f"{t['title']}｜重要:{t['importance']} 緊急:{t['urgency']}｜{t['category']}（{t['status']}）ID:{t['id']}": t["id"] for t in matches}
sel_label = st.selectbox("該当タスクを選択", options=list(options.keys()))
sel_id = options[sel_label]

if st.button("決定"):
    st.session_state.search_selected_id = int(sel_id)

st.divider()
tid = st.session_state.search_selected_id
if tid is None:
    st.caption("上で選び「決定」を押すと編集フォームが出ます。")
    st.stop()

row = get_task(int(tid))
if not row:
    st.error("選択されたタスクが見つかりません。")
    st.stop()

st.subheader("タスク詳細（編集可）")

DEFAULT_CATS = ["仕事","学業","人間関係","生活・健康","趣味・余暇","財務"]
cats = sorted(set(DEFAULT_CATS + [row["category"]]))

status_map = {"アクティブ":STATUS_ACTIVE, "非アクティブ":STATUS_INACTIVE, "待ち":STATUS_WAITING, "完了":STATUS_DONE}
inv_status_map = {v:k for k,v in status_map.items()}
current_status_label = inv_status_map.get(row["status"], "アクティブ")

with st.form("edit_form"):
    title = st.text_input("タスク名", value=row["title"])
    importance = st.slider("重要度(1-100)", 1, 100, int(row["importance"]))
    urgency = st.slider("緊急度(1-100)", 1, 100, int(row["urgency"]))
    cat_choice = st.selectbox("種類", options=cats, index=cats.index(row["category"]) if row["category"] in cats else 0)
    url = st.text_input("GoogleドキュメントURL（任意）", value=row["url"] or "")
    status_label = st.selectbox("状態（4区分）", options=list(status_map.keys()), index=list(status_map.keys()).index(current_status_label))

    if st.form_submit_button("保存"):
        if not title.strip():
            st.error("タスク名は必須です。")
        else:
            update_task(int(tid), title.strip(), int(importance), int(urgency), cat_choice, url.strip() if url else None)
            set_task_status(int(tid), status_map[status_label])
            st.success("保存しました。")

c1, c2, c3 = st.columns(3)
with c1:
    if row["url"]:
        st.link_button("Googleドキュメントを開く", row["url"])
with c2:
    if st.button("選び直す"):
        st.session_state.search_selected_id = None
        st.rerun()
with c3:
    st.empty()

st.divider()
with st.expander("危険な操作（削除）", expanded=False):
    st.caption("※取り消せません。リンクするデイリーも削除されます。")
    confirm = st.checkbox("このタスクを完全に削除する", key="del_confirm")
    if st.button("タスク削除", disabled=not confirm):
        delete_task(int(tid))
        st.success("削除しました。")
        st.session_state.search_selected_id = None
        st.rerun()
