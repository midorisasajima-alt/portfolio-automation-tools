import streamlit as st
from db import init_db, ensure_seed_goals
from config import NUTRIENTS, DAILY_GOALS

st.set_page_config(page_title="Neutrition Management", layout="wide")

# 初期化
init_db()
ensure_seed_goals(DAILY_GOALS)

st.title("Mens sana in corpore sano")
