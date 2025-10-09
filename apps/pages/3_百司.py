
import streamlit as st
from data_store import list_tasks, update_task, ALL_STATUSES

st.set_page_config(page_title="百司のタスク", layout="wide")
st.header("百司のタスク")

q = st.text_input("タスク名で検索", "")

tasks = list_tasks("百司")
if q:
    tasks = [t for t in tasks if q in t.get("name","")]

from collections import defaultdict
buckets = defaultdict(list)
for t in tasks:
    buckets[t.get("status","アクティブ")].append(t)

order = ["アクティブ","非アクティブ","待ち","完了"]
for sec in order:
    items = buckets.get(sec, [])
    st.subheader(sec)
    if not items:
        st.caption("（なし）")
        continue
    for t in items:
        with st.container(border=True):
            cols = st.columns([6,1.2,1.2,1.2,2.2,2.2])
            with cols[0]:
                subtitle = t["name"]
                meta = t.get("memo","") or ""
                if meta:
                    st.markdown(f"**{subtitle}**  \n<span style='opacity:0.75;'>{meta[:120] + ('…' if len(meta)>120 else '')}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**{subtitle}**", unsafe_allow_html=True)
                st.caption(f"作成: {t.get('created_at','')} / 更新: {t.get('updated_at','')}")
            with cols[1]:
                new_status = st.selectbox("状", ALL_STATUSES,
                                          index=ALL_STATUSES.index(t.get("status","アクティブ")),
                                          key=f"status_hyakushi_{t['id']}", label_visibility="collapsed")
                if new_status != t.get("status"):
                    update_task("百司", t["id"], status=new_status)
                    st.experimental_rerun()
            with cols[2]:
                if st.button("詳細へ", key=f"edit_hyakushi_{t['id']}"):
                    st.session_state["edit_owner"] = "百司"
                    st.session_state["edit_task_id"] = t["id"]
                    try:
                        st.switch_page("pages/7_タスク編集と追加.py")
                    except Exception:
                        st.info("上部のページ一覧から「タスク編集と追加」を開いてください。")
            with cols[3]:
                url = t.get("url","").strip()
                if url:
                    st.link_button("doc", url)
                else:
                    st.button("doc", disabled=True, key=f"doc_hyakushi_{t['id']}")
            with cols[4]:
                est = t.get("est_hours", None)
                est_val = 0.0 if est is None else float(est)
                est_val = st.number_input("概算h", min_value=0.0, step=0.5, value=est_val, key=f"est_{t['id']}")
            with cols[5]:
                act = t.get("actual_hours", None)
                act_val = 0.0 if act is None else float(act)
                act_val = st.number_input("実績h", min_value=0.0, step=0.5, value=act_val, key=f"act_{t['id']}")
        if st.button("保存", key=f"save_{t['id']}"):
            update_task("百司", t["id"], est_hours=float(est_val), actual_hours=float(act_val))
            st.success("保存しました。")
        st.divider()
