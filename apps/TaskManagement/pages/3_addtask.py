from __future__ import annotations
import streamlit as st
from db import add_task

st.set_page_config(page_title="Add Task", layout="centered")
st.title("Add Task")

DEFAULT_CATS = ["Work", "Study", "Relationships", "Life & Health", "Hobbies & Leisure", "Finance", "Other"]

with st.form("add_task"):
    title = st.text_input("Task name", placeholder="e.g., Draft project proposal")
    importance = st.slider("Importance (1–100)", 1, 100, 50)
    urgency = st.slider("Urgency (1–100)", 1, 100, 50)
    cat_choice = st.selectbox("Category", options=DEFAULT_CATS)
    custom_cat = ""
    if cat_choice == "Other":
        custom_cat = st.text_input("Custom category", placeholder="e.g., Volunteer work")
    url = st.text_input("Google Docs URL (optional)")

    if st.form_submit_button("Add"):
        category = custom_cat.strip() if (cat_choice == "Other" and custom_cat.strip()) else cat_choice
        if not title.strip():
            st.error("Task name is required.")
            st.stop()
        add_task(
            title.strip(),
            int(importance),
            int(urgency),
            category,
            url.strip() if url else None
        )
        st.success("Task added successfully.")
