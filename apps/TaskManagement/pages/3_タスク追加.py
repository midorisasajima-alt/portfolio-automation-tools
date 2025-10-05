from __future__ import annotations
import streamlit as st
from db import add_task

st.set_page_config(page_title="タスク追加", layout="centered")
st.title("タスク追加")

DEFAULT_CATS = ["仕事","学業","人間関係","生活・健康","趣味・余暇","財務","その他"]

with st.form("add_task"):
    title = st.text_input("タスク名", placeholder="例：企画書ドラフト作成")
    importance = st.slider("重要度(1-100)", 1, 100, 50)
    urgency = st.slider("緊急度(1-100)", 1, 100, 50)
    cat_choice = st.selectbox("種類", options=DEFAULT_CATS)
    custom_cat = ""
    if cat_choice == "その他":
        custom_cat = st.text_input("種類（自由入力）", placeholder="例：ボランティア")
    url = st.text_input("GoogleドキュメントURL（任意）")

    if st.form_submit_button("追加"):
        category = custom_cat.strip() if (cat_choice=="その他" and custom_cat.strip()) else cat_choice
        if not title.strip():
            st.error("タスク名は必須です。")
            st.stop()
        add_task(title.strip(), int(importance), int(urgency), category, url.strip() if url else None)
        st.success("追加しました。")
