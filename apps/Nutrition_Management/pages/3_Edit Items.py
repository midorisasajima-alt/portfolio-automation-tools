import streamlit as st
from db import list_genres, list_items, insert_item, update_item, delete_item, get_item

st.set_page_config(page_title="Edit Items", layout="wide")

st.header("Add / Edit / Delete Items")

TAB_ADD, TAB_EDIT = st.tabs(["Add Item", "Edit / Delete Items"])

with TAB_ADD:
    st.subheader("Add Item")
    genre = st.text_input("Category (e.g., Staples, Main dish, Snack, Beverage)")
    name = st.text_input("Item name")
    unit = st.text_input("Unit (e.g., piece, g, ml, cup)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        energy = st.number_input("Energy / unit", min_value=0.0, step=1.0)
    with c2:
        protein = st.number_input("Protein / unit", min_value=0.0, step=0.1)
    with c3:
        fat = st.number_input("Fat / unit", min_value=0.0, step=0.1)
    with c4:
        carb = st.number_input("Carbohydrate / unit", min_value=0.0, step=1.0)

    if st.button("Save"):
        if not (genre and name and unit):
            st.warning("Please enter category, item name, and unit.")
        else:
            insert_item({
                "genre": genre, "name": name, "unit": unit,
                "energy": energy, "protein": protein, "fat": fat, "carbohydrate": carb
            })
            st.success("Saved successfully.")

with TAB_EDIT:
    st.subheader("Edit / Delete Items")
    genres = [""] + list_genres()
    g = st.selectbox("Select category", options=genres)
    keyword = st.text_input("Search items (partial match)")

    items = list_items(keyword=keyword, genre=(g if g else None))
    if not items:
        st.info("No matching items found.")
    else:
        for it in items:
            with st.expander(f"{it['genre']} / {it['name']}"):
                ng = st.text_input("Category", value=it['genre'], key=f"g_{it['id']}")
                nm = st.text_input("Item name", value=it['name'], key=f"n_{it['id']}")
                un = st.text_input("Unit", value=it['unit'], key=f"u_{it['id']}")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    en = st.number_input("Energy / unit", min_value=0.0, step=1.0, value=float(it['energy']), key=f"e_{it['id']}")
                with c2:
                    pr = st.number_input("Protein / unit", min_value=0.0, step=0.1, value=float(it['protein']), key=f"p_{it['id']}")
                with c3:
                    ft = st.number_input("Fat / unit", min_value=0.0, step=0.1, value=float(it['fat']), key=f"f_{it['id']}")
                with c4:
                    ca = st.number_input("Carbohydrate / unit", min_value=0.0, step=1.0, value=float(it['carbohydrate']), key=f"c_{it['id']}")
                cta1, cta2 = st.columns(2)
                with cta1:
                    if st.button("Update", key=f"upd_item_{it['id']}"):
                        update_item(it['id'], {
                            "genre": ng, "name": nm, "unit": un,
                            "energy": en, "protein": pr, "fat": ft, "carbohydrate": ca
                        })
                        st.success("Updated successfully.")
                with cta2:
                    if st.button("Delete", key=f"del_item_{it['id']}"):
                        delete_item(it['id'])
                        st.success("Deleted successfully.")
