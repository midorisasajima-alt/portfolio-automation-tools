# =============================
# pages/2_Candidates.py
# -----------------------------
import streamlit as st
from datetime import date
import pandas as pd
import altair as alt
from msal_auth import get_access_token
from graph_client import list_events, create_event_from_candidate
from db import list_candidates_by_date, delete_candidate, get_candidate
from utils import graph_dt_to_london

st.title("2) Candidates (Timeline + Add/Edit/Delete)")

D = st.date_input("Date", value=date.today(), format="YYYY-MM-DD")

# Graph events
try:
    token = get_access_token()
    ms_events = list_events(token, D.isoformat())
except Exception:
    st.warning("Demo mode: Outlook not authenticated or failed to retrieve events. Displaying empty list.")
    ms_events = []

# Candidate events
cands = list_candidates_by_date(D.isoformat())

# Data for timeline
rows = []
for ev in ms_events:
    st_dt = graph_dt_to_london(ev.get("start"))
    en_dt = graph_dt_to_london(ev.get("end"))
    rows.append({
        "line": "Confirmed",
        "title": ev.get("subject") or "(No title)",
        "start": st_dt.replace(tzinfo=None).isoformat(),
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
        "info": c.get("info_url", "")
    })

if rows:
    df = pd.DataFrame(rows)
    base = alt.Chart(df)

    chart = base.mark_bar().encode(
        y=alt.Y("line:N", sort=None, title=None),           # Hide Y-axis title (“line”)
        x=alt.X("start:T", title=None),
        x2="end:T",
        tooltip=["title", "start", "end", "line"],
        color=alt.Color(                                     # Fixed colors for each type
            "type:N",
            scale=alt.Scale(
                domain=["ms", "cand"],
                range=["#4682B4", "#3CB371"]                # Confirmed = steelblue, Candidate = MediumSeaGreen
            ),
            legend=None
        ),
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No data available for this date.")

st.subheader("Candidate List")
for c in cands:
    colL, colR = st.columns([2,1])
    with colL:
        st.write(f"📝 {c['title']} | {c['start_time']} → {c['end_time']} | Info: {c.get('info_url', '')}")
    with colR:
        info_col, add_col, edit_col, del_col = st.columns(4)
        with info_col:
            if c.get('info_url'):
                if c.get("info_url"):
                    st.link_button("Info", c["info_url"])
                else:
                    st.button("Info", disabled=True)
        with add_col:
            if st.button("Add", key=f"add_{c['id']}"):
                try:
                    ev = create_event_from_candidate(
                        token, c['date'], c['title'], c['start_time'], c['end_time']
                    )
                except Exception as e:
                    st.error(f"An exception occurred while adding to Outlook: {e}")
                    ev = None

                if ev:
                    try:
                        delete_candidate(c['id'])
                        st.success("Added to Outlook and removed from database.")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"Added to Outlook, but failed to delete the candidate record: {e}")
                else:
                    st.error("Failed to add to Outlook. Candidate was not deleted.")

        with edit_col:
            # Edit button
            if st.button("Edit", key=f"edit_{c['id']}"):
                st.session_state["edit_id"] = c["id"]
                try:
                    st.switch_page("pages/4_EditDelete.py")
                except Exception:
                    st.rerun()

        with del_col:
            if st.button("Delete", key=f"del_{c['id']}"):
                if st.session_state.get(f"confirm_{c['id']}"):
                    delete_candidate(c['id'])
                    st.success("Deleted successfully.")
                else:
                    st.session_state[f"confirm_{c['id']}"] = True
                    st.warning("Press again to confirm deletion.")
