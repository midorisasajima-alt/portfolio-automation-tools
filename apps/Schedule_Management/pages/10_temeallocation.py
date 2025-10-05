# =============================
# pages/10_TimeAllocation.py
# -----------------------------
import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime
from db import list_routine, list_efficiency, list_tasks
from msal_auth import get_access_token
from graph_client import list_events
from utils import graph_dt_to_london

st.title("10) Time Allocation (24h Base)")

col = st.columns(2)
with col[0]:
    s = st.date_input("Start Date", value=date.today(), format="YYYY-MM-DD")
with col[1]:
    e = st.date_input("End Date", value=date.today(), format="YYYY-MM-DD")

st.markdown("---")

# Total hours from Outlook events across the period
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
        # move to next day
        cur = cur.fromordinal(cur.toordinal() + 1)
    return mins / 60.0

# Routine time = number of days * (hours / period_days)
def total_routine_hours(s, e):
    days = (e - s).days + 1
    tot = 0.0
    for r in list_routine():
        tot += days * (float(r['hours']) / int(r['period_days']))
    return tot

# Split out sleep from routine:
# Sum entries whose title is "Sleep" and treat the rest as other routine.
def split_sleep(s, e):
    days = (e - s).days + 1
    sleep = 0.0
    other = 0.0
    for r in list_routine():
        hours = days * (float(r['hours']) / int(r['period_days']))
        if r['title'] == 'Sleep':
            sleep += hours
        else:
            other += hours
    return sleep, other

# Tasks: sum over days of (remaining_hours / days_until_due), adjusted by efficiency
def total_task_hours(s, e):
    from datetime import datetime as dt, timedelta

    tasks = list_tasks(active=True)

    def norm_progress(p):
        try:
            p = float(p)
        except:
            return 0.0
        if p > 1.0:
            p = p / 100.0
        return min(max(p, 0.0), 1.0)

    # Initialize remaining time per task
    rem = []
    dues = []
    for t in tasks:
        R = float(t.get('required_hours', 0.0) or 0.0)
        P = norm_progress(t.get('progress', 0.0) or 0.0)
        remaining = max(0.0, R * (1.0 - P))
        rem.append(remaining)
        dues.append(dt.fromisoformat(f"{t['due_date']}T{t['due_time']}"))

    # Representative efficiency (mean). Fallback to 1.0 if unset/non-positive.
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
        for i, _t in enumerate(tasks):
            if rem[i] <= 0.0:
                continue
            due = dues[i]
            delta_days = (due - day_start).total_seconds() / SEC_PER_DAY

            if delta_days <= 0.0:
                # overdue: allocate all remaining today
                alloc = rem[i]
            else:
                # even allocation across remaining real days (inclusive of today)
                alloc = rem[i] / delta_days

            if alloc < 0.0:
                alloc = 0.0
            if alloc > rem[i]:
                alloc = rem[i]

            rem[i] -= alloc
            total += alloc

        day += one_day

    return total / eff

ms_h = total_ms_hours(s, e)
sleep_h, life_other_h = split_sleep(s, e)  # life_other_h = routine excluding sleep
work_h = total_task_hours(s, e)

# Free time = 24h * days − (schedule + routine + sleep + tasks)
N = (e - s).days + 1
other = max(0.0, 24.0 * N - (ms_h + life_other_h + sleep_h + work_h))

src = pd.DataFrame({
    "category": ["Schedule", "Routine", "Sleep", "Tasks", "Free Time"],
    "hours": [ms_h, life_other_h, sleep_h, work_h, other]
})

c1, c2 = st.columns([1, 1])
with c2:
    st.dataframe(src, use_container_width=True)

with c1:
    CAT_ORDER = ["Free Time", "Schedule", "Routine", "Sleep", "Tasks"]
    MUTED_BLUE = "#4A6FA5"
    OTHER_GREEN = "#74C476"
    colors = [MUTED_BLUE if cat != "Free Time" else OTHER_GREEN for cat in CAT_ORDER]

    df = src.copy()
    df["category"] = pd.Categorical(df["category"], categories=CAT_ORDER, ordered=True)
    df = df[df["hours"] > 0]

    pie = alt.Chart(df).mark_arc(outerRadius=140, innerRadius=70).encode(
        theta=alt.Theta("hours:Q", stack=True),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=CAT_ORDER, range=colors),
            legend=alt.Legend(title="Category"),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="Category"),
            alt.Tooltip("hours:Q", title="Hours", format=",.2f"),
        ],
    )

    labels = alt.Chart(df).mark_text(
        radius=105,
        size=12,
        fontWeight="bold",
        color="white",
    ).encode(
        theta=alt.Theta("hours:Q", stack=True),
        text="category:N",
    )

    st.altair_chart(pie + labels, use_container_width=True)
