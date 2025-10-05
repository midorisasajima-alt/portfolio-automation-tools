import streamlit as st
import pandas as pd
from datetime import date
from db import list_genres, list_items_by_genre, insert_record

st.set_page_config(page_title="Record", layout="wide")

st.header("Record Entry")

col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Date", value=date.today(), format="YYYY-MM-DD")
with col2:
    meal = st.number_input("Meal number", min_value=1, max_value=10, step=1, value=1)

genres = list_genres()
if not genres:
    st.info("Please register items first in 'Edit Items'.")
else:
    tabs = st.tabs(genres)
    for gi, g in enumerate(genres):
        with tabs[gi]:
            items = list_items_by_genre(g)
            if not items:
                st.write("No items registered in this category.")
                continue
            for row in items:
                with st.expander(f"{row['name']} (Unit: {row['unit']})"):
                    st.write(f"Energy {row['energy']} / Protein {row['protein']} / Fat {row['fat']} / Carbohydrate {row['carbohydrate']}")
                    qty = st.number_input(
                        f"Amount ({row['unit']}) - {row['name']}",
                        min_value=0.0,
                        step=0.5,
                        key=f'qty_{row["id"]}'
                    )
                    if st.button("Save", key=f'save_{row["id"]}'):
                        if qty <= 0:
                            st.warning("Please enter a positive value for the amount.")
                        else:
                            insert_record(d.isoformat(), int(meal), int(row["id"]), float(qty))
                            st.success("Saved successfully.")
