import streamlit as st
from db import init_db, SessionLocal, Person
from utils import save_photo_bytes, add_photo

init_db()
st.title("写真アップロード")

with SessionLocal() as sess:
    persons = sess.query(Person).order_by(Person.name.asc()).all()

options = {f"{p.name} / {p.country or '-'} / id:{p.id}": p.id for p in persons}
sel = st.selectbox("人物を選択", options=list(options.keys()))
person_id = options[sel] if sel else None

uploaded_files = st.file_uploader("画像ファイル（複数可）", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
caption = st.text_input("共通キャプション（任意、各画像に同じ説明を付与）")

if st.button("アップロード"):
    if not person_id:
        st.error("人物を選択してください。")
    elif not uploaded_files:
        st.error("ファイルを選択してください。")
    else:
        saved = 0
        with SessionLocal() as sess:
            for uf in uploaded_files:
                raw = uf.read()
                out_path = save_photo_bytes(person_id, uf.name, raw)
                add_photo(sess, person_id, out_path, caption)
                saved += 1
        st.success(f"{saved}件の画像を登録しました。")

st.divider()
st.caption("登録済み写真プレビュー（先頭12件）")
if person_id:
    with SessionLocal() as sess:
        p = sess.get(Person, person_id)
        if p and p.photos:
            for ph in p.photos[:12]:
                st.image(ph.file_path, caption=ph.caption or "", use_container_width=True)
        else:
            st.caption("写真なし")
