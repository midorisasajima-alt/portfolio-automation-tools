from __future__ import annotations
import streamlit as st, datetime
from db import add_daily_task, list_tasks, STATUS_ACTIVE

st.set_page_config(page_title="デイリータスク追加", layout="centered")
st.title("デイリータスク追加")

date = st.date_input("日付", value=datetime.date.today())
date_str = date.strftime("%Y-%m-%d")

mode = st.radio("追加モード", ["既存タスクにリンク","自由入力（単独のデイリー）"], horizontal=True)

if mode == "既存タスクにリンク":
    tasks = list_tasks(status=STATUS_ACTIVE)
    if not tasks:
        st.info("アクティブなタスクがありません。")
    else:
        options = {f"{t['title']}（重要:{t['importance']} 緊急:{t['urgency']}｜{t['category']}）": t["id"] for t in tasks}
        label = st.selectbox("タスクを選択", options=list(options.keys()))
        notes = st.text_area("メモ（任意）", placeholder="今日の具体的な着手内容など")
        if st.button("追加"):
            add_daily_task(date_str, task_id=int(options[label]), title=None, notes=notes.strip() if notes else None, url=None)
            st.success("追加しました。")
else:
    title = st.text_input("タイトル", placeholder="例：30分ジョギング")
    notes = st.text_area("メモ（任意）")
    url = st.text_input("GoogleドキュメントURL（任意）")
    if st.button("追加"):
        if not title.strip():
            st.error("タイトルは必須です。")
            st.stop()
        add_daily_task(date_str, task_id=None, title=title.strip(), notes=notes.strip() if notes else None, url=url.strip() if url else None)
        st.success("追加しました。")
