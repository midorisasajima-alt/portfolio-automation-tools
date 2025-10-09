
import streamlit as st
from data_store import list_tasks, update_task, SIX_MINISTRIES
from ui_helpers import render_sections

st.set_page_config(page_title="六部のタスク", layout="wide")
st.subheader("君使臣以禮，臣事君以忠")
st.text("主君は礼をもって臣を使い、臣は忠をもって主君に仕える")
st.text("ー『論語』八佾よりー")
st.markdown("---")

tabs = st.tabs(SIX_MINISTRIES)

for i, name in enumerate(SIX_MINISTRIES):
    with tabs[i]:
        q = st.text_input("タスク名で検索", "", key=f"q_{name}")
        tasks = list_tasks(name)
        if q: tasks = [t for t in tasks if q in t.get("name","")]

        def on_change_status(task_id, new_status, _name=name):
            update_task(_name, task_id, status=new_status)
        def on_detail(task_id, _name=name):
            st.session_state["edit_owner"] = _name
            st.session_state["edit_task_id"] = task_id
            try:
                st.switch_page("pages/7_タスク編集と追加.py")
            except Exception:
                st.info("上部のページ一覧から「タスク編集と追加」を開いてください。")

        render_sections(name, tasks, on_change_status, on_detail, show_doc=True)
