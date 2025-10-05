
# =============================
# pages/3_候補追加.py
# -----------------------------
import streamlit as st
from datetime import date
from db import insert_candidate

st.title("3) 候補追加")

with st.form("cand_add"):
    title = st.text_input("タイトル")
    d = st.date_input("日付", value=date.today(), format="YYYY-MM-DD")
    start = st.time_input("開始時間")
    end = st.time_input("終了時間")
    info = st.text_input("情報（リンク）", placeholder="https://...")
    submitted = st.form_submit_button("追加")

    if submitted:
    # バリデーション：終了 > 開始 を強制（同時刻は不可）
        if end <= start:
            st.error("終了時間は開始時間よりも後でなければなりません。")
        else:
            insert_candidate(
                d.isoformat(),
                title,
                start.strftime("%H:%M"),
                end.strftime("%H:%M"),
                info,
            )
            st.success("追加しました。")

