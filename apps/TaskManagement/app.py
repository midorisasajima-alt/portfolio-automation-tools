from __future__ import annotations
import streamlit as st
from db import init_db

@st.cache_resource
def _init():
    init_db()
_init()

st.header("Non exiguum temporis habemus, sed multum perdidimus.")
st.text("ーOur time is not short, but we make it so by wasting it.ー")
