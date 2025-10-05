import streamlit as st
from datetime import date
from db import insert_candidate

st.title("3) Add Candidate")

with st.form("cand_add"):
    title = st.text_input("Title")
    d = st.date_input("Date", value=date.today(), format="YYYY-MM-DD")
    start = st.time_input("Start Time")
    end = st.time_input("End Time")
    info = st.text_input("Information (Link)", placeholder="https://...")
    submitted = st.form_submit_button("Add")

    if submitted:
        # Validation: enforce End > Start (same time not allowed)
        if end <= start:
            st.error("End time must be later than start time.")
        else:
            insert_candidate(
                d.isoformat(),
                title,
                start.strftime("%H:%M"),
                end.strftime("%H:%M"),
                info,
            )
            st.success("Candidate added successfully.")
