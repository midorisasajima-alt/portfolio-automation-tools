# -*- coding: utf-8 -*-
import streamlit as st
import matplotlib.pyplot as plt
from typing import List, Dict
from db import get_available_months, list_genres, get_conn

st.set_page_config(page_title="統計（ジャンル推移）", layout="wide")

months = get_available_months()
if not months:
    st.info("データがありません。先に『買い物_記録』で記録してください。")
    st.stop()
months = sorted(months)  # 昇順

genres = list_genres()   # [(id, name), ...]
if not genres:
    st.info("ジャンルが未登録です。『編集』で追加してください。")
    st.stop()


# ボタン群
c1, c2, c3 = st.columns([1,1,4])
with c1:
    if st.button("全選択"):
        for gid, _ in genres:
            st.session_state[f"sel_genre_{gid}"] = True
with c2:
    if st.button("全解除"):
        for gid, _ in genres:
            st.session_state[f"sel_genre_{gid}"] = False

st.markdown("#### ジャンル選択")
# チェックボックス群
selected_ids = []
cols = st.columns(4)  # 適宜分割列数
for i, (gid, gname) in enumerate(genres):
    key = f"sel_genre_{gid}"
    with cols[i % len(cols)]:
        checked = st.checkbox(gname, value=st.session_state.get(key, False), key=key)
        if checked:
            selected_ids.append(gid)

# 現在の選択を「前選択」として保存
st.session_state.prev_selection = set(selected_ids)

if not selected_ids:
    st.info("表示するジャンルを選択してください。")
    st.stop()

# ---- データ取得：ジャンル×月の時系列（monthly_genre_summary を横断） ----
def fetch_series_for_genre(genre_id: int, month_list: List[str]) -> List[float]:
    """monthly_genre_summary から genre_id の各月合計を取り出し、存在しない月は0埋め。"""
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT month, total_amount
        FROM monthly_genre_summary
        WHERE genre_id=?
    """, (genre_id,))
    rows = cur.fetchall()
    conn.close()
    d: Dict[str, float] = {m: float(v or 0.0) for (m, v) in rows}
    return [d.get(m, 0.0) for m in month_list]

# ---- プロット ----
fig, ax = plt.subplots()
x = list(range(len(months)))

for gid in selected_ids:
    # 表示名
    gname = next(n for (g, n) in genres if g == gid)
    y = fetch_series_for_genre(gid, months)
    ax.plot(x, y, label=gname)

ax.set_xticks(x)
ax.set_xticklabels(months, rotation=45, ha="right")
ax.set_xlabel("Month")
ax.set_ylabel("Total Amount")
ax.legend()
fig.tight_layout()
st.pyplot(fig)

