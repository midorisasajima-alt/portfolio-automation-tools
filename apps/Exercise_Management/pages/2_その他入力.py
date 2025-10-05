# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db import insert_activity
from utils import activity_mets_min

st.set_page_config(page_title="その他入力", layout="centered")


with st.form("form_activity"):
    d = st.date_input("日付", value=date.today(), format="YYYY-MM-DD")
    atype = st.text_input("運動の種類（例：ラン、バイク、筋トレ 等）", value="ラン")
    mets = st.number_input("METs（強度）", min_value=0.0, step=0.1, value=7.0, format="%.1f")
    minutes = st.number_input("分数", min_value=0.0, step=1.0, value=30.0, format="%.1f")
    preview = activity_mets_min(float(mets), float(minutes))
    st.info(f"参考：この入力は 約 {preview:.1f} METs・分")

    submitted = st.form_submit_button("保存")
    if submitted:
        rec_id = insert_activity(d.strftime("%Y-%m-%d"), atype.strip() or "種目", float(mets), float(minutes))
        st.success(f"保存しました（ID: {rec_id}）")
