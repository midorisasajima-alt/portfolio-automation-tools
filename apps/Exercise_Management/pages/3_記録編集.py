# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
from db import list_walking, list_activity, update_walking, update_activity, delete_walking, delete_activity

st.set_page_config(page_title="記録編集", layout="wide")

TAB_WALK, TAB_ACT = st.tabs(["歩行", "その他の運動"])

with TAB_WALK:
    wl = list_walking()
    if not wl:
        st.info("歩行記録はありません。")
    else:
        for r in wl:
            with st.expander(f"ID {r['id']} | {r['date']} | steps {r['steps']}"):
                c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
                d = c1.date_input("日付", value=date.fromisoformat(r["date"]), format="YYYY-MM-DD", key=f"wd_{r['id']}")
                steps = c2.number_input("歩数", min_value=0, step=100, value=int(r["steps"]), key=f"ws_{r['id']}")
                step_len = c3.number_input("歩幅(m/歩)", min_value=0.3, max_value=1.2, step=0.01, value=float(r["step_length_m"]), format="%.2f", key=f"wsl_{r['id']}")
                speed = c4.number_input("速度(m/分)", min_value=20.0, max_value=140.0, step=1.0, value=float(r["speed_m_per_min"]), format="%.1f", key=f"wsp_{r['id']}")
                col_u, col_d = st.columns([1,1])
                if col_u.button("更新", key=f"wu_{r['id']}"):
                    update_walking(r["id"], d.strftime("%Y-%m-%d"), int(steps), float(step_len), float(speed))
                    st.success("更新しました。再表示で反映されます。")
                if col_d.button("削除", key=f"wdl_{r['id']}"):
                    delete_walking(r["id"])
                    st.warning("削除しました。再表示で反映されます。")

with TAB_ACT:
    al = list_activity()
    if not al:
        st.info("その他の運動記録はありません。")
    else:
        for r in al:
            with st.expander(f"ID {r['id']} | {r['date']} | {r['activity_type']}"):
                c1, c2, c3, c4 = st.columns([1,1,1,1])
                d = c1.date_input("日付", value=date.fromisoformat(r["date"]), format="YYYY-MM-DD", key=f"ad_{r['id']}")
                at = c2.text_input("種目", value=r["activity_type"], key=f"at_{r['id']}")
                mets = c3.number_input("METs", min_value=0.0, step=0.1, value=float(r["mets"]), format="%.1f", key=f"am_{r['id']}")
                mins = c4.number_input("分数", min_value=0.0, step=1.0, value=float(r["minutes"]), format="%.1f", key=f"amin_{r['id']}")
                col_u, col_d = st.columns([1,1])
                if col_u.button("更新", key=f"au_{r['id']}"):
                    update_activity(r["id"], d.strftime("%Y-%m-%d"), at.strip() or "種目", float(mets), float(mins))
                    st.success("更新しました。再表示で反映されます。")
                if col_d.button("削除", key=f"adl_{r['id']}"):
                    delete_activity(r["id"])
                    st.warning("削除しました。再表示で反映されます。")
