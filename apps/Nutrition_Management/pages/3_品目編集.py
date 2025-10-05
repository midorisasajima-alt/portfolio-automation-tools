import streamlit as st
from db import list_genres, list_items, insert_item, update_item, delete_item, get_item

st.set_page_config(page_title="品目編集", layout="wide")

st.header("品目 追加・編集・削除")

TAB_ADD, TAB_EDIT = st.tabs(["品目追加", "品目編集・削除"])

with TAB_ADD:
    st.subheader("品目追加")
    genre = st.text_input("ジャンル（例：主食、主菜、間食、飲料 など）")
    name = st.text_input("品目名")
    unit = st.text_input("単位（例：個、g、ml、カップ など）")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        energy = st.number_input("Energy/単位", min_value=0.0, step=1.0)
    with c2:
        protein = st.number_input("Protein/単位", min_value=0.0, step=0.1)
    with c3:
        fat = st.number_input("Fat/単位", min_value=0.0, step=0.1)
    with c4:
        carb = st.number_input("Carbohydrate/単位", min_value=0.0, step=1.0)

    if st.button("保存"):
        if not (genre and name and unit):
            st.warning("ジャンル・品目名・単位を入力してください。")
        else:
            insert_item({
                "genre": genre, "name": name, "unit": unit,
                "energy": energy, "protein": protein, "fat": fat, "carbohydrate": carb
            })
            st.success("保存しました。")

with TAB_EDIT:
    st.subheader("品目編集・削除")
    genres = [""] + list_genres()
    g = st.selectbox("ジャンルを選択", options=genres)
    keyword = st.text_input("品目検索（部分一致）")

    items = list_items(keyword=keyword, genre=(g if g else None))
    if not items:
        st.info("該当する品目がありません。")
    else:
        for it in items:
            with st.expander(f"{it['genre']} / {it['name']}"):
                ng = st.text_input("ジャンル", value=it['genre'], key=f"g_{it['id']}")
                nm = st.text_input("品目名", value=it['name'], key=f"n_{it['id']}")
                un = st.text_input("単位", value=it['unit'], key=f"u_{it['id']}")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    en = st.number_input("Energy/単位", min_value=0.0, step=1.0, value=float(it['energy']), key=f"e_{it['id']}")
                with c2:
                    pr = st.number_input("Protein/単位", min_value=0.0, step=0.1, value=float(it['protein']), key=f"p_{it['id']}")
                with c3:
                    ft = st.number_input("Fat/単位", min_value=0.0, step=0.1, value=float(it['fat']), key=f"f_{it['id']}")
                with c4:
                    ca = st.number_input("Carbohydrate/単位", min_value=0.0, step=1.0, value=float(it['carbohydrate']), key=f"c_{it['id']}")
                cta1, cta2 = st.columns(2)
                with cta1:
                    if st.button("更新", key=f"upd_item_{it['id']}"):
                        update_item(it['id'], {
                            "genre": ng, "name": nm, "unit": un,
                            "energy": en, "protein": pr, "fat": ft, "carbohydrate": ca
                        })
                        st.success("更新しました。")
                with cta2:
                    if st.button("削除", key=f"del_item_{it['id']}"):
                        delete_item(it['id'])
                        st.success("削除しました。")
