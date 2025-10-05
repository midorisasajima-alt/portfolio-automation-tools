import streamlit as st
from datetime import date
from db import insert_task

st.title("8) Add Task")

with st.form("task_add"):
    title = st.text_input("Title")
    d = st.date_input("Due Date", value=date.today(), format="YYYY-MM-DD")
    t = st.time_input("Due Time")
    hrs = st.number_input("Estimated Hours (h)", min_value=0.0, step=0.5)
    info = st.text_input("Information (Link)")
    rep = st.selectbox("Repeat", ["One-time only", "Repeat"])
    period = None
    if rep == "Repeat":
        period = st.number_input("Interval (days)", min_value=1, value=7)

    submitted = st.form_submit_button("Add")

    if submitted:
        insert_task(title, d.isoformat(), t.strftime('%H:%M'), float(hrs), info, 0.0)
        st.success("Added successfully. Note: Recurrence will be supported in a future update.")
