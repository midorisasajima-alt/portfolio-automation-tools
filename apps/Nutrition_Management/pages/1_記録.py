import streamlit as st
import pandas as pd
from datetime import date
from db import list_genres, list_items_by_genre, insert_record

st.set_page_config(page_title="記録", layout="wide")

st.header("記録")

col1, col2 = st.columns(2)
with col1:
    d = st.date_input("日付", value=date.today(), format="YYYY-MM-DD")
with col2:
    meal = st.number_input("何食目", min_value=1, max_value=10, step=1, value=1)

genres = list_genres()
if not genres:
    st.info("まず『品目編集』で品目を登録してください。")
else:
    tabs = st.tabs(genres)
    for gi, g in enumerate(genres):
        with tabs[gi]:
            items = list_items_by_genre(g)
            if not items:
                st.write("このジャンルに品目はありません。")
                continue
            for row in items:
                with st.expander(f"{row['name']}（単位: {row['unit']}）"):
                    st.write(f"Energy {row['energy']} / Protein {row['protein']} / Fat {row['fat']} / Carbohydrate {row['carbohydrate']}")
                    qty = st.number_input(f"量（{row['unit']}単位） - {row['name']}", min_value=0.0, step=0.5, key=f"qty_{row['id']}")
                    if st.button("保存", key=f"save_{row['id']}"):
                        if qty <= 0:
                            st.warning("量は正の数で入力してください。")
                        else:
                            insert_record(d.isoformat(), int(meal), int(row['id']), float(qty))
                            st.success("保存しました。")
