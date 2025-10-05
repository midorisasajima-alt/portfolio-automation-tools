# =============================
# pages/11_生活時間.py
# -----------------------------
import streamlit as st
from db import insert_routine, list_routine, update_routine, delete_routine

st.title("11) 生活時間（定期ルーチン）")

mode = st.tabs(["追加", "編集・削除"])

with mode[0]:
    with st.form("routine_add"):
        title = st.text_input("やることのタイトル（例：睡眠、食事、移動 など）")
        hrs = st.number_input("かかる時間（h/1回）", min_value=0.0, step=0.5)
        period = st.number_input("何日周期か", min_value=1, value=1)
        submitted = st.form_submit_button("追加")
        if submitted:
            insert_routine(title, float(hrs), int(period))
            st.success("追加しました。")

with mode[1]:
    rts = list_routine()
    for r in rts:
        with st.form(f"edit_{r['id']}"):
            title = st.text_input("タイトル", r['title'])
            hrs = st.number_input("かかる時間（h/1回）", min_value=0.0, step=0.5, value=float(r['hours']))
            period = st.number_input("何日周期か", min_value=1, value=int(r['period_days']))
            col1, col2 = st.columns(2)
            with col1:
                saved = st.form_submit_button("保存")
            with col2:
                removed = st.form_submit_button("削除")
        if saved:
            update_routine(r['id'], title, float(hrs), int(period))
            st.success("保存しました。")
        if removed:
            delete_routine(r['id'])
            st.success("削除しました。")
