# =============================
# pages/6_体.py（能率の期間設定）
# -----------------------------
import streamlit as st
from datetime import date
from db import insert_efficiency, list_efficiency, update_efficiency, delete_efficiency

st.title("6) 体（能率）")

tab_add, tab_edit = st.tabs(["追加", "編集削除"])

# -------- 追加タブ --------
with tab_add:
    with st.form("eff_add"):
        col1, col2 = st.columns(2)
        with col1:
            s = st.date_input("開始日", value=date.today(), format="YYYY-MM-DD")
            e = st.date_input("終了日", value=date.today(), format="YYYY-MM-DD")
        eff = st.slider("能率（%）", min_value=0, max_value=100, value=80, step=1)

        rep = st.selectbox("繰り返し", ["一度限り", "繰り返す"])

        # 「繰り返す」時のみ、未選択プレースホルダ付きセレクトを表示
        interval_edit = None
        interval_placeholder = "—選択—"
        if rep == "繰り返す":
            # 1〜30日を候補に（必要に応じて範囲調整）
            options = [interval_placeholder] + list(range(1, 31))
            chosen = st.selectbox("周期（日）", options, index=0, key="interval_days_select")
            if chosen != interval_placeholder:
                interval_edit = int(chosen)

        # 送信ボタンはバリデーションに応じて無効化
        can_submit = True
        msg = None
        if e < s:
            can_submit = False
            msg = "終了日は開始日以降である必要があります。"
        if rep == "繰り返す" and interval_edit is None:
            can_submit = False
            msg = "周期（日）を選択してください。"

        submitted = st.form_submit_button("追加", disabled=not can_submit)

        if submitted:
            insert_efficiency(
                s.isoformat(),
                e.isoformat(),
                eff / 100.0,
                1 if rep == "繰り返す" else 0,
                interval_edit if rep == "繰り返す" else None,
            )
            st.success("追加しました。")
            st.rerun()

        if msg and not submitted:
            st.info(msg)

# -------- 編集削除タブ --------
with tab_edit:
    st.subheader("登録済み")
    rows = list_efficiency()

    if not rows:
        st.info("登録がありません。")
    else:
        for r in rows:
            try:
                s_default = date.fromisoformat(r["start_date"])
                e_default = date.fromisoformat(r["end_date"])
            except Exception:
                s_default = date.today()
                e_default = date.today()

            eff_pct = int(round((r.get("efficiency") or 0.0) * 100))
            rep_default = "繰り返す" if (r.get("repeat") or 0) == 1 else "一度限り"
            interval_default = r.get("interval_days")

            header = f"ID {r['id']}｜{r['start_date']} → {r['end_date']}｜{eff_pct}%｜{'繰返' if rep_default=='繰り返す' else '単発'}"
            with st.expander(header, expanded=False):
                with st.form(f"eff_edit_{r['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        s_edit = st.date_input("開始日", value=s_default, format="YYYY-MM-DD", key=f"s_{r['id']}")
                        e_edit = st.date_input("終了日", value=e_default, format="YYYY-MM-DD", key=f"e_{r['id']}")
                    eff_edit = st.slider("能率（%）", min_value=0, max_value=100, value=eff_pct, step=1, key=f"eff_{r['id']}")
                    rep_edit = st.selectbox("繰り返し", ["一度限り", "繰り返す"],
                                            index=(0 if rep_default == "一度限り" else 1), key=f"rep_{r['id']}")

                    interval_edit_row = None
                    if rep_edit == "繰り返す":
                        # 編集時も「—選択—」を用意。既存値があればそれを既定選択
                        options_row = [interval_placeholder] + list(range(1, 31))
                        if isinstance(interval_default, int) and 1 <= interval_default <= 30:
                            init_idx = options_row.index(interval_default)
                        else:
                            init_idx = 0
                        chosen_row = st.selectbox("周期（日）", options_row, index=init_idx, key=f"int_{r['id']}")
                        if chosen_row != interval_placeholder:
                            interval_edit_row = int(chosen_row)

                    colu = st.columns(3)
                    with colu[0]:
                        save = st.form_submit_button("保存",
                            disabled=(e_edit < s_edit) or (rep_edit == "繰り返す" and interval_edit_row is None))
                    with colu[1]:
                        delete = st.form_submit_button("削除", type="primary")
                    with colu[2]:
                        cancel = st.form_submit_button("キャンセル")

                if save:
                    updated = update_efficiency(
                        r["id"],
                        s_edit.isoformat(),
                        e_edit.isoformat(),
                        eff_edit / 100.0,
                        1 if rep_edit == "繰り返す" else 0,
                        interval_edit_row if rep_edit == "繰り返す" else None,
                    )
                    if updated == 1:
                        st.success("更新しました。")
                        st.rerun()
                    else:
                        st.warning("更新対象が見つかりませんでした。")

                if delete:
                    removed = delete_efficiency(r["id"])
                    if removed == 1:
                        st.success("削除しました。")
                        st.rerun()
                    else:
                        st.warning("削除対象が見つかりませんでした。")
