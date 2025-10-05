import streamlit as st
from datetime import date
from db import (
    init_db, seed_minimal, list_genres, list_items_by_genre, list_stores, list_payments,
    ensure_store, update_purchase, delete_purchase,
    update_item_unit, change_item_genre, get_purchases_by_genre_item,delete_genre_and_update_summaries,get_purchases_filtered
)

st.set_page_config(page_title="買い物_記録編集", layout="wide")

init_db()
seed_minimal()

def name_id_map(pairs):
    return {name: _id for (_id, name) in pairs}

genres = list_genres()
if not genres:
    st.error("ジャンルが未設定です。")
    st.stop()

tab_main, tab_reclass, tab_item_admin,tab_master, tab_edit = st.tabs(
    ["記録修正・削除", "品目のジャンル変更","品目編集・削除", "マスタ追加", "マスタ編集・削除"]
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
            # 1) 品目フィルタ
            sel = st.selectbox(
                "品目で絞り込み",
                options=options,
                format_func=lambda x: "（すべて）" if x is None else f"{x[1]}",
                key=f"filter_item_{genre_id}",
            )
            item_id = None if sel is None else sel[0]

            # 2) 店名フィルタ
            store_filter_options = [("ALL", "（すべて）")] + [(sid, sname) for (sid, sname) in stores]
            store_sel = st.selectbox(
                "店名で絞込み",
                options=store_filter_options,
                format_func=lambda t: t[1],
                key=f"filter_store_{genre_id}",
            )
            store_id = None if store_sel[0] == "ALL" else store_sel[0]

            # 3) 日付フィルタ（任意・範囲）
            use_date = st.checkbox("日付で絞込む", value=False, key=f"filter_date_use_{genre_id}")
            start_iso = end_iso = None
            if use_date:
                # 初期値は当月の1日〜今日（必要に応じて変更）
                from datetime import date, timedelta
                today = date.today()
                start_default = today.replace(day=1)
                dr = st.date_input(
                    "日付範囲",
                    value=(start_default, today),
                    key=f"filter_date_rng_{genre_id}"
                )
                # streamlit の戻りが tuple[date, date] 前提
                if isinstance(dr, tuple) and len(dr) == 2:
                    start_iso = dr[0].isoformat()
                    end_iso = dr[1].isoformat()

            # 取得処理：サーバ側フィルタを使用
            rows = get_purchases_filtered(
                genre_id=genre_id,
                item_id=item_id,
                store_id=store_id,
                start_date_iso=start_iso,
                end_date_iso=end_iso
            )

            if not rows:
                st.info("該当する記録はありません。")
            else:
                for (pid, iid, iname, unit, d, store_id_row, store_name, qty, total, unit_price, payment_id, payment_name) in rows:
                    with st.expander(f"{d} ｜ {iname} ｜ {store_name} ｜ {qty} {unit} ｜ 合計 {total} ｜ {payment_name}", expanded=False):
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c1:
                            new_date = st.date_input("日付", value=date.fromisoformat(d), key=f"date_{pid}")
                            new_qty = st.number_input(f"数量（{unit}）", min_value=0.0, value=float(qty), step=1.0, key=f"qty_{pid}")
                        with c2:
                            new_total = st.number_input("合計金額", min_value=0.0, value=float(total), step=1.0, key=f"total_{pid}")
                            st.caption(f"単価: {(new_total/new_qty) if new_qty else 0:.2f} / {unit}")
                        with c3:
                            new_store = st.selectbox("店名", store_names, index=store_names.index(store_name) if store_name in store_names else 0, key=f"store_{pid}")
                            new_payment = st.selectbox("支払い手段", pay_names, index=pay_names.index(payment_name) if payment_name in pay_names else 0, key=f"pay_{pid}")

                        colu1, colu2 = st.columns([1,1])
                        with colu1:
                            if st.button("更新", key=f"update_{pid}"):
                                try:
                                    update_purchase(
                                        purchase_id=pid,
                                        date_iso=new_date.isoformat(),
                                        store_id=store_name_to_id[new_store],
                                        qty=float(new_qty),
                                        total=float(new_total),
                                        payment_id=pay_name_to_id[new_payment],
                                    )
                                    st.success("更新しました。（集計も更新済み）")
                                except Exception as e:
                                    st.error(f"更新に失敗しました: {e}")
                        with colu2:
                            if st.button("品目を削除（この品目の購入記録も全て削除）", key=f"del_{pid}", type="secondary"):
                                try:
                                    from db import delete_item_and_update_summaries
                                    delete_item_and_update_summaries(iid)  # ← 行の品目IDを渡す
                                    st.success("品目を削除しました。月別ジャンル集計・支払い手段集計も更新済みです。")
                                except Exception as e:
                                    st.error(f"削除に失敗しました: {e}")
                            

with tab_reclass:
    # 現在のジャンル→品目→新ジャンル
    scol1, scol2, scol3 = st.columns([1,2,1])
    with scol1:
        gidx = st.selectbox("現在のジャンル", options=list(range(len(genres))), format_func=lambda i: genres[i][1], key="re_g")
        current_gid = genres[gidx][0]
    items = list_items_by_genre(current_gid)
    if not items:
        st.info("このジャンルに品目がありません。")
    else:
        with scol2:
            labels = [f"{name}" for (_id, name, unit) in items]
            idx = st.selectbox("品目", options=list(range(len(items))), format_func=lambda i: labels[i], key="re_item")
            item_id = items[idx][0]
        with scol3:
            new_gidx = st.selectbox("新しいジャンル", options=list(range(len(genres))), format_func=lambda i: genres[i][1], key="re_newg")
            new_gid = genres[new_gidx][0]

        if st.button("ジャンルを変更"):
            try:
                change_item_genre(item_id, new_gid)
                st.success("ジャンルを変更しました。（集計も移行済み）")
            except Exception as e:
                st.error(f"変更に失敗しました: {e}")
                
with tab_master:
    
    # ジャンル追加
    g1, g2 = st.columns([3,1])
    with g1:
        new_genre = st.text_input("新規ジャンル名")
    with g2:
        if st.button("ジャンルを追加",key="add_genre_btn"):
            try:
                from db import ensure_genre
                gid = ensure_genre(new_genre)
                st.success(f"ジャンルを追加しました：{new_genre}")
            except Exception as e:
                st.error(f"追加に失敗しました: {e}")

    st.markdown("---")
    # 店名追加
    s1, s2 = st.columns([3,1])
    with s1:
        new_store = st.text_input("新規店名")
    with s2:
        if st.button("店名を追加",key="add_store_btn"):
            try:
                from db import ensure_store
                sid = ensure_store(new_store)
                st.success(f"店名を追加しました：{new_store}")
            except Exception as e:
                st.error(f"追加に失敗しました: {e}")

    st.markdown("---")
    # 支払い手段追加
    p1, p2 = st.columns([3,1])
    with p1:
        new_payment = st.text_input("新規支払い手段")
    with p2:
        if st.button("支払い手段を追加",key="add_payment_btn"):
            try:
                from db import ensure_payment
                pid = ensure_payment(new_payment)
                st.success(f"支払い手段を追加しました：{new_payment}")
            except Exception as e:
                st.error(f"追加に失敗しました: {e}")

with tab_edit:
    genres = list_genres()
    if not genres:
        st.info("ジャンルがありません。")
    else:
        g_sel = st.selectbox("対象ジャンル", options=genres, format_func=lambda g: g[1], key="edit_genre_sel")
        new_gname = st.text_input("新しいジャンル名", value=g_sel[1], key="edit_genre_name")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("ジャンル名を更新", key="btn_update_genre"):
                try:
                    from db import update_genre_name
                    update_genre_name(g_sel[0], new_gname)
                    st.success("ジャンル名を更新しました。")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新に失敗しました: {e}")
        with c2:
            if st.button("ジャンルを削除（配下すべて削除）", key="btn_delete_genre"):
                try:
                    delete_genre_and_update_summaries(g_sel[0])
                    st.success(f"ジャンル「{g_sel[1]}」を削除しました。関連データも整合済みです。")
                    st.rerun()
                except Exception as e:
                    st.error(f"削除に失敗しました: {e}")

    st.markdown("---")
    stores = list_stores()
    if not stores:
        st.info("店名がありません。")
    else:
        s_sel = st.selectbox("対象の店", options=stores, format_func=lambda s: s[1], key="edit_store_sel")
        new_sname = st.text_input("新しい店名", value=s_sel[1], key="edit_store_name")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("店名を更新", key="btn_update_store"):
                try:
                    from db import update_store_name
                    update_store_name(s_sel[0], new_sname)
                    st.success("店名を更新しました。")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新に失敗しました: {e}")
        with c2:
            # 参照がある場合の再割当 UI
            from db import count_purchases_by_store
            n_ref = count_purchases_by_store(s_sel[0])
            if n_ref > 0:
                st.warning(f"この店は {n_ref} 件の購入に参照されています。削除には再割当が必要です。")
                candidate_stores = [s for s in stores if s[0] != s_sel[0]]
                if candidate_stores:
                    re_to = st.selectbox("再割当先の店", options=candidate_stores, format_func=lambda s: s[1], key="reassign_store_to")
                    if st.button("再割当して旧店を削除", key="btn_reassign_and_delete_store"):
                        try:
                            from db import reassign_store_in_purchases, delete_store
                            reassign_store_in_purchases(s_sel[0], re_to[0])
                            delete_store(s_sel[0])
                            st.success(f"購入を「{re_to[1]}」へ再割当し、旧店を削除しました。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除に失敗しました: {e}")
                else:
                    st.info("再割当先の店がありません。別の店を追加してから再実行してください。")
            else:
                if st.button("店を削除", key="btn_delete_store_no_ref"):
                    try:
                        from db import delete_store
                        delete_store(s_sel[0])
                        st.success("店を削除しました。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除に失敗しました: {e}")

    st.markdown("---")
    payments = list_payments()
    if not payments:
        st.info("支払い手段がありません。")
    else:
        p_sel = st.selectbox("対象の支払い手段", options=payments, format_func=lambda p: p[1], key="edit_payment_sel")
        new_pname = st.text_input("新しい支払い手段名", value=p_sel[1], key="edit_payment_name")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("支払い手段名を更新", key="btn_update_payment"):
                try:
                    from db import update_payment_name
                    update_payment_name(p_sel[0], new_pname)
                    st.success("支払い手段名を更新しました。")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新に失敗しました: {e}")
        with c2:
            from db import count_purchases_by_payment
            n_ref = count_purchases_by_payment(p_sel[0])
            if n_ref > 0:
                st.warning(f"この支払い手段は {n_ref} 件の購入に参照されています。削除には再割当が必要です。")
                candidate_pay = [p for p in payments if p[0] != p_sel[0]]
                if candidate_pay:
                    re_to = st.selectbox("再割当先の支払い手段", options=candidate_pay, format_func=lambda p: p[1], key="reassign_payment_to")
                    if st.button("再割当して旧支払い手段を削除", key="btn_reassign_and_delete_payment"):
                        try:
                            from db import reassign_payment_in_purchases, delete_payment
                            reassign_payment_in_purchases(p_sel[0], re_to[0])
                            delete_payment(p_sel[0])
                            st.success(f"購入を「{re_to[1]}」へ再割当し、旧支払い手段を削除しました。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除に失敗しました: {e}")
                else:
                    st.info("再割当先の支払い手段がありません。別の支払い手段を追加してから再実行してください。")
            else:
                if st.button("支払い手段を削除", key="btn_delete_payment_no_ref"):
                    try:
                        from db import delete_payment
                        delete_payment(p_sel[0])
                        st.success("支払い手段を削除しました。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除に失敗しました: {e}")
                        
with tab_item_admin:

    # ジャンル選択
    if not genres:
        st.info("ジャンルがありません。")
    else:
        genre_tabs = st.tabs([g[1] for g in genres])  # ジャンル名でタブを作成

        for (gid, gname), gtab in zip(genres, genre_tabs):
            with gtab:

                # 検索（前方・中間一致）
                q = st.text_input("品目名で検索（部分一致）", value="", key=f"itadm_query_{gid}").strip().lower()

                # 対象品目取得＋ローカル絞り込み
                items = list_items_by_genre(gid)  # [(id, name, unit)]
                if q:
                    items = [(i, n, u) for (i, n, u) in items if q in n.lower()]

                if not items:
                    st.info("該当する品目がありません。")
                else:
                    st.caption(f"{len(items)} 件")
                    for (iid, name, unit) in items:
                        with st.expander(f"{name}（{unit}）", expanded=False):
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                new_name = st.text_input("品目名", value=name, key=f"itadm_name_{iid}")
                                new_unit = st.text_input("単位", value=unit, key=f"itadm_unit_{iid}")
                            with c2:
                                # 更新
                                if st.button("更新", key=f"itadm_update_{iid}"):
                                    try:
                                        from db import update_item
                                        update_item(iid, new_name, new_unit)
                                        st.success("更新しました。")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"更新に失敗しました: {e}")

                                # 削除（購入・集計も整合削除）
                                if st.button("削除（この品目と紐づく購入・集計も整理）", key=f"itadm_delete_{iid}"):
                                    try:
                                        from db import delete_item_and_update_summaries
                                        delete_item_and_update_summaries(iid)
                                        st.success("削除しました。関連集計も整合済みです。")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"削除に失敗しました: {e}")
