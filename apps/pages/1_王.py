
import streamlit as st
from data_store import list_tasks, update_task
from ui_helpers import render_sections

st.set_page_config(page_title="王のタスク", layout="wide")
st.subheader("苛政猛於虎")
st.text("苛烈な統治は虎よりも恐ろしい")
st.text("ー『礼記』檀弓下よりー")
st.markdown("---")

q = st.text_input("タスク名で検索", "")
tasks = list_tasks("王")
if q: tasks = [t for t in tasks if q in t.get("name","")]

def on_change_status(task_id, new_status):
    update_task("王", task_id, status=new_status)
def on_detail(task_id):
    st.session_state["edit_owner"] = "王"
    st.session_state["edit_task_id"] = task_id
    try:
        st.switch_page("pages/7_タスク編集と追加.py")
    except Exception:
        st.info("上部のページ一覧から「タスク編集と追加」を開いてください。")

render_sections("王", tasks, on_change_status, on_detail, show_doc=True)
