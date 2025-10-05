import streamlit as st
from sqlalchemy.orm import Session
from db import init_db, SessionLocal, Person
from utils import search_persons

# 初期化
init_db()
st.set_page_config(page_title="表示（検索・閲覧）", layout="wide")
st.title("表示（検索・閲覧）")

# 入力UI
name_q = st.text_input("名前で検索（部分一致）", value="")
country_q = st.text_input("国で検索（部分一致）", value="")
notes_q = st.text_input("メモ内を部分検索（大文字小文字を無視）", value="")

# 検索トリガの既定値を確保
if "search_trigger" not in st.session_state:
    st.session_state["search_trigger"] = False

if st.button("検索"):
    st.session_state["search_trigger"] = True

# 検索実行
if st.session_state.get("search_trigger"):
    with SessionLocal() as sess:
        rows = search_persons(sess, name_q=name_q, country_q=country_q)

        # メモ内部分一致フィルタ（クライアント側）
        nq = notes_q.strip().lower()
        if nq:
            rows = [p for p in rows if nq in (p.notes or "").lower()]

        st.write(f"件数：{len(rows)}")

        for p in rows:
            with st.expander(f"{p.name}（{p.country or '-'}）", expanded=True):  # 既定で開く
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.text(f"Instagram: {p.instagram or ''}")
                    st.text(f"WhatsApp:  {p.whatsapp or ''}")
                    st.text(f"LinkedIn:  {p.linkedin or ''}")
                    st.text(f"地域:      {p.region or ''}")
                    st.text(f"現住所:    {p.residence or ''}")
                    st.text(f"誕生日:    {p.birthday.isoformat() if p.birthday else ''}")
                    st.text(f"職歴:      {p.work_history or ''}")
                    st.text(f"写真集:    {p.photo_album or ''}")
                    st.text(f"メモ:      {p.notes or ''}")
                with col2:
                    if p.photos:
                        for ph in p.photos[:6]:
                            st.image(ph.file_path, caption=ph.caption or "", use_container_width=True)
                    else:
                        st.caption("写真なし")
