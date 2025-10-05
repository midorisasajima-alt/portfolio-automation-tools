# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db import (
    list_walking, list_activity,
    update_walking, update_activity,
    delete_walking, delete_activity
)

st.set_page_config(page_title="Edit Records", layout="wide")

TAB_WALK, TAB_ACT = st.tabs(["Walking", "Other Activities"])

# ----- Walking records -----
with TAB_WALK:
    wl = list_walking()
    if not wl:
        st.info("No walking records found.")
    else:
        for r in wl:
            with st.expander(f"ID {r['id']} | {r['date']} | Steps {r['steps']}"):
                c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
                d = c1.date_input("Date", value=date.fromisoformat(r["date"]), format="YYYY-MM-DD", key=f"wd_{r['id']}")
                steps = c2.number_input("Steps", min_value=0, step=100, value=int(r["steps"]), key=f"ws_{r['id']}")
                step_len = c3.number_input("Step length (m/step)", min_value=0.3, max_value=1.2, step=0.01, value=float(r["step_length_m"]), format="%.2f", key=f"wsl_{r['id']}")
                speed = c4.number_input("Speed (m/min)", min_value=20.0, max_value=140.0, step=1.0, value=float(r["speed_m_per_min"]), format="%.1f", key=f"wsp_{r['id']}")
                col_u, col_d = st.columns([1, 1])
                if col_u.button("Update", key=f"wu_{r['id']}"):
                    update_walking(r["id"], d.strftime("%Y-%m-%d"), int(steps), float(step_len), float(speed))
                    st.success("Updated successfully. Changes will be reflected after refreshing.")
                if col_d.button("Delete", key=f"wdl_{r['id']}"):
                    delete_walking(r["id"])
                    st.warning("Deleted successfully. Changes will be reflected after refreshing.")

# ----- Other activity records -----
with TAB_ACT:
    al = list_activity()
    if not al:
        st.info("No other activity records found.")
    else:
        for r in al:
            with st.expander(f"ID {r['id']} | {r['date']} | {r['activity_type']}"):
                c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                d = c1.date_input("Date", value=date.fromisoformat(r["date"]), format="YYYY-MM-DD", key=f"ad_{r['id']}")
                at = c2.text_input("Activity type", value=r["activity_type"], key=f"at_{r['id']}")
                mets = c3.number_input("METs", min_value=0.0, step=0.1, value=float(r["mets"]), format="%.1f", key=f"am_{r['id']}")
                mins = c4.number_input("Duration (minutes)", min_value=0.0, step=1.0, value=float(r["minutes"]), format="%.1f", key=f"amin_{r['id']}")
                col_u, col_d = st.columns([1, 1])
                if col_u.button("Update", key=f"au_{r['id']}"):
                    update_activity(r["id"], d.strftime("%Y-%m-%d"), at.strip() or "Activity", float(mets), float(mins))
                    st.success("Updated successfully. Changes will be reflected after refreshing.")
                if col_d.button("Delete", key=f"adl_{r['id']}"):
                    delete_activity(r["id"])
                    st.warning("Deleted successfully. Changes will be reflected after refreshing.")
