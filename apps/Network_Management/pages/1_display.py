import streamlit as st
from sqlalchemy.orm import Session
from db import init_db, SessionLocal, Person
from utils import search_persons

# Initialization
init_db()
st.set_page_config(page_title="Display (Search & View)", layout="wide")
st.title("Display (Search & View)")

# Input UI
name_q = st.text_input("Search by name (partial match)", value="")
country_q = st.text_input("Search by country (partial match)", value="")
notes_q = st.text_input("Search within notes (case-insensitive partial match)", value="")

# Ensure default state for search trigger
if "search_trigger" not in st.session_state:
    st.session_state["search_trigger"] = False

if st.button("Search"):
    st.session_state["search_trigger"] = True

# Execute search
if st.session_state.get("search_trigger"):
    with SessionLocal() as sess:
        rows = search_persons(sess, name_q=name_q, country_q=country_q)

        # Client-side partial match filter for notes
        nq = notes_q.strip().lower()
        if nq:
            rows = [p for p in rows if nq in (p.notes or "").lower()]

        st.write(f"Number of records: {len(rows)}")

        for p in rows:
            with st.expander(f"{p.name} ({p.country or '-'})", expanded=True):  # Open by default
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.text(f"Instagram: {p.instagram or ''}")
                    st.text(f"WhatsApp:  {p.whatsapp or ''}")
                    st.text(f"LinkedIn:  {p.linkedin or ''}")
                    st.text(f"Region:     {p.region or ''}")
                    st.text(f"Residence:  {p.residence or ''}")
                    st.text(f"Birthday:   {p.birthday.isoformat() if p.birthday else ''}")
                    st.text(f"Work history: {p.work_history or ''}")
                    st.text(f"Photo album:  {p.photo_album or ''}")
                    st.text(f"Notes:        {p.notes or ''}")
                with col2:
                    if p.photos:
                        for ph in p.photos[:6]:
                            st.image(ph.file_path, caption=ph.caption or "", use_column_width_width=True)
                    else:
                        st.caption("No photos available")
