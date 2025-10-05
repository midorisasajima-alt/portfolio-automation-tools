from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from db import init_db, list_tasks, all_categories, get_task, set_task_status
from db import STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, STATUS_DONE
st.set_page_config(page_title="タスクマップ", layout="wide")

st.title("タスクマップ（重要度×緊急度）")

# 状態フィルタ
status_map = {"アクティブ":STATUS_ACTIVE, "非アクティブ":STATUS_INACTIVE, "待ち":STATUS_WAITING, "完了":STATUS_DONE}
sel = st.multiselect("表示する状態", options=list(status_map.keys()),
                     default=["アクティブ","非アクティブ","待ち"],
                     help="散布図に表示するタスクの状態")
sel_codes = [status_map[s] for s in sel] if sel else list(status_map.values())

tasks = list_tasks(status=sel_codes)
if not tasks:
    st.info("表示対象のタスクがありません。")
    st.stop()

df = pd.DataFrame([{
    "id": t["id"],
    "title": t["title"],
    "importance": int(t["importance"]),
    "urgency": int(t["urgency"]),
    "category": t["category"],
    "status": t["status"]
} for t in tasks])

with st.expander("データ確認", expanded=False):
    st.write(f"レコード数: {len(df)}")
    st.dataframe(df[["id","title","importance","urgency","category","status"]])

fig = px.scatter(
    df, x="urgency", y="importance", color="category",
    hover_name="title",
    hover_data={"id":True, "urgency":True, "importance":True, "category":True, "status":True},
    labels={"urgency":"緊急度(1-100)", "importance":"重要度(1-100)"},
    range_x=[0.5,100.5], range_y=[0.5,100.5], height=650,
    custom_data=["id"]
)
fig.update_traces(marker=dict(size=14, line=dict(width=0)))
st.plotly_chart(fig, use_container_width=True)

st.caption("詳細編集は「タスク検索と編集」ページから行えます。")
