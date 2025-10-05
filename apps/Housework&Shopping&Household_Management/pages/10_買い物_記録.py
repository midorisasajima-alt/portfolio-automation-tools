import streamlit as st
from datetime import date
from db import (
    init_db, seed_minimal, list_genres, list_items_by_genre,
    list_stores, list_payments, ensure_store, ensure_payment,
    insert_purchase, ensure_item
)

st.set_page_config(page_title="買い物_記録", layout="wide")

init_db()
seed_minimal()

def name_id_map(pairs):
    return {name: _id for (_id, name) in pairs}

genres = list_genres()
if not genres:
    st.error("ジャンルが未設定です。db.pyのseed_minimalを編集してください。")
    st.stop()

tab_labels = [g[1] for g in genres]
tabs = st.tabs(tab_labels)

for tab, (genre_id, genre_name) in zip(tabs, genres):
    with tab:

        # --- 検索＋選択（横並び） ---
        items = list_items_by_genre(genre_id)  # [(id, name, unit)]
        c1, c2 = st.columns([1, 2])
        with c1:
            q = st.text_input("検索（品目名の部分一致）", key=f"search_{genre_id}")
        filtered = [(iid, name, unit) for (iid, name, unit) in items if (q in name) or not q]

        with c2:
            if filtered:
                labels = [f"{name}（{unit}）" for (_, name, unit) in filtered]
                idx = st.selectbox("品目（単位）", options=list(range(len(filtered))), format_func=lambda i: labels[i], key=f"item_sel_{genre_id}")
                item_id = filtered[idx][0]
                unit = filtered[idx][2]
            else:
                st.info("ヒットなし。下で新規追加できます。")
                item_id = None
                unit = ""

        # --- 品目の新規追加 ---
        with st.expander("品目の新規追加（クリックで開く）", expanded=True):
            st.caption("このジャンルに新規品目を作成します。")

            a1, a2, a3 = st.columns([2, 1, 1])
            with a1:
                new_item_name = st.text_input("品目名（新規）", key=f"new_item_name_{genre_id}")
            with a2:
                new_item_unit = st.text_input("単位（新規）", key=f"new_item_unit_{genre_id}")
            with a3:
                add_clicked = st.button("追加", key=f"add_item_{genre_id}")

            if add_clicked:
                try:
                    new_id = ensure_item(genre_id, new_item_name, new_item_unit)
                    st.success(f"追加しました：{new_item_name}（{new_item_unit}）")
                    item_id = new_id
                    unit = new_item_unit
                except Exception as e:
                    st.error(f"追加に失敗しました: {e}")


        # --- 日付・店・数量・金額・支払い手段 ---
        d = st.date_input("日付", value=date.today(), key=f"date_{genre_id}")

        stores = list_stores()
        store_names = [s[1] for s in stores]
        store_name_to_id = name_id_map(stores)
        store_choice = st.selectbox("店名（選択）", ["（選択してください）"] + store_names + ["＋ 新規追加"], key=f"store_sel_{genre_id}")
        store_id = None
        if store_choice == "＋ 新規追加":
            new_store = st.text_input("新規店名", key=f"store_new_{genre_id}")
            if new_store:
                store_id = ensure_store(new_store.strip())
        elif store_choice != "（選択してください）":
            store_id = store_name_to_id.get(store_choice)

        qty = st.number_input(f"数量（{unit or '単位未設定'}）", min_value=0.0, value=1.0, step=1.0, key=f"qty_{genre_id}")
        total = st.number_input("合計金額", min_value=0.0, value=0.0, step=1.0, key=f"total_{genre_id}")

        payments = list_payments()
        pay_names = [p[1] for p in payments]
        pay_name_to_id = name_id_map(payments)
        pay_choice = st.selectbox("支払い手段", pay_names, key=f"pay_{genre_id}")
        payment_id = pay_name_to_id.get(pay_choice)

        col_a, col_b = st.columns([1,1])
        with col_a:
            if qty > 0:
                st.caption(f"一単位当たりの金額（自動計算）: { (total / qty) if qty else 0:.2f} / {unit or '-'}")
            else:
                st.caption("数量が0以下のため単価は計算されません。")
        with col_b:
            submitted = st.button("保存", key=f"submit_{genre_id}")

        if submitted:
            if not item_id:
                st.error("品目を選択するか新規追加してください。")
            elif not store_id:
                st.error("店名を選択または追加してください。")
            elif qty <= 0:
                st.error("数量は正の数で入力してください。")
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
                    st.success("保存しました。月×ジャンルの集計・品目リストも更新済みです。")
                except Exception as e:
                    st.error(f"保存に失敗しました: {e}")