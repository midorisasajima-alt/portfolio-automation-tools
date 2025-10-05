# ==========================================================
# pages/20_誕生日.py（Streamlit ページ：表示のみ）
# ==========================================================
import streamlit as st
import pandas as pd
from db import init_db, list_birthdays_today_and_tomorrow

st.set_page_config(page_title="誕生日一覧", layout="centered")
st.title("誕生日（今日・明日）")

# DB初期化（既存なら無害）
init_db()

data = list_birthdays_today_and_tomorrow()

# 今日
st.subheader("今日の誕生日")
if data["today"]:
    df_today = pd.DataFrame(data["today"])  # 列: id, name, age, birthday
    st.dataframe(df_today[["name", "age", "birthday"]], use_container_width=True)
else:
    st.info("なし")

# 明日
st.subheader("明日の誕生日")
if data["tomorrow"]:
    df_tomorrow = pd.DataFrame(data["tomorrow"])  # 列: id, name, age, birthday
    st.dataframe(df_tomorrow[["name", "age", "birthday"]], use_container_width=True)
else:
    st.info("なし")