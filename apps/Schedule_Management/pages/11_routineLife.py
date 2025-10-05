import streamlit as st
from db import insert_routine, list_routine, update_routine, delete_routine

st.title("11) Routine Life (Regular Activities)")

mode = st.tabs(["Add", "Edit / Delete"])

# --- Add Routine ---
with mode[0]:
    with st.form("routine_add"):
        title = st.text_input("Activity Title (e.g., Sleep, Meals, Commute, etc.)")
        hrs = st.number_input("Required Time (hours per occurrence)", min_value=0.0, step=0.5)
        period = st.number_input("Cycle (days)", min_value=1, value=1)
        submitted = st.form_submit_button("Add")
        if submitted:
            insert_routine(title, float(hrs), int(period))
            st.success("Added successfully.")

# --- Edit / Delete Routine ---
with mode[1]:
    rts = list_routine()
    for r in rts:
        with st.form(f"edit_{r['id']}"):
            title = st.text_input("Title", r['title'])
            hrs = st.number_input("Required Time (hours per occurrence)", min_value=0.0, step=0.5, value=float(r['hours']))
            period = st.number_input("Cycle (days)", min_value=1, value=int(r['period_days']))
            col1, col2 = st.columns(2)
            with col1:
                saved = st.form_submit_button("Save")
            with col2:
                removed = st.form_submit_button("Delete")
        if saved:
            update_routine(r['id'], title, float(hrs), int(period))
            st.success("Saved successfully.")
        if removed:
            delete_routine(r['id'])
            st.success("Deleted successfully.")
