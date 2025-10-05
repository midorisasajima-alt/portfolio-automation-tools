import streamlit as st
from datetime import date
from sqlalchemy import func
from db import init_db, SessionLocal, Person
from utils import upsert_person, delete_person

init_db()
st.set_page_config(page_title="Edit/Delete (Search Supported)", layout="wide")
st.title("Edit/Delete")

# --- Search UI ---
name_q = st.text_input("Search by name (partial match)", value="")
country_q = st.text_input("Search by country (partial match)", value="")
notes_q = st.text_input("Search within notes (case-insensitive partial match)", value="")

if "edit_search_trigger" not in st.session_state:
    st.session_state["edit_search_trigger"] = False

if st.button("Search"):
    st.session_state["edit_search_trigger"] = True

# --- Data retrieval (apply search filters) ---
with SessionLocal() as sess:
    q = sess.query(Person)
    if st.session_state.get("edit_search_trigger"):
        if name_q.strip():
            q = q.filter(Person.name.ilike(f"%{name_q.strip()}%"))
        if country_q.strip():
            q = q.filter(Person.country.ilike(f"%{country_q.strip()}%"))
        if notes_q.strip():
            # SQLite-compatible: lowercase COALESCE(notes, '') for LIKE search
            q = q.filter(
                func.lower(func.coalesce(Person.notes, "")).like(f"%{notes_q.strip().lower()}%")
            )
    persons = q.order_by(Person.name.asc()).all()

if not persons:
    st.info("No matching records found. Please adjust your search criteria.")
    st.stop()

options = {f"{p.name} / {p.country or '-'} / id:{p.id}": p.id for p in persons}
sel = st.selectbox("Select a person", options=list(options.keys()))
person_id = options[sel] if sel else None

if person_id:
    with SessionLocal() as sess:
        p = sess.get(Person, person_id)

    with st.form("edit_form"):
        name = st.text_input("Name*", value=p.name or "")
        instagram = st.text_input("Instagram", value=p.instagram or "")
        whatsapp = st.text_input("WhatsApp", value=p.whatsapp or "")
        linkedin = st.text_input("LinkedIn", value=p.linkedin or "")
        country = st.text_input("Country of origin", value=p.country or "")
        region = st.text_input("Region of origin", value=p.region or "")
        work_history = st.text_area("Work history (free description)", value=p.work_history or "", height=120)
        birthday = st.date_input("Birthday", value=p.birthday)
        residence = st.text_input("Current residence", value=p.residence or "")
        photo_album = st.text_input("Photo album information", value=p.photo_album or "")
        notes = st.text_area("Notes", value=p.notes or "", height=120)

        colu1, colu2 = st.columns(2)
        with colu1:
            saved = st.form_submit_button("Save")
        with colu2:
            deleted = st.form_submit_button("Delete", use_container_width=True)

        if saved:
            with SessionLocal() as sess:
                upsert_person(
                    sess,
                    id=p.id,
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
            st.success("Saved successfully.")
            st.rerun()

        if deleted:
            with SessionLocal() as sess:
                delete_person(sess, p.id)
            st.success("Deleted successfully.")
            st.rerun()
