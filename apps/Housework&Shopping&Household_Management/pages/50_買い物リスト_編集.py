# -*- coding: utf-8 -*-
import streamlit as st
from db_sl import (
    init_db, list_genres, ensure_genre, update_genre_name, delete_genre,
    list_items_by_genre, ensure_item, update_item_name, delete_item
)

st.set_page_config(page_title="リスト編集", layout="wide")
init_db()

tab_genre, tab_item = st.tabs(["ジャンル", "品目"])

with tab_genre:
    st.markdown("### ジャンルの追加")
    with st.form("genre_add"):
        gname = st.text_input("ジャンル名")
        submitted = st.form_submit_button("追加")
        if submitted:
            try:
                gid = ensure_genre(gname)
                st.success(f"追加: {gname} (id={gid})")
            except Exception as e:
                st.error(str(e))

    st.markdown("### ジャンルの編集/削除")
    genres = list_genres()
    if not genres:
        st.caption("ジャンルがありません。")
    else:
        sel = st.selectbox("編集対象", options=genres, format_func=lambda x: x[1], key="genre_sel")
        if sel:
            gid, gname_cur = sel
            new_name = st.text_input("新しい名前", value=gname_cur, key="genre_new")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("名前を更新"):
                    try:
                        update_genre_name(gid, new_name)
                        st.success("更新しました。ページを再読み込みしてください。")
                    except Exception as e:
                        st.error(str(e))
            with col2:
                if st.button("このジャンルを削除", type="primary"):
                    try:
                        delete_genre(gid)
                        st.success("削除しました。ページを再読み込みしてください。")
                    except Exception as e:
                        st.error(str(e))

with tab_item:
    genres = list_genres()
    if not genres:
        st.caption("まずジャンルを作成してください。")
    else:
        st.markdown("### 品目の追加")
        sel_g = st.selectbox("所属ジャンル", options=genres, format_func=lambda x: x[1], key="item_add_gid")
        iname = st.text_input("品目名")
        if st.button("品目を追加"):
            try:
                iid = ensure_item(sel_g[0], iname)
                st.success(f"追加: {sel_g[1]} / {iname} (id={iid})")
            except Exception as e:
                st.error(str(e))

        st.markdown("### 品目の編集/削除")
        sel_g2 = st.selectbox("ジャンル選択", options=genres, format_func=lambda x: x[1], key="item_edit_gid")
        q = st.text_input("検索（部分一致）", key="item_search")
        items = list_items_by_genre(sel_g2[0])
        if q.strip():
            items = [x for x in items if q.lower() in x[1].lower()]
        if not items:
            st.caption("該当品目がありません。")
        else:
            sel_item = st.selectbox("対象品目", options=items, format_func=lambda x: x[1], key="item_sel")
            if sel_item:
                iid, iname_cur = sel_item
                new_iname = st.text_input("新しい名前", value=iname_cur, key="item_newname")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("品目名を更新"):
                        try:
                            update_item_name(iid, new_iname)
                            st.success("更新しました。ページを再読み込みしてください。")
                        except Exception as e:
                            st.error(str(e))
                with col2:
                    if st.button("この品目を削除", type="primary"):
                        try:
                            delete_item(iid)
                            st.success("削除しました。ページを再読み込みしてください。")
                        except Exception as e:
                            st.error(str(e))
