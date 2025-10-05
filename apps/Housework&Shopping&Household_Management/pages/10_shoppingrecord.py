import streamlit as st
from datetime import date
from db import (
    init_db, seed_minimal, list_genres, list_items_by_genre,
    list_stores, list_payments, ensure_store, ensure_payment,
    insert_purchase, ensure_item
)

st.set_page_config(page_title="Shopping Record", layout="wide")

init_db()
seed_minimal()

def name_id_map(pairs):
    return {name: _id for (_id, name) in pairs}

genres = list_genres()
if not genres:
    st.error("No genres found. Please edit 'seed_minimal' in db.py.")
    st.stop()

tab_labels = [g[1] for g in genres]
tabs = st.tabs(tab_labels)

for tab, (genre_id, genre_name) in zip(tabs, genres):
    with tab:

        # --- Search & Select (side by side) ---
        items = list_items_by_genre(genre_id)  # [(id, name, unit)]
        c1, c2 = st.columns([1, 2])
        with c1:
            q = st.text_input("Search (partial match for item name)", key=f"search_{genre_id}")
        filtered = [(iid, name, unit) for (iid, name, unit) in items if (q in name) or not q]

        with c2:
            if filtered:
                labels = [f"{name} ({unit})" for (_, name, unit) in filtered]
                idx = st.selectbox(
                    "Item (unit)",
                    options=list(range(len(filtered))),
                    format_func=lambda i: labels[i],
                    key=f"item_sel_{genre_id}"
                )
                item_id = filtered[idx][0]
                unit = filtered[idx][2]
            else:
                st.info("No matches found. You can add a new item below.")
                item_id = None
                unit = ""

        # --- Add new item ---
        with st.expander("Add new item (click to open)", expanded=True):
            st.caption("Create a new item under this genre.")

            a1, a2, a3 = st.columns([2, 1, 1])
            with a1:
                new_item_name = st.text_input("New item name", key=f"new_item_name_{genre_id}")
            with a2:
                new_item_unit = st.text_input("New unit", key=f"new_item_unit_{genre_id}")
            with a3:
                add_clicked = st.button("Add", key=f"add_item_{genre_id}")

            if add_clicked:
                try:
                    new_id = ensure_item(genre_id, new_item_name, new_item_unit)
                    st.success(f"Added: {new_item_name} ({new_item_unit})")
                    item_id = new_id
                    unit = new_item_unit
                except Exception as e:
                    st.error(f"Failed to add item: {e}")

        # --- Date / Store / Quantity / Total / Payment ---
        d = st.date_input("Date", value=date.today(), key=f"date_{genre_id}")

        stores = list_stores()
        store_names = [s[1] for s in stores]
        store_name_to_id = name_id_map(stores)
        store_choice = st.selectbox(
            "Store name (select)",
            ["(Please select)"] + store_names + ["＋ Add new store"],
            key=f"store_sel_{genre_id}"
        )
        store_id = None
        if store_choice == "＋ Add new store":
            new_store = st.text_input("New store name", key=f"store_new_{genre_id}")
            if new_store:
                store_id = ensure_store(new_store.strip())
        elif store_choice != "(Please select)":
            store_id = store_name_to_id.get(store_choice)

        qty = st.number_input(
            f"Quantity ({unit or 'unit not set'})",
            min_value=0.0, value=1.0, step=1.0,
            key=f"qty_{genre_id}"
        )
        total = st.number_input(
            "Total amount",
            min_value=0.0, value=0.0, step=1.0,
            key=f"total_{genre_id}"
        )

        payments = list_payments()
        pay_names = [p[1] for p in payments]
        pay_name_to_id = name_id_map(payments)
        pay_choice = st.selectbox("Payment method", pay_names, key=f"pay_{genre_id}")
        payment_id = pay_name_to_id.get(pay_choice)

        col_a, col_b = st.columns([1,1])
        with col_a:
            if qty > 0:
                st.caption(f"Unit price (auto-calculated): {(total / qty) if qty else 0:.2f} / {unit or '-'}")
            else:
                st.caption("Unit price cannot be calculated because quantity ≤ 0.")
        with col_b:
            submitted = st.button("Save", key=f"submit_{genre_id}")

        if submitted:
            if not item_id:
                st.error("Please select or add an item first.")
            elif not store_id:
                st.error("Please select or add a store.")
            elif qty <= 0:
                st.error("Quantity must be a positive number.")
            else:
                try:
                    insert_purchase(
                        item_id=item_id,
                        date_iso=d.isoformat(),
                        store_id=store_id,
                        qty=qty,
                        total=total,
                        payment_id=payment_id,
                    )
                    st.success("Saved successfully. Monthly & genre summaries updated.")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
