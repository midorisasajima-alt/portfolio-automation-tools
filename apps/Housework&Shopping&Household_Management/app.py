import streamlit as st
from db import init_db
init_db()

st.set_page_config(page_title="Housework & Shopping & Household Management", layout="wide")
