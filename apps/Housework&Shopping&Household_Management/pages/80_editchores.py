# -*- coding: utf-8 -*-
import streamlit as st
from db_kaji import init_db, ensure_chore, list_chores, update_chore, delete_chore

st.set_page_config(page_title="Edit Chores", layout="wide")
init_db()

st.markdown("#### Add New Chore")
with st.form("add_form"):
    name = st.text_input("Chore Name")
    mod = st.number_input("mod", min_value=1, step=1, value=7)
    remainder = st.number_input("remainder", min_value=0, step=1, value=0)
    submitted = st.form_submit_button("Add")
    if submitted:
        try:
            if remainder >= mod:
                st.error("Remainder must be between 0 (inclusive) and mod (exclusive).")
            else:
                cid = ensure_chore(name, int(mod), int(remainder))
                st.success(f"Added successfully (id={cid}).")
        except Exception as e:
            st.error(str(e))

st.markdown("---")
st.markdown("#### Edit / Delete Chore")

chores = list_chores()
if not chores:
    st.caption("No chores have been registered.")
else:
    sel = st.selectbox("Select a chore", options=chores, format_func=lambda x: x[1])
    if sel:
        cid, cur_name, cur_mod, cur_rem = sel
        new_name = st.text_input("Name", value=cur_name, key=f"nm_{cid}")
        new_mod = st.number_input("mod", min_value=1, step=1, value=int(cur_mod), key=f"md_{cid}")
        new_rem = st.number_input("remainder", min_value=0, step=1, value=int(cur_rem), key=f"rm_{cid}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Update", key=f"upd_{cid}"):
                try:
                    if int(new_rem) >= int(new_mod):
                        st.error("Remainder must be between 0 (inclusive) and mod (exclusive).")
                    else:
                        update_chore(cid, new_name, int(new_mod), int(new_rem))
                        st.success("Updated successfully. Please reload the page.")
                except Exception as e:
                    st.error(str(e))
        with c2:
            if st.button("Delete", key=f"del_{cid}"):
                try:
                    delete_chore(cid)
                    st.success("Deleted successfully. Please reload the page.")
                except Exception as e:
                    st.error(str(e))
