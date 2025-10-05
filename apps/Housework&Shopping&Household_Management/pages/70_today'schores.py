# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db_kaji import (
    init_db, days_since_base, todays_chores,
    add_carryover, list_carryovers, complete_carryover,
    mark_done_today
)

st.set_page_config(page_title="Today's Chores", layout="wide")
init_db()

today = date.today()
today_str = today.strftime("%Y/%m/%d")
c1, c2 = st.columns([1,1])
st.write(f"{today_str}")
st.write(f"Days since 2025/09/07: {days_since_base(today)}")

st.markdown("### Today's Chores")
rows = todays_chores(today)
if not rows:
    st.caption("No chores scheduled for today.")
else:
    for chore_id, name, mod, remainder in rows:
        c1, c2, c3 = st.columns([4, 1.5, 1.5])
        with c1:
            st.write(f"{name} (mod={mod}, remainder={remainder})")
        with c2:
            if st.button("Mark as Done", key=f"done_{chore_id}"):
                mark_done_today(chore_id, today.strftime("%Y-%m-%d"))
                st.rerun()
        with c3:
            if st.button("Carry Over", key=f"carry_{chore_id}"):
                add_carryover(chore_id)
                st.rerun()

st.markdown("---")
st.markdown("### Carried-Over Chores")
carry = list_carryovers()
if not carry:
    st.caption("No chores currently carried over.")
else:
    for carry_id, chore_id, name, mod, remainder in carry:
        c1, c2 = st.columns([5, 1.5])
        with c1:
            st.write(f"{name} (mod={mod}, remainder={remainder})")
        with c2:
            if st.button("Mark as Done", key=f"carry_done_{carry_id}"):
                complete_carryover(carry_id)
                st.rerun()
