# -*- coding: utf-8 -*-
import streamlit as st
from db_kaji import init_db, ensure_chore, list_chores, update_chore, delete_chore

st.set_page_config(page_title="家事の編集", layout="wide")
init_db()

st.markdown("#### 家事追加")
with st.form("add_form"):
    name = st.text_input("家事の名前")
    mod = st.number_input("mod", min_value=1, step=1, value=7)
    remainder = st.number_input("余り", min_value=0, step=1, value=0)
    submitted = st.form_submit_button("追加")
    if submitted:
        try:
            if remainder >= mod:
                st.error("余りは 0 以上 mod 未満にしてください。")
            else:
                cid = ensure_chore(name, int(mod), int(remainder))
                st.success(f"追加しました（id={cid}）。")
        except Exception as e:
            st.error(str(e))

st.markdown("---")
st.markdown("#### 家事編集・削除")

chores = list_chores()
if not chores:
    st.caption("家事が登録されていません。")
else:
    sel = st.selectbox("家事を選ぶ", options=chores, format_func=lambda x: x[1])
    if sel:
        cid, cur_name, cur_mod, cur_rem = sel
        new_name = st.text_input("名前", value=cur_name, key=f"nm_{cid}")
        new_mod = st.number_input("mod", min_value=1, step=1, value=int(cur_mod), key=f"md_{cid}")
        new_rem = st.number_input("余り", min_value=0, step=1, value=int(cur_rem), key=f"rm_{cid}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("更新", key=f"upd_{cid}"):
                try:
                    if int(new_rem) >= int(new_mod):
                        st.error("余りは 0 以上 mod 未満にしてください。")
                    else:
                        update_chore(cid, new_name, int(new_mod), int(new_rem))
                        st.success("更新しました。ページを再読み込みしてください。")
                except Exception as e:
                    st.error(str(e))
        with c2:
            if st.button("削除", key=f"del_{cid}"):
                try:
                    delete_chore(cid)
                    st.success("削除しました。ページを再読み込みしてください。")
                except Exception as e:
                    st.error(str(e))
