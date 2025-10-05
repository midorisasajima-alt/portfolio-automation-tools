import streamlit as st
from datetime import date
from db import init_db, SessionLocal
from utils import upsert_person

init_db()
st.title("Add Entry")

with st.form("add_form", clear_on_submit=True):
    name = st.text_input("Name*", max_chars=200)
    instagram = st.text_input("Instagram")
    whatsapp = st.text_input("WhatsApp")
    linkedin = st.text_input("LinkedIn")
    country = st.text_input("Country of origin")
    region = st.text_input("Region of origin")
    work_history = st.text_area("Work history (free description)", height=120)
    birthday = st.date_input("Birthday", value=None, format="YYYY-MM-DD")
    residence = st.text_input("Current residence")
    photo_album = st.text_input("Photo album information")
    notes = st.text_area("Notes", height=120)
    submitted = st.form_submit_button("Add")

    if submitted:
        if not name.strip():
            st.error("Name is required.")
        else:
            with SessionLocal() as sess:
                p = upsert_person(
                    sess,
                    name=name.strip(),
                    instagram=instagram.strip() or None,
                    whatsapp=whatsapp.strip() or None,
                    linkedin=linkedin.strip() or None,
                    country=country.strip() or None,
                    region=region.strip() or None,
                    work_history=work_history.strip() or None,
                    birthday=birthday if isinstance(birthday, date) else None,
                    residence=residence.strip() or None,
                    photo_album=photo_album.strip() or None,
                    notes=notes.strip() or None,
                )
                st.success(f"Added successfully (ID: {p.id})")
