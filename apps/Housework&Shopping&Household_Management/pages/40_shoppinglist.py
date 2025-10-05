# -*- coding: utf-8 -*-
import streamlit as st
from db_sl import (
    init_db, list_genres, list_items_by_genre, get_state, set_to_buy, list_to_buy_by_genre
)

st.set_page_config(page_title="Shopping List", layout="wide")
init_db()

genres = list_genres()
if not genres:
    st.info("Please create genres/items first in 'Edit List'.")
    st.stop()

# Upper section: tabs by genre + checkboxes (instant update)
tabs = st.tabs([gname for (_, gname) in genres])
for tab, (gid, gname) in zip(tabs, genres):
    with tab:
        items = list_items_by_genre(gid)
        if not items:
            st.caption("No items. Please add them in 'Edit List'.")
        else:
            for iid, iname in items:
                checked, _memo = get_state(iid)
                new_val = st.checkbox(iname, value=bool(checked), key=f"chk_{gid}_{iid}")
                if new_val != bool(checked):
                    set_to_buy(iid, new_val)

# Lower section: text output (left = item names only, right = item + memo)
st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.text("Things to buy (by genre, item names only)")
    txt_lines = []
    for gid, gname in genres:
        rows = list_to_buy_by_genre(gid)
        if rows:
            txt_lines.append(f"[{gname}]")
            for iid, iname, memo in rows:
                txt_lines.append(f"- {iname}")
            txt_lines.append("")
    st.text_area("For copy", value="\n".join(txt_lines), height=240, key="copy_plain")

with col_right:
    st.text("Things to buy (by genre, item + memo)")
    txt_lines = []
    for gid, gname in genres:
        rows = list_to_buy_by_genre(gid)
        if rows:
            txt_lines.append(f"[{gname}]")
            for iid, iname, memo in rows:
                line = f"- {iname}"
                if memo.strip():
                    line += f": {memo.strip()}"
                txt_lines.append(line)
            txt_lines.append("")
    st.text_area("For copy", value="\n".join(txt_lines), height=240, key="copy_with_memo")
