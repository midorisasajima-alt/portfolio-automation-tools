
# =============================
# pages/2_候補.py
# -----------------------------
import streamlit as st
from datetime import date
import pandas as pd
import altair as alt
from msal_auth import get_access_token
from graph_client import list_events, create_event_from_candidate
from db import list_candidates_by_date, delete_candidate, get_candidate
from utils import graph_dt_to_london

st.title("2) 候補（Time Line + 追加/編集/削除）")

D = st.date_input("日付", value=date.today(), format="YYYY-MM-DD")

# Graph イベント
try:
    token = get_access_token()
    ms_events = list_events(token, D.isoformat())
except Exception:
    st.warning("デモ：Outlook 未認証または取得失敗。空で表示します。")
    ms_events = []

# 候補
cands = list_candidates_by_date(D.isoformat())

# タイムライン用データフレーム
rows = []
for ev in ms_events:
    st_dt = graph_dt_to_london(ev.get("start"))
    en_dt = graph_dt_to_london(ev.get("end"))
    rows.append({
        "line": "確定",
        "title": ev.get("subject") or "(No title)",
        "start": st_dt.replace(tzinfo=None).isoformat(),  # ← tzinfo を外す
        "end":   en_dt.replace(tzinfo=None).isoformat(),
        "type": "ms",
    })
for i, c in enumerate(cands, start=1):
    rows.append({
        "line": c["title"],
        "title": c["title"],
        "start": f"{c['date']}T{c['start_time']}",
        "end":   f"{c['date']}T{c['end_time']}",
        "type": "cand",
        "cid": c["id"],
        "info": c.get("info_url","")
    })

if rows:
    df = pd.DataFrame(rows)
    base = alt.Chart(df)

    chart = base.mark_bar().encode(
        y=alt.Y("line:N", sort=None, title=None),           # ← y軸タイトルを非表示（"line"を消す）
        x=alt.X("start:T", title=None),
        x2="end:T",
        tooltip=["title", "start", "end", "line"],
        color=alt.Color(                                     # ← typeごとに色を固定
            "type:N",
            scale=alt.Scale(
                domain=["ms", "cand"],
                range=["#4682B4", "#3CB371"]                # 確定=steelblue, 候補=MediumSeaGreen（明度近似）
            ),
            legend=None                                      # 凡例は不要なら隠す
        ),
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info("この日のデータがありません。")

st.subheader("候補リスト")
for c in cands:
    colL, colR = st.columns([2,1])
    with colL:
        st.write(f"📝 {c['title']} | {c['start_time']}→{c['end_time']} | 情報: {c.get('info_url','')}")
    with colR:
        info_col, add_col, edit_col, del_col = st.columns(4)
        with info_col:
            if c.get('info_url'):
                if c.get("info_url"):
                    st.link_button("情報", c["info_url"])
                else:
                    st.button("情報", disabled=True)
        with add_col:
            if st.button("追加", key=f"add_{c['id']}"):   # インデント4
                try:                                     # インデント8
                    ev = create_event_from_candidate(     # インデント12
                        token, c['date'], c['title'], c['start_time'], c['end_time']
                    )
                except Exception as e:                   # インデント8
                    st.error(f"Outlook 追加時に例外が発生しました: {e}")  # インデント12
                    ev = None                            # インデント12

                if ev:                                   # インデント8
                    try:                                 # インデント12
                        delete_candidate(c['id'])        # インデント16
                        st.success("Outlook に追加しました。候補をDBから削除しました。")  # インデント16
                        st.rerun()                       # インデント16
                    except Exception as e:               # インデント12
                        st.warning(f"Outlookへは追加済みですが、候補の削除に失敗しました: {e}")  # インデント16
                else:                                    # インデント8
                    st.error("Outlook への追加に失敗しました。候補は削除していません。")  # インデント12


        with edit_col:
            # 編集ボタン
            if st.button("編集", key=f"edit_{c['id']}"):
                st.session_state["edit_id"] = c["id"]
                try:
                    # 新しめのStreamlit
                    st.switch_page("pages/4_編集削除.py")
                except Exception:
                    # 古い版の保険として同ページでリロードし、受け側で session_state を読む
                    st.rerun()

        with del_col:
            if st.button("削除", key=f"del_{c['id']}"):
                if st.session_state.get(f"confirm_{c['id']}"):
                    delete_candidate(c['id'])
                    st.success("削除しました。")
                else:
                    st.session_state[f"confirm_{c['id']}"] = True
                    st.warning("もう一度押すと削除します。")
