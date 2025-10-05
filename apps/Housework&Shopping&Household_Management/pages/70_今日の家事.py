# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db_kaji import (
    init_db, days_since_base, todays_chores,
    add_carryover, list_carryovers, complete_carryover,
    mark_done_today
)

st.set_page_config(page_title="今日の家事", layout="wide")
init_db()


today = date.today()
today_str = today.strftime("%Y/%m/%d")
c1,c2 = st.columns([1,1])
st.write(f"{today_str}")
st.write(f"2025/09/07 からの経過日数：{days_since_base(today)}")

st.markdown("### 今日の家事")
rows = todays_chores(today)
if not rows:
    st.caption("本日該当はありません。")
else:
    for chore_id, name, mod, remainder in rows:
        c1, c2, c3 = st.columns([4, 1.5, 1.5])
        with c1:
            st.write(f"{name}（mod={mod}, 余り={remainder}）")
        with c2:
            if st.button("完了にする", key=f"done_{chore_id}"):
                mark_done_today(chore_id, today.strftime("%Y-%m-%d"))
                st.rerun()
        with c3:
            if st.button("繰越", key=f"carry_{chore_id}"):
                add_carryover(chore_id)
                st.rerun()

st.markdown("---")
st.markdown("### 繰越家事")
carry = list_carryovers()
if not carry:
    st.caption("繰越中の家事はありません。")
else:
    for carry_id, chore_id, name, mod, remainder in carry:
        c1, c2 = st.columns([5, 1.5])
        with c1:
            st.write(f"{name}（mod={mod}, 余り={remainder}）")
        with c2:
            if st.button("完了にする", key=f"carry_done_{carry_id}"):
                complete_carryover(carry_id)
                st.rerun()
