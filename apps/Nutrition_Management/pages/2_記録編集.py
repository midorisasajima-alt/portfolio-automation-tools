import streamlit as st
import pandas as pd
from datetime import date
from db import list_genres, list_records, list_items, update_record, delete_record

st.set_page_config(page_title="記録編集", layout="wide")

st.header("記録編集・削除")

colf = st.columns(3)
with colf[0]:
    d = st.date_input("日付で絞り込み", value=None, format="YYYY-MM-DD")
with colf[1]:
    meal = st.number_input("何食目で絞り込み (空=0)", min_value=0, max_value=10, step=1, value=0)
with colf[2]:
    genres = [""] + list_genres()
    g = st.selectbox("ジャンルで絞り込み", options=genres)

sel_date = d.isoformat() if d else None
sel_meal = meal if meal != 0 else None
sel_genre = g if g != "" else None

rows = list_records(date=sel_date, meal_index=sel_meal, genre=sel_genre)

if not rows:
    st.info("該当する記録がありません。")
else:
    for r in rows:
        with st.expander(f"{r['date']} / {r['meal_index']}食目 / {r['genre']} / {r['name']}"):
            c1, c2, c3, c4 = st.columns([1,1,2,1])
            with c1:
                new_date = st.date_input("日付", value=date.fromisoformat(r['date']), key=f"d_{r['id']}")
            with c2:
                new_meal = st.number_input("何食目", min_value=1, max_value=10, value=int(r['meal_index']), step=1, key=f"m_{r['id']}")
            with c3:
                # 品目変更
                all_items = list_items(genre=r['genre'])
                id2name = {it['id']: it['name'] for it in all_items}
                inv = {v:k for k,v in id2name.items()}
                current_name = id2name.get(r['item_id'], r['name'])
                new_name = st.selectbox("品目", options=list(id2name.values()), index=list(id2name.values()).index(current_name), key=f"it_{r['id']}")
                new_item_id = inv[new_name]
            with c4:
                new_qty = st.number_input("量", min_value=0.0, step=0.5, value=float(r['quantity']), key=f"q_{r['id']}")

            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("更新", key=f"upd_{r['id']}"):
                    if new_qty <= 0:
                        st.warning("量は正の数で入力してください。")
                    else:
                        update_record(r['id'], date=new_date.isoformat(), meal_index=int(new_meal), item_id=int(new_item_id), quantity=float(new_qty))
                        st.success("更新しました。ページを再読み込みすると反映されます。")
            with cc2:
                if st.button("削除", key=f"del_{r['id']}"):
                    delete_record(r['id'])
                    st.success("削除しました。ページを再読み込みすると反映されます。")
