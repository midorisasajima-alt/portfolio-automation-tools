
# =============================
# pages/10_時間の割合.py
# -----------------------------
import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime
from db import list_routine, list_efficiency, list_tasks
from msal_auth import get_access_token
from graph_client import list_events
# 先頭の import に追加
from utils import graph_dt_to_london

st.title("10) 時間の割合（24hベース）")

col = st.columns(2)
with col[0]:
    s = st.date_input("開始日", value=date.today(), format="YYYY-MM-DD")
with col[1]:
    e = st.date_input("終了日", value=date.today(), format="YYYY-MM-DD")

st.markdown("---")
# 予定（Outlook）時間合計
def total_ms_hours(s, e):
    try:
        token = get_access_token()
    except Exception:
        return 0.0
    cur = s
    mins = 0
    while cur <= e:
        evs = list_events(token, cur.isoformat())
        for ev in evs:
            st_dt = graph_dt_to_london(ev.get("start"))
            en_dt = graph_dt_to_london(ev.get("end"))
            if st_dt and en_dt:
                mins += max(0, int((en_dt - st_dt).total_seconds() / 60))
                cur = cur.fromordinal(cur.toordinal()+1)
    return mins/60.0

# 生活（ルーチン）時間＝期間日数 * (hours/period_days)

def total_routine_hours(s, e):
    days = (e - s).days + 1
    tot = 0.0
    for r in list_routine():
        tot += days * (float(r['hours']) / int(r['period_days']))
    return tot

# 睡眠＝生活から分ける or ここでは routine に「睡眠」エントリを作る運用を推奨
# ここでは単純化のため、タイトルが「睡眠」のものを睡眠として合算し、自由時間生活から差し引く

def split_sleep(s, e):
    days = (e - s).days + 1
    sleep = 0.0
    other = 0.0
    for r in list_routine():
        hours = days * (float(r['hours']) / int(r['period_days']))
        if r['title'] == '睡眠':
            sleep += hours
        else:
            other += hours
    return sleep, other

# 課題：Σ( かかる時間×(1-達成率)/締切までの日数 ) の合計を能率で補正

def total_task_hours(s, e):
    from datetime import datetime as dt, timedelta

    tasks = list_tasks(active=True)

    def norm_progress(p):
        try:
            p = float(p)
        except:
            return 0.0
        # 0–100で入っている場合に備えた防御
        if p > 1.0:
            p = p / 100.0
        return min(max(p, 0.0), 1.0)

    # 残り必要時間をタスク毎に初期化
    rem = []
    dues = []
    for t in tasks:
        R = float(t.get('required_hours', 0.0) or 0.0)
        P = norm_progress(t.get('progress', 0.0) or 0.0)
        remaining = max(0.0, R * (1.0 - P))
        rem.append(remaining)
        dues.append(dt.fromisoformat(f"{t['due_date']}T{t['due_time']}"))

    # 能率の代表値（平均）。未設定や非正なら1.0にフォールバック
    effs = list_efficiency()
    eff_list = []
    for r in effs:
        try:
            eff_list.append(float(r['efficiency']))
        except:
            pass
    eff = (sum(eff_list) / len(eff_list)) if eff_list else 1.0
    if eff <= 0:
        eff = 1.0

    total = 0.0
    day = s
    one_day = timedelta(days=1)
    SEC_PER_DAY = 86400.0

    while day <= e:
        day_start = dt.combine(day, dt.min.time())
        for i, t in enumerate(tasks):
            if rem[i] <= 0.0:
                continue
            due = dues[i]
            delta_days = (due - day_start).total_seconds() / SEC_PER_DAY

            if delta_days <= 0.0:
                # 期限超過：この日に残りを全て割当
                alloc = rem[i]
            else:
                # 期限までの実数日で均等割（当日含意）
                alloc = rem[i] / delta_days

            # 数値安定化
            if alloc < 0.0:
                alloc = 0.0
            if alloc > rem[i]:
                alloc = rem[i]

            rem[i] -= alloc
            total += alloc

        day += one_day

    return total / eff

ms_h = total_ms_hours(s, e)
sleep_h, life_other_h = split_sleep(s, e)
# life_other_h には「睡眠以外の生活ルーチン」合計が入る

# 課題
work_h = total_task_hours(s, e)

# 自由時間＝24h*日数 −（予定＋生活＋睡眠＋課題）
N = (e - s).days + 1
other = max(0.0, 24.0*N - (ms_h + life_other_h + sleep_h + work_h))

src = pd.DataFrame({
    "category": ["予定","生活","睡眠","課題","freetime"],
    "hours": [ms_h, life_other_h, sleep_h, work_h, other]
})
c1,c2 = st.columns([1,1])
with c2:
    st.dataframe(src, use_container_width=True)
    # --- ドーナツチャート with 白文字ラベル ---
with c1:
    CAT_ORDER = ["freetime","予定", "生活", "睡眠", "課題"]
    MUTED_BLUE = "#4A6FA5"
    OTHER_GREEN = "#74C476"
    colors = [MUTED_BLUE if cat != "freetime" else OTHER_GREEN for cat in CAT_ORDER]

    df = src.copy()
    df["category"] = pd.Categorical(df["category"], categories=CAT_ORDER, ordered=True)
    df = df[df["hours"] > 0]

    # 本体
    pie = alt.Chart(df).mark_arc(outerRadius=140, innerRadius=70).encode(
        theta=alt.Theta("hours:Q", stack=True),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=CAT_ORDER, range=colors),
            legend=alt.Legend(title="カテゴリ"),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="カテゴリ"),
            alt.Tooltip("hours:Q", title="時間", format=",.2f"),
        ],
    )

    # カテゴリ名を白文字で内側に表示
    labels = alt.Chart(df).mark_text(
        radius=105,  # 内外半径の中間あたり (70〜140 → 約105)
        size=12,
        fontWeight="bold",
        color="white",
    ).encode(
        theta=alt.Theta("hours:Q", stack=True),
        text="category:N",
    )

    st.altair_chart(pie + labels, use_container_width=True)
