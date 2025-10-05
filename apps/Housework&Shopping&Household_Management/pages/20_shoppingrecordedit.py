import streamlit as st
from datetime import date
from db import (
    init_db, seed_minimal, list_genres, list_items_by_genre, list_stores, list_payments,
    ensure_store, update_purchase, delete_purchase,
    update_item_unit, change_item_genre, get_purchases_by_genre_item, delete_genre_and_update_summaries, get_purchases_filtered
)

st.set_page_config(page_title="Shopping Record Editor", layout="wide")

init_db()
seed_minimal()

def name_id_map(pairs):
    return {name: _id for (_id, name) in pairs}

genres = list_genres()
if not genres:
    st.error("No genres found.")
    st.stop()

tab_main, tab_reclass, tab_item_admin, tab_master, tab_edit = st.tabs(
    ["Edit/Delete Records", "Change Item Genre", "Edit/Delete Items", "Add Master Data", "Edit/Delete Master Data"]
)

with tab_main:
    t_genre_labels = [g[1] for g in genres]
    sub_tabs = st.tabs(t_genre_labels)

    stores = list_stores()
    store_name_to_id = name_id_map(stores)
    store_names = [s[1] for s in stores]

    payments = list_payments()
    pay_name_to_id = name_id_map(payments)
    pay_names = [p[1] for p in payments]

    for sub_tab, (genre_id, genre_name) in zip(sub_tabs, genres):
        with sub_tab:
            items = list_items_by_genre(genre_id)  # [(id, name, unit), ...]
            options = [None] + items

            # 1) Filter by item
            sel = st.selectbox(
                "Filter by item",
                options=options,
                format_func=lambda x: "(All)" if x is None else f"{x[1]}",
                key=f"filter_item_{genre_id}",
            )
            item_id = None if sel is None else sel[0]

            # 2) Filter by store
            store_filter_options = [("ALL", "(All)")] + [(sid, sname) for (sid, sname) in stores]
            store_sel = st.selectbox(
                "Filter by store",
                options=store_filter_options,
                format_func=lambda t: t[1],
                key=f"filter_store_{genre_id}",
            )
            store_id = None if store_sel[0] == "ALL" else store_sel[0]

            # 3) Optional date-range filter
            use_date = st.checkbox("Filter by date", value=False, key=f"filter_date_use_{genre_id}")
            start_iso = end_iso = None
            if use_date:
                from datetime import date, timedelta
                today = date.today()
                start_default = today.replace(day=1)
                dr = st.date_input(
                    "Date range",
                    value=(start_default, today),
                    key=f"filter_date_rng_{genre_id}"
                )
                if isinstance(dr, tuple) and len(dr) == 2:
                    start_iso = dr[0].isoformat()
                    end_iso = dr[1].isoformat()

            # Fetch with server-side filtering
            rows = get_purchases_filtered(
                genre_id=genre_id,
                item_id=item_id,
                store_id=store_id,
                start_date_iso=start_iso,
                end_date_iso=end_iso
            )

            if not rows:
                st.info("No matching records.")
            else:
                for (pid, iid, iname, unit, d, store_id_row, store_name, qty, total, unit_price, payment_id, payment_name) in rows:
                    with st.expander(f"{d} ｜ {iname} ｜ {store_name} ｜ {qty} {unit} ｜ Total {total} ｜ {payment_name}", expanded=False):
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c1:
                            new_date = st.date_input("Date", value=date.fromisoformat(d), key=f"date_{pid}")
                            new_qty = st.number_input(f"Quantity ({unit})", min_value=0.0, value=float(qty), step=1.0, key=f"qty_{pid}")
                        with c2:
                            new_total = st.number_input("Total amount", min_value=0.0, value=float(total), step=1.0, key=f"total_{pid}")
                            st.caption(f"Unit price: {(new_total/new_qty) if new_qty else 0:.2f} / {unit}")
                        with c3:
                            new_store = st.selectbox("Store", store_names, index=store_names.index(store_name) if store_name in store_names else 0, key=f"store_{pid}")
                            new_payment = st.selectbox("Payment method", pay_names, index=pay_names.index(payment_name) if payment_name in pay_names else 0, key=f"pay_{pid}")

                        colu1, colu2 = st.columns([1,1])
                        with colu1:
                            if st.button("Update", key=f"update_{pid}"):
                                try:
                                    update_purchase(
                                        purchase_id=pid,
                                        date_iso=new_date.isoformat(),
                                        store_id=store_name_to_id[new_store],
                                        qty=float(new_qty),
                                        total=float(new_total),
                                        payment_id=pay_name_to_id[new_payment],
                                    )
                                    st.success("Updated. (Summaries refreshed.)")
                                except Exception as e:
                                    st.error(f"Update failed: {e}")
                        with colu2:
                            if st.button("Delete item (this will remove all purchase records for this item)", key=f"del_{pid}", type="secondary"):
                                try:
                                    from db import delete_item_and_update_summaries
                                    delete_item_and_update_summaries(iid)
                                    st.success("Item deleted. Monthly-by-genre and payment-method summaries have been refreshed.")
                                except Exception as e:
                                    st.error(f"Deletion failed: {e}")

with tab_reclass:
    # Current genre -> item -> new genre
    scol1, scol2, scol3 = st.columns([1,2,1])
    with scol1:
        gidx = st.selectbox("Current genre", options=list(range(len(genres))), format_func=lambda i: genres[i][1], key="re_g")
        current_gid = genres[gidx][0]
    items = list_items_by_genre(current_gid)
    if not items:
        st.info("No items in this genre.")
    else:
        with scol2:
            labels = [f"{name}" for (_id, name, unit) in items]
            idx = st.selectbox("Item", options=list(range(len(items))), format_func=lambda i: labels[i], key="re_item")
            item_id = items[idx][0]
        with scol3:
            new_gidx = st.selectbox("New genre", options=list(range(len(genres))), format_func=lambda i: genres[i][1], key="re_newg")
            new_gid = genres[new_gidx][0]

        if st.button("Change genre"):
            try:
                change_item_genre(item_id, new_gid)
                st.success("Genre changed. (Summaries migrated.)")
            except Exception as e:
                st.error(f"Change failed: {e}")

with tab_master:
    # Add genre
    g1, g2 = st.columns([3,1])
    with g1:
        new_genre = st.text_input("New genre name")
    with g2:
        if st.button("Add genre", key="add_genre_btn"):
            try:
                from db import ensure_genre
                gid = ensure_genre(new_genre)
                st.success(f"Added genre: {new_genre}")
            except Exception as e:
                st.error(f"Add failed: {e}")

    st.markdown("---")
    # Add store
    s1, s2 = st.columns([3,1])
    with s1:
        new_store = st.text_input("New store name")
    with s2:
        if st.button("Add store", key="add_store_btn"):
            try:
                from db import ensure_store
                sid = ensure_store(new_store)
                st.success(f"Added store: {new_store}")
            except Exception as e:
                st.error(f"Add failed: {e}")

    st.markdown("---")
    # Add payment method
    p1, p2 = st.columns([3,1])
    with p1:
        new_payment = st.text_input("New payment method")
    with p2:
        if st.button("Add payment method", key="add_payment_btn"):
            try:
                from db import ensure_payment
                pid = ensure_payment(new_payment)
                st.success(f"Added payment method: {new_payment}")
            except Exception as e:
                st.error(f"Add failed: {e}")

with tab_edit:
    genres = list_genres()
    if not genres:
        st.info("No genres.")
    else:
        g_sel = st.selectbox("Target genre", options=genres, format_func=lambda g: g[1], key="edit_genre_sel")
        new_gname = st.text_input("New genre name", value=g_sel[1], key="edit_genre_name")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("Update genre name", key="btn_update_genre"):
                try:
                    from db import update_genre_name
                    update_genre_name(g_sel[0], new_gname)
                    st.success("Genre name updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
        with c2:
            if st.button("Delete genre (delete all subordinate data)", key="btn_delete_genre"):
                try:
                    delete_genre_and_update_summaries(g_sel[0])
                    st.success(f'Deleted genre "{g_sel[1]}". Related data have been reconciled.')
                    st.rerun()
                except Exception as e:
                    st.error(f"Deletion failed: {e}")

    st.markdown("---")
    stores = list_stores()
    if not stores:
        st.info("No stores.")
    else:
        s_sel = st.selectbox("Target store", options=stores, format_func=lambda s: s[1], key="edit_store_sel")
        new_sname = st.text_input("New store name", value=s_sel[1], key="edit_store_name")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("Update store name", key="btn_update_store"):
                try:
                    from db import update_store_name
                    update_store_name(s_sel[0], new_sname)
                    st.success("Store name updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
        with c2:
            # Reassignment UI when referenced
            from db import count_purchases_by_store
            n_ref = count_purchases_by_store(s_sel[0])
            if n_ref > 0:
                st.warning(f"This store is referenced by {n_ref} purchases. Reassignment is required before deletion.")
                candidate_stores = [s for s in stores if s[0] != s_sel[0]]
                if candidate_stores:
                    re_to = st.selectbox("Reassign to store", options=candidate_stores, format_func=lambda s: s[1], key="reassign_store_to")
                    if st.button("Reassign and delete old store", key="btn_reassign_and_delete_store"):
                        try:
                            from db import reassign_store_in_purchases, delete_store
                            reassign_store_in_purchases(s_sel[0], re_to[0])
                            delete_store(s_sel[0])
                            st.success(f'Reassigned purchases to "{re_to[1]}" and deleted the old store.')
                            st.rerun()
                        except Exception as e:
                            st.error(f"Deletion failed: {e}")
                else:
                    st.info("No destination store available. Please add another store and try again.")
            else:
                if st.button("Delete store", key="btn_delete_store_no_ref"):
                    try:
                        from db import delete_store
                        delete_store(s_sel[0])
                        st.success("Store deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Deletion failed: {e}")

    st.markdown("---")
    payments = list_payments()
    if not payments:
        st.info("No payment methods.")
    else:
        p_sel = st.selectbox("Target payment method", options=payments, format_func=lambda p: p[1], key="edit_payment_sel")
        new_pname = st.text_input("New payment method name", value=p_sel[1], key="edit_payment_name")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("Update payment method name", key="btn_update_payment"):
                try:
                    from db import update_payment_name
                    update_payment_name(p_sel[0], new_pname)
                    st.success("Payment method name updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
        with c2:
            from db import count_purchases_by_payment
            n_ref = count_purchases_by_payment(p_sel[0])
            if n_ref > 0:
                st.warning(f"This payment method is referenced by {n_ref} purchases. Reassignment is required before deletion.")
                candidate_pay = [p for p in payments if p[0] != p_sel[0]]
                if candidate_pay:
                    re_to = st.selectbox("Reassign to payment method", options=candidate_pay, format_func=lambda p: p[1], key="reassign_payment_to")
                    if st.button("Reassign and delete old method", key="btn_reassign_and_delete_payment"):
                        try:
                            from db import reassign_payment_in_purchases, delete_payment
                            reassign_payment_in_purchases(p_sel[0], re_to[0])
                            delete_payment(p_sel[0])
                            st.success(f'Reassigned purchases to "{re_to[1]}" and deleted the old method.')
                            st.rerun()
                        except Exception as e:
                            st.error(f"Deletion failed: {e}")
                else:
                    st.info("No destination payment method available. Please add another method and try again.")
            else:
                if st.button("Delete payment method", key="btn_delete_payment_no_ref"):
                    try:
                        from db import delete_payment
                        delete_payment(p_sel[0])
                        st.success("Payment method deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Deletion failed: {e}")

with tab_item_admin:
    # Genre selection
    if not genres:
        st.info("No genres.")
    else:
        genre_tabs = st.tabs([g[1] for g in genres])  # Tabs by genre name

        for (gid, gname), gtab in zip(genres, genre_tabs):
            with gtab:
                # Search (partial match)
                q = st.text_input("Search by item name (partial match)", value="", key=f"itadm_query_{gid}").strip().lower()

                # Fetch target items and filter locally
                items = list_items_by_genre(gid)  # [(id, name, unit)]
                if q:
                    items = [(i, n, u) for (i, n, u) in items if q in n.lower()]

                if not items:
                    st.info("No matching items.")
                else:
                    st.caption(f"{len(items)} items")
                    for (iid, name, unit) in items:
                        with st.expander(f"{name} ({unit})", expanded=False):
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                new_name = st.text_input("Item name", value=name, key=f"itadm_name_{iid}")
                                new_unit = st.text_input("Unit", value=unit, key=f"itadm_unit_{iid}")
                            with c2:
                                # Update
                                if st.button("Update", key=f"itadm_update_{iid}"):
                                    try:
                                        from db import update_item
                                        update_item(iid, new_name, new_unit)
                                        st.success("Updated.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Update failed: {e}")

                                # Delete (also reconcile purchases/summaries)
                                if st.button("Delete (also remove related purchases and reconcile summaries)", key=f"itadm_delete_{iid}"):
                                    try:
                                        from db import delete_item_and_update_summaries
                                        delete_item_and_update_summaries(iid)
                                        st.success("Deleted. Related summaries have been reconciled.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Deletion failed: {e}")
