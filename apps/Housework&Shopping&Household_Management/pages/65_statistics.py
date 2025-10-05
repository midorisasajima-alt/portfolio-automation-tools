# -*- coding: utf-8 -*-
import streamlit as st
import matplotlib.pyplot as plt
from typing import List, Dict
from db import get_available_months, list_genres, get_conn

st.set_page_config(page_title="Statistics (Genre Trends)", layout="wide")

months = get_available_months()
if not months:
    st.info("No data available. Please record first in 'Shopping_Record'.")
    st.stop()
months = sorted(months)  # ascending order

genres = list_genres()   # [(id, name), ...]
if not genres:
    st.info("No genres registered. Please add them in 'Edit'.")
    st.stop()

# ── Button group ───────────────────────────────────────────────
c1, c2, c3 = st.columns([1,1,4])
with c1:
    if st.button("Select All"):
        for gid, _ in genres:
            st.session_state[f"sel_genre_{gid}"] = True
with c2:
    if st.button("Deselect All"):
        for gid, _ in genres:
            st.session_state[f"sel_genre_{gid}"] = False

st.markdown("#### Select Genres")
# ── Checkbox group ─────────────────────────────────────────────
selected_ids = []
cols = st.columns(4)  # Adjust the number of columns as needed
for i, (gid, gname) in enumerate(genres):
    key = f"sel_genre_{gid}"
    with cols[i % len(cols)]:
        checked = st.checkbox(gname, value=st.session_state.get(key, False), key=key)
        if checked:
            selected_ids.append(gid)

# Save the current selection as "previous selection"
st.session_state.prev_selection = set(selected_ids)

if not selected_ids:
    st.info("Please select at least one genre to display.")
    st.stop()

# ---- Data retrieval: time series of (genre × month) ----
def fetch_series_for_genre(genre_id: int, month_list: List[str]) -> List[float]:
    """Retrieve total amount per month for the specified genre_id from monthly_genre_summary.
    Fill missing months with zeros.
    """
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

# ---- Plotting ----
fig, ax = plt.subplots()
x = list(range(len(months)))

for gid in selected_ids:
    # Display name
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
