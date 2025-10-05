# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db import insert_walking
from utils import walking_mets_min

st.set_page_config(page_title="歩数入力", layout="centered")


with st.form("form_walk"):
    d = st.date_input("日付", value=date.today(), format="YYYY-MM-DD")
    # 歩数（歩）
    steps = st.number_input(
        "歩数（歩）",
        min_value=0,
        step=100,
        value=6000
    )

    # 歩幅は cm/歩 で入力（内部で m/歩 に変換）
    step_len_cm = st.number_input(
        "歩幅（cm/歩）",
        min_value=30,  # 30–120 cm 程度が一般的
        max_value=120,
        step=1,
        value=70
    )

    # 速度は km/h で入力（内部で m/分 に変換）
    speed_kmh = st.number_input(
        "歩行速度（km/h）",
        min_value=1.0,   # 1–12 km/h を現実的な範囲に設定
        max_value=12.0,
        step=0.1,
        value=4.7,
        format="%.1f"
    )

    # 単位変換
    step_len_m = step_len_cm / 100.0            # m/歩
    speed_m_per_min = speed_kmh * 1000.0 / 60.0 # m/分

    # プレビュー（ACSM式に基づく）
    mets_min_preview = walking_mets_min(int(steps), float(step_len_m), float(speed_m_per_min))
    st.info(f"参考：この入力は 約 {mets_min_preview:.1f} METs・分")

    submitted = st.form_submit_button("保存")
    if submitted:
        rec_id = insert_walking(
            d.strftime("%Y-%m-%d"),
            int(steps),
            float(step_len_m),
            float(speed_m_per_min)
        )
        st.success(f"保存しました（ID: {rec_id}）")

