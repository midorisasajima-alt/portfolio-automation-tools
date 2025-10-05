import streamlit as st
from db import init_db, ensure_seed_goals
from config import NUTRIENTS, DAILY_GOALS

st.set_page_config(page_title="栄養管理", layout="wide")

# 初期化
init_db()
ensure_seed_goals(DAILY_GOALS)

st.title("Mens sana in corpore sano")

st.write("ー健全なる精神は健全なる身体に宿るー")
