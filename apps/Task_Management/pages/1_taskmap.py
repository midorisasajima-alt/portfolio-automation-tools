from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from db import init_db, list_tasks, all_categories, get_task, set_task_status
from db import STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, STATUS_DONE

st.set_page_config(page_title="Task Map", layout="wide")

st.title("Task Map (Importance × Urgency)")

# Status filter
status_map = {
    "Active": STATUS_ACTIVE,
    "Inactive": STATUS_INACTIVE,
    "Waiting": STATUS_WAITING,
    "Completed": STATUS_DONE
}
sel = st.multiselect(
    "Select status to display",
    options=list(status_map.keys()),
    default=["Active", "Inactive", "Waiting"],
    help="Select which task statuses to show in the scatter plot"
)
sel_codes = [status_map[s] for s in sel] if sel else list(status_map.values())

tasks = list_tasks(status=sel_codes)
if not tasks:
    st.info("No tasks to display.")
    st.stop()

df = pd.DataFrame([{
    "id": t["id"],
    "title": t["title"],
    "importance": int(t["importance"]),
    "urgency": int(t["urgency"]),
    "category": t["category"],
    "status": t["status"]
} for t in tasks])

with st.expander("Data overview", expanded=False):
    st.write(f"Number of records: {len(df)}")
    st.dataframe(df[["id", "title", "importance", "urgency", "category", "status"]])

fig = px.scatter(
    df,
    x="urgency",
    y="importance",
    color="category",
    hover_name="title",
    hover_data={
        "id": True,
        "urgency": True,
        "importance": True,
        "category": True,
        "status": True
    },
    labels={"urgency": "Urgency (1–100)", "importance": "Importance (1–100)"},
    range_x=[0.5, 100.5],
    range_y=[0.5, 100.5],
    height=650,
    custom_data=["id"]
)
fig.update_traces(marker=dict(size=14, line=dict(width=0)))
st.plotly_chart(fig, use_container_width=True)

st.caption("For detailed editing, please go to the 'Task Search and Edit' page.")
