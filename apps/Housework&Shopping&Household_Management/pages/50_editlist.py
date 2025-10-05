# -*- coding: utf-8 -*-
import streamlit as st
from db_sl import (
    init_db, list_genres, ensure_genre, update_genre_name, delete_genre,
    list_items_by_genre, ensure_item, update_item_name, delete_item
)

st.set_page_config(page_title="List Editor", layout="wide")
init_db()

tab_genre, tab_item = st.tabs(["Genres", "Items"])

with tab_genre:
    st.markdown("### Add Genre")
    with st.form("genre_add"):
        gname = st.text_input("Genre Name")
        submitted = st.form_submit_button("Add")
        if submitted:
            try:
                gid = ensure_genre(gname)
                st.success(f"Added: {gname} (id={gid})")
            except Exception as e:
                st.error(str(e))

    st.markdown("### Edit/Delete Genre")
    genres = list_genres()
    if not genres:
        st.caption("No genres available.")
    else:
        sel = st.selectbox("Select Genre", options=genres, format_func=lambda x: x[1], key="genre_sel")
        if sel:
            gid, gname_cur = sel
            new_name = st.text_input("New Name", value=gname_cur, key="genre_new")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Name"):
                    try:
                        update_genre_name(gid, new_name)
                        st.success("Updated. Please reload the page.")
                    except Exception as e:
                        st.error(str(e))
            with col2:
                if st.button("Delete This Genre", type="primary"):
                    try:
                        delete_genre(gid)
                        st.success("Deleted. Please reload the page.")
                    except Exception as e:
                        st.error(str(e))

with tab_item:
    genres = list_genres()
    if not genres:
        st.caption("Please create a genre first.")
    else:
        st.markdown("### Add Item")
        sel_g = st.selectbox("Belonging Genre", options=genres, format_func=lambda x: x[1], key="item_add_gid")
        iname = st.text_input("Item Name")
        if st.button("Add Item"):
            try:
                iid = ensure_item(sel_g[0], iname)
                st.success(f"Added: {sel_g[1]} / {iname} (id={iid})")
            except Exception as e:
                st.error(str(e))

        st.markdown("### Edit/Delete Item")
        sel_g2 = st.selectbox("Select Genre", options=genres, format_func=lambda x: x[1], key="item_edit_gid")
        q = st.text_input("Search (partial match)", key="item_search")
        items = list_items_by_genre(sel_g2[0])
        if q.strip():
            items = [x for x in items if q.lower() in x[1].lower()]
        if not items:
            st.caption("No matching items found.")
        else:
            sel_item = st.selectbox("Select Item", options=items, format_func=lambda x: x[1], key="item_sel")
            if sel_item:
                iid, iname_cur = sel_item
                new_iname = st.text_input("New Name", value=iname_cur, key="item_newname")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Item Name"):
                        try:
                            update_item_name(iid, new_iname)
                            st.success("Updated. Please reload the page.")
                        except Exception as e:
                            st.error(str(e))
                with col2:
                    if st.button("Delete This Item", type="primary"):
                        try:
                            delete_item(iid)
                            st.success("Deleted. Please reload the page.")
                        except Exception as e:
                            st.error(str(e))
