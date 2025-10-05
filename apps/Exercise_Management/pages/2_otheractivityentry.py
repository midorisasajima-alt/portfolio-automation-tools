# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db import insert_activity
from utils import activity_mets_min

st.set_page_config(page_title="Other Activity Entry", layout="centered")

with st.form("form_activity"):
    d = st.date_input("Date", value=date.today(), format="YYYY-MM-DD")
    atype = st.text_input("Type of activity (e.g., Run, Bike, Strength training, etc.)", value="Run")
    mets = st.number_input("METs (intensity)", min_value=0.0, step=0.1, value=7.0, format="%.1f")
    minutes = st.number_input("Duration (minutes)", min_value=0.0, step=1.0, value=30.0, format="%.1f")
    preview = activity_mets_min(float(mets), float(minutes))
    st.info(f"Reference: This input corresponds to approximately {preview:.1f} METs·min")

    submitted = st.form_submit_button("Save")
    if submitted:
        rec_id = insert_activity(d.strftime("%Y-%m-%d"), atype.strip() or "Activity", float(mets), float(minutes))
        st.success(f"Saved successfully (ID: {rec_id})")
