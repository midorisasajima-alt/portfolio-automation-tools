import streamlit as st
import pandas as pd
from db import init_db, list_birthdays_today_and_tomorrow

st.set_page_config(page_title="Birthday List", layout="centered")
st.title("Birthdays (Today & Tomorrow)")

# DB initialization (harmless if already initialized)
init_db()

data = list_birthdays_today_and_tomorrow()

# Today
st.subheader("Today's Birthdays")
if data["today"]:
    df_today = pd.DataFrame(data["today"])  # columns: id, name, age, birthday
    st.dataframe(df_today[["name", "age", "birthday"]], use_container_width=True)
else:
    st.info("None")

# Tomorrow
st.subheader("Tomorrow's Birthdays")
if data["tomorrow"]:
    df_tomorrow = pd.DataFrame(data["tomorrow"])  # columns: id, name, age, birthday
    st.dataframe(df_tomorrow[["name", "age", "birthday"]], use_container_width=True)
else:
    st.info("None")
