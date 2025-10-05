from __future__ import annotations
import streamlit as st
from db import list_tasks, list_recent_done, all_categories
from db import STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING,set_task_status

st.set_page_config(page_title="タスク一覧", layout="wide")
st.title("タスク一覧")

title_filter = st.text_input("タスク名で検索")
date_filter = st.date_input("作成日で検索（任意）", value=None)
date_str = date_filter.strftime("%Y-%m-%d") if date_filter else None

with st.expander("種類・重要度で絞り込み", expanded=False):
    DEFAULT_CATS = ["仕事","学業","人間関係","生活・健康","趣味・余暇","財務"]
    cats = sorted(set((all_categories() or []) + DEFAULT_CATS))
    sel_categories = st.multiselect("種類（複数可）", options=cats)
    imp_min, imp_max = st.slider("重要度", 1, 100, (1,100))

def _match(row) -> bool:
    if sel_categories and (row["category"] not in sel_categories):
        return False
    try:
        imp = int(row["importance"])
    except Exception:
        return False
    return imp_min <= imp <= imp_max
status_map = {"アクティブ": "active", "非アクティブ": "inactive", "待ち": "waiting", "完了": "done"}
inv_status_map = {v: k for k, v in status_map.items()}
def _section(label, status_code: str, key_prefix: str):
    st.subheader(label)
    items = list_tasks(search_title=title_filter or None, date_str=date_str, status=status_code)
    items = [t for t in items if _match(t)]
    if not items:
        st.write("該当なし")
        return
    expected_default = status_map[label]
    for t in items:
        cols = st.columns([6,1,1,1])
    
        with cols[0]:
            st.write(f"・{t['title']}（{t['category']}｜重要:{t['importance']} 緊急:{t['urgency']}）")
            

        with cols[1]:
            # 現在状態（行にstatusが無ければセクションの既定へ）
            code = t["status"] if ("status" in t.keys()) else expected_default
            current = inv_status_map.get(code, inv_status_map[expected_default])

            new_status = st.selectbox(
                "状態",
                options=list(status_map.keys()),
                index=list(status_map.keys()).index(current),
                key=f"status_{key_prefix}_{t['id']}",
                label_visibility="collapsed",
            )
            if new_status != current:
                set_task_status(int(t["id"]), status_map[new_status])
                st.rerun()

        with cols[2]:
            if st.button("詳細へ", key=f"{key_prefix}_{t['id']}"):
                st.session_state.search_selected_id = int(t["id"])
                try:
                    st.switch_page("pages/6_タスク検索と編集.py")
                except Exception:
                    st.rerun()

        with cols[3]:
            if t["url"]:
                st.link_button("Doc", t["url"])


_section("アクティブ", STATUS_ACTIVE, "open_active")
st.divider()
_section("非アクティブ", STATUS_INACTIVE, "open_inactive")
st.divider()
_section("待ち", STATUS_WAITING, "open_waiting")

st.divider()
st.subheader("完了（最新20件）")
done = list_recent_done(limit=20)
if not done:
    st.write("まだありません。")
else:
    status_map = {"アクティブ":"active","非アクティブ":"inactive","待ち":"waiting","完了":"done"}
    inv_status_map = {v:k for k,v in status_map.items()}
    for t in done:
        cols = st.columns([6,1,1,1])
        
        with cols[0]:
            completed_at = t["completed_at"] if ("completed_at" in t.keys()) else "-"
            st.write(f"・{t['title']}（完了: {completed_at}｜{t['category']}）")

        with cols[1]:
            # sqlite3.Row は .get を持たないためキー存在チェック
            code = t["status"] if ("status" in t.keys()) else "done"
            current = inv_status_map.get(code, "完了")
            new_status = st.selectbox(
                "状態",
                options=list(status_map.keys()),
                index=list(status_map.keys()).index(current),
                key=f"status_{t['id']}",
                label_visibility="collapsed"
            )
            if new_status != current:
                from db import set_task_status
                set_task_status(int(t["id"]), status_map[new_status])
                st.rerun()  # 状態変更後に一覧を即反映

        with cols[2]:
            if st.button("詳細へ", key=f"done_{t['id']}"):
                st.session_state.search_selected_id = int(t["id"])
                try:
                    st.switch_page("pages/6_タスク検索と編集.py")
                except Exception:
                    st.rerun()

        with cols[3]:
            if t["url"]:
                st.link_button("Doc", t["url"])
