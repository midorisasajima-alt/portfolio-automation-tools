import streamlit as st
from db import init_db

st.set_page_config(page_title="Contacts", page_icon="📇", layout="wide")
init_db()

st.title("φίλος ἄλλος αὐτός")
st.text("ー友とはもう一人の自分自身であるー")
