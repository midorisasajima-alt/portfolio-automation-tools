
import streamlit as st
from typing import List, Dict
from data_store import ALL_STATUSES

STATUS_LABELS = ["アクティブ","非アクティブ","待ち","完了"]

def group_by_status(tasks: List[Dict]) -> dict:
    buckets = {k: [] for k in STATUS_LABELS}
    for t in tasks:
        buckets.get(t.get("status","アクティブ"), []).append(t)
    return buckets

def render_task_line(owner: str, t: Dict, status_key: str, on_change_status, on_detail, doc_right=True):
    cols = st.columns([8,1.2,1.2,1.2] if doc_right else [9,1.5,1.5])
    with cols[0]:
        subtitle = t["name"]
        meta = t.get("memo","").strip()
        if meta:
            st.markdown(f"• **{subtitle}**  \n<span style='opacity:0.75;'>{meta[:120] + ('…' if len(meta)>120 else '')}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"• **{subtitle}**", unsafe_allow_html=True)
    with cols[1]:
        new_status = st.selectbox("状態", ALL_STATUSES,
                                  index=ALL_STATUSES.index(t.get("status","アクティブ")),
                                  key=status_key, label_visibility="collapsed")
        if new_status != t.get("status"):
            on_change_status(t["id"], new_status)
            st.experimental_rerun()
    with cols[2]:
        if st.button("詳細へ", key=f"detail_{t['id']}"):
            on_detail(t["id"])
    if doc_right:
        with cols[3]:
            url = t.get("url","").strip()
            if url:
                st.link_button("doc", url)
            else:
                st.button("doc", disabled=True, key=f"doc_{t['id']}")
    st.divider()

def render_sections(owner: str, tasks: List[Dict], on_change_status, on_detail, show_doc=True):
    buckets = group_by_status(tasks)
    order = ["アクティブ","非アクティブ","待ち","完了"]
    for sec in order:
        items = buckets.get(sec, [])
        st.subheader(sec)
        for t in items:
            render_task_line(owner, t, status_key=f"status_{owner}_{t['id']}",
                             on_change_status=on_change_status,
                             on_detail=on_detail,
                             doc_right=show_doc)
        if not items:
            st.caption("（なし）")
