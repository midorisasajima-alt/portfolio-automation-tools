import streamlit as st
from datetime import date
from db import init_db, SessionLocal
from utils import upsert_person

init_db()
st.title("追加")

with st.form("add_form", clear_on_submit=True):
    name = st.text_input("名前*", max_chars=200)
    instagram = st.text_input("Instagram")
    whatsapp = st.text_input("WhatsApp")
    linkedin = st.text_input("LinkedIn")
    country = st.text_input("出身国")
    region = st.text_input("出身地域")
    work_history = st.text_area("職歴（自由記述）", height=120)
    birthday = st.date_input("誕生日", value=None, format="YYYY-MM-DD")
    residence = st.text_input("住んでいるところ")
    photo_album = st.text_input("写真集の情報")
    notes = st.text_area("メモ", height=120)
    submitted = st.form_submit_button("追加")

    if submitted:
        if not name.strip():
            st.error("名前は必須です。")
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
                st.success(f"追加しました（ID: {p.id}）")
