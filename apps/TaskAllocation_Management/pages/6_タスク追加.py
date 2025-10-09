
import streamlit as st
from data_store import add_task, ALL_STATUSES

st.set_page_config(page_title="タスク追加", layout="centered")
st.header("タスク追加（王のタスクへ）")

with st.form("add_task_form"):
    name = st.text_input("タスク名", "")
    memo = st.text_area("メモ（任意）", "", height=120)
    url = st.text_input("URL（任意）", "")
    status = st.selectbox("状態", ALL_STATUSES, index=0)
    submitted = st.form_submit_button("追加")
    if submitted:
        if name.strip() == "":
            st.error("タスク名は必須です。")
        else:
            t = add_task("王", name=name.strip(), memo=memo.strip(), url=url.strip(), status=status)
            st.success(f"追加しました：{t['name']}")
