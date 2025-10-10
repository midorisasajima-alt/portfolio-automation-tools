import streamlit as st
from db import init_db, SessionLocal, Person
from utils import save_photo_bytes, add_photo

init_db()
st.title("Photo Upload")

with SessionLocal() as sess:
    persons = sess.query(Person).order_by(Person.name.asc()).all()

options = {f"{p.name} / {p.country or '-'} / id:{p.id}": p.id for p in persons}
sel = st.selectbox("Select a person", options=list(options.keys()))
person_id = options[sel] if sel else None

uploaded_files = st.file_uploader(
    "Image files (multiple allowed)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
)
caption = st.text_input("Common caption (optional; applied to each image)")

if st.button("Upload"):
    if not person_id:
        st.error("Please select a person.")
    elif not uploaded_files:
        st.error("Please select file(s).")
    else:
        saved = 0
        with SessionLocal() as sess:
            for uf in uploaded_files:
                raw = uf.read()
                out_path = save_photo_bytes(person_id, uf.name, raw)
                add_photo(sess, person_id, out_path, caption)
                saved += 1
        st.success(f"Registered {saved} image(s).")

st.divider()
st.caption("Preview of registered photos (first 12)")
if person_id:
    with SessionLocal() as sess:
        p = sess.get(Person, person_id)
        if p and p.photos:
            for ph in p.photos[:12]:
                st.image(ph.file_path, caption=ph.caption or "", use_column_width_width=True)
        else:
            st.caption("No photos available")
