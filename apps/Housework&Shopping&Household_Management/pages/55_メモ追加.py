# -*- coding: utf-8 -*-
import streamlit as st
from db_sl import (
    init_db, list_genres, list_items_by_genre, search_items, get_state, set_memo
)

st.set_page_config(page_title="メモ追加", layout="wide")
init_db()

genres = list_genres()
if not genres:
    st.info("まず『リスト編集』でジャンル/品目を作成してください。")
    st.stop()

tabs = st.tabs([gname for (_, gname) in genres])

for tab, (gid, gname) in zip(tabs, genres):
    with tab:

        col_find, col_edit = st.columns([1,1])

        with col_find:
            q = st.text_input("検索語（任意）", key=f"q_{gid}")
            if q.strip():
                candidates = search_items(q, genre_id=gid)
                options = [(iid, nm) for (iid, _gid, nm) in candidates]
            else:
                options = list_items_by_genre(gid)
            sel = st.selectbox("品目", options=options, format_func=lambda x: x[1], key=f"sel_{gid}")

        with col_edit:
            if sel:
                iid, iname = sel
                _checked, memo_cur = get_state(iid)
                new_memo = st.text_area("メモ", value=memo_cur, height=120, key=f"memo_{iid}")
                if st.button("保存", key=f"save_{iid}"):
                    try:
                        set_memo(iid, new_memo)
                        st.success("保存しました。")
                    except Exception as e:
                        st.error(str(e))
