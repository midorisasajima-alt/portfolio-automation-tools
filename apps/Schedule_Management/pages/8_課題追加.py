# =============================
# pages/8_課題追加.py
# -----------------------------
import streamlit as st
from datetime import date
from db import insert_task

st.title("8) 課題追加")

with st.form("task_add"):
    title = st.text_input("タイトル")
    d = st.date_input("締め切り日", value=date.today(), format="YYYY-MM-DD")
    t = st.time_input("締め切り時間")
    hrs = st.number_input("かかる時間（h）", min_value=0.0, step=0.5)
    info = st.text_input("情報（リンク）")
    rep = st.selectbox("繰り返し", ["一度限り","繰り返す"])
    period = None
    if rep == "繰り返す":
        period = st.number_input("周期（日）", min_value=1, value=7)
    submitted = st.form_submit_button("追加")
    if submitted:
        insert_task(title, d.isoformat(), t.strftime('%H:%M'), float(hrs), info, 0.0)
        st.success("追加しました。※繰り返しは今後の拡張で自動生成対応予定")

