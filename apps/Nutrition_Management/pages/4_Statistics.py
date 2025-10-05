import streamlit as st
import pandas as pd
from datetime import date
from config import NUTRIENTS
from utils import compute_binned_totals, plot_line_with_goal, summarize_by_item, plot_pie_breakdown, plot_bar_top_items, daterange_days


st.header("Statistics")

TAB_TREND, TAB_BREAK = st.tabs(["Trends", "Breakdown"])

with TAB_TREND:
    st.subheader("Trends")
    c1, c2, c3 = st.columns(3)
    with c1:
        start = st.date_input("Period start date", value=date(2025, 9, 14), format="YYYY-MM-DD")
    with c2:
        end = st.date_input("Period end date", value=date.today(), format="YYYY-MM-DD")
    with c3:
        window = st.number_input("Window size (days)", min_value=1, max_value=60, step=1, value=1)

    if start > end:
        st.warning("The start date exceeds the end date.")
    else:
        df = compute_binned_totals(start, end, int(window))
        ntabs = st.tabs(NUTRIENTS)
        for i, nut in enumerate(NUTRIENTS):
            with ntabs[i]:
                fig = plot_line_with_goal(df, nut, int(window))
                st.pyplot(fig, clear_figure=True)

with TAB_BREAK:
    st.subheader("Breakdown")
    c1, c2 = st.columns(2)
    with c1:
        start_b = st.date_input("Period start date", value=date.today(), format="YYYY-MM-DD", key="bstart")
    with c2:
        end_b = st.date_input("Period end date", value=date.today(), format="YYYY-MM-DD", key="bend")

    if start_b > end_b:
        st.warning("The start date exceeds the end date.")
    else:
        days = daterange_days(start_b, end_b)
        df_item = summarize_by_item(start_b, end_b)
        ntabs2 = st.tabs(NUTRIENTS)
        for i, nut in enumerate(NUTRIENTS):
            with ntabs2[i]:
                left, right = st.columns([1, 1])
                with right:
                    fig_bar = plot_bar_top_items(df_item[["name", nut]].copy(), nut)
                    st.pyplot(fig_bar, clear_figure=True)
                with left:
                    fig_pie = plot_pie_breakdown(df_item[["name", nut]].copy(), nut, days)
                    st.pyplot(fig_pie, clear_figure=True)
