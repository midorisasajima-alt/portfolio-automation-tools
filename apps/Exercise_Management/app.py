# -*- coding: utf-8 -*-
import streamlit as st
from db import init_db
from config import APP_TITLE

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 初回起動時にDB初期化
init_db()

st.title("Because it’s there.")
st.text("ーWhen the highest peak stands before us, how could we not climb it?ー")
