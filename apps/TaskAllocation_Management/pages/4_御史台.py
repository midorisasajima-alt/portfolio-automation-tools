#Before English translation

import streamlit as st
from data_store import list_tasks, update_task
from ui_helpers import render_task_line

st.set_page_config(page_title="御史台のタスク", layout="wide")
st.header("御史台のタスク")

tasks = list_tasks("御史台")

st.subheader("一覧")
for t in tasks:
    def on_change_status(task_id, new_status):
        update_task("御史台", task_id, status=new_status)
    def on_detail(task_id):
        st.session_state["edit_owner"] = "御史台"
        st.session_state["edit_task_id"] = task_id
        try:
            st.switch_page("pages/7_タスク編集と追加.py")
        except Exception:
            st.info("上部のページ一覧から「タスク編集と追加」を開いてください。")
    render_task_line("御史台", t, status_key=f"status_yushi_{t['id']}", on_change_status=on_change_status, on_detail=on_detail, doc_right=True)
    c1, c2, c3 = st.columns([1,1,6])
    with c1:
        st.link_button("監査", "https://chatgpt.com/g/g-p-68e795917f04819182d2e9ac46b24c68/project")
    with c2:
        st.link_button("記録", "https://drive.google.com/drive/u/0/folders/1-rlIypG0BsDctYyyL77JlTDJSm5KpBNX")
    st.caption(f"作成: {t.get('created_at','')} / 更新: {t.get('updated_at','')}")
    st.divider()
