import streamlit as st
from datetime import date
from sqlalchemy import func
from db import init_db, SessionLocal, Person
from utils import upsert_person, delete_person

init_db()
st.set_page_config(page_title="編集・削除（検索対応）", layout="wide")
st.title("編集・削除")

# --- 検索UI ---
name_q = st.text_input("名前で検索（部分一致）", value="")
country_q = st.text_input("国で検索（部分一致）", value="")
notes_q = st.text_input("メモ内を部分検索（大文字小文字を無視）", value="")

if "edit_search_trigger" not in st.session_state:
    st.session_state["edit_search_trigger"] = False

if st.button("検索"):
    st.session_state["edit_search_trigger"] = True

# --- データ取得（検索適用） ---
with SessionLocal() as sess:
    q = sess.query(Person)
    if st.session_state.get("edit_search_trigger"):
        if name_q.strip():
            q = q.filter(Person.name.ilike(f"%{name_q.strip()}%"))
        if country_q.strip():
            q = q.filter(Person.country.ilike(f"%{country_q.strip()}%"))
        if notes_q.strip():
            # SQLite対応：COALESCE(notes, '') を小文字化して LIKE
            q = q.filter(
                func.lower(func.coalesce(Person.notes, "")).like(f"%{notes_q.strip().lower()}%")
            )
    persons = q.order_by(Person.name.asc()).all()

if not persons:
    st.info("該当する人物がいません。検索条件を調整してください。")
    st.stop()

options = {f"{p.name} / {p.country or '-'} / id:{p.id}": p.id for p in persons}
sel = st.selectbox("人物を選択", options=list(options.keys()))
person_id = options[sel] if sel else None

if person_id:
    with SessionLocal() as sess:
        p = sess.get(Person, person_id)

    with st.form("edit_form"):
        name = st.text_input("名前*", value=p.name or "")
        instagram = st.text_input("Instagram", value=p.instagram or "")
        whatsapp = st.text_input("WhatsApp", value=p.whatsapp or "")
        linkedin = st.text_input("LinkedIn", value=p.linkedin or "")
        country = st.text_input("出身国", value=p.country or "")
        region = st.text_input("出身地域", value=p.region or "")
        work_history = st.text_area("職歴（自由記述）", value=p.work_history or "", height=120)
        birthday = st.date_input("誕生日", value=p.birthday)
        residence = st.text_input("住んでいるところ", value=p.residence or "")
        photo_album = st.text_input("写真集の情報", value=p.photo_album or "")
        notes = st.text_area("メモ", value=p.notes or "", height=120)

        colu1, colu2 = st.columns(2)
        with colu1:
            saved = st.form_submit_button("保存")
        with colu2:
            deleted = st.form_submit_button("削除", use_container_width=True)

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
            st.success("保存しました。")
            st.rerun()

        if deleted:
            with SessionLocal() as sess:
                delete_person(sess, p.id)
            st.success("削除しました。")
            st.rerun()
