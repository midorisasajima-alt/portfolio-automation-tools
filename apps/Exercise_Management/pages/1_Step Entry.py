# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db import insert_walking
from utils import walking_mets_min

st.set_page_config(page_title="Step Entry", layout="centered")

with st.form("form_walk"):
    d = st.date_input("Date", value=date.today(), format="YYYY-MM-DD")

    # Number of steps
    steps = st.number_input(
        "Steps (count)",
        min_value=0,
        step=100,
        value=6000
    )

    # Step length in cm/step (converted internally to m/step)
    step_len_cm = st.number_input(
        "Step length (cm/step)",
        min_value=30,   # Typical range: 30–120 cm
        max_value=120,
        step=1,
        value=70
    )

    # Walking speed in km/h (converted internally to m/min)
    speed_kmh = st.number_input(
        "Walking speed (km/h)",
        min_value=1.0,   # Reasonable range: 1–12 km/h
        max_value=12.0,
        step=0.1,
        value=4.7,
        format="%.1f"
    )

    # Unit conversion
    step_len_m = step_len_cm / 100.0             # m/step
    speed_m_per_min = speed_kmh * 1000.0 / 60.0  # m/min

    # Preview (based on ACSM formula)
    mets_min_preview = walking_mets_min(int(steps), float(step_len_m), float(speed_m_per_min))
    st.info(f"Reference: This input corresponds to approximately {mets_min_preview:.1f} METs·min")

    submitted = st.form_submit_button("Save")
    if submitted:
        rec_id = insert_walking(
            d.strftime("%Y-%m-%d"),
            int(steps),
            float(step_len_m),
            float(speed_m_per_min)
        )
        st.success(f"Saved successfully (ID: {rec_id})")
