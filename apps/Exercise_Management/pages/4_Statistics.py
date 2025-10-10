# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from config import GOAL_METS_MIN_PER_DAY
from utils import (
    compute_binned_totals, plot_line_with_goal, summarize_by_item,
    plot_pie_goaltile, plot_bar_top_items, load_daily_totals, daterange_days
)

st.set_page_config(page_title="Statistics", layout="centered")

TAB_TREND, TAB_BREAK, TAB_TABLE = st.tabs(["Trend", "Breakdown", "Table"])

# ----- Tab: Trend -----
with TAB_TREND:
    c1, c2, c3 = st.columns(3)
    with c1:
        start = st.date_input("Start date", value=date(2025, 9, 27), format="YYYY-MM-DD")
    with c2:
        end = st.date_input("End date", value=date.today(), format="YYYY-MM-DD")
    with c3:
        window = st.number_input("Window size (days)", min_value=1, max_value=60, step=1, value=1)

    if start > end:
        st.warning("The start date is later than the end date.")
    else:
        df = compute_binned_totals(start, end, int(window))
        st.caption(f"Goal (per day): {GOAL_METS_MIN_PER_DAY} METs·min")
        fig = plot_line_with_goal(df, int(window))
        st.pyplot(fig, clear_figure=True)

# ----- Tab: Breakdown -----
with TAB_BREAK:
    c1, c2 = st.columns(2)
    with c1:
        start_b = st.date_input("Start date (breakdown)", value=date(2025, 9, 27), format="YYYY-MM-DD", key="bstart")
    with c2:
        end_b = st.date_input("End date (breakdown)", value=date.today(), format="YYYY-MM-DD", key="bend")

    if start_b > end_b:
        st.warning("The start date is later than the end date.")
    else:
        days = daterange_days(start_b, end_b)
        df_item = summarize_by_item(start_b, end_b)

        left, right = st.columns([1, 1])
        with left:
            cols = st.slider("Number of tiles per row", min_value=2, max_value=8, value=4, step=1)
            fig_tiles = plot_pie_goaltile(df_item[["name", "mets_min"]].copy(), days, cols=cols)
            st.pyplot(fig_tiles, clear_figure=True)
        with right:
            fig_bar = plot_bar_top_items(df_item[["name", "mets_min"]].copy())
            st.pyplot(fig_bar, clear_figure=True)

# ----- Tab: Table -----
with TAB_TABLE:
    df_daily = load_daily_totals(start_b, end_b)
    st.dataframe(df_daily, use_container_width=True)
