#Before English translation

import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from data_store import list_tasks

st.set_page_config(page_title="誤差分析（百司｜インデックス軸）", layout="wide")
st.header("誤差分析")

tasks = list_tasks("百司")

# Build error list sorted by timestamp; x-axis = 1..N
records = []
for t in tasks:
    est = t.get("est_hours")
    act = t.get("actual_hours")
    if est is None or act is None:
        continue
    try:
        est = float(est); act = float(act)
    except:
        continue
    if est <= 0:
        continue
    err = (act - est) / est
    ts = t.get("updated_at") or t.get("created_at")
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except:
        dt = None
    records.append((dt, err, t.get("name","")))

if not records:
    st.info("誤差率データがまだありません。百司ページで概算hと実績hを保存してください。")
    st.stop()

# Sort by timestamp if available; otherwise by insertion order
records.sort(key=lambda x: (x[0] is None, x[0]))

ys = [r[1] for r in records]
xs = list(range(1, len(ys)+1))

# Optional: windowed smoothing toggle
smooth = st.checkbox("3点移動平均を重ねる", value=False)

fig, ax = plt.subplots(figsize=(8,4), facecolor="black")
ax.set_facecolor("black")
ax.plot(xs, ys, marker="o")
ax.set_xlabel("index", color="white")
ax.set_ylabel("error rate", color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")
ax.grid(True, alpha=0.2)
ax.axhline(0, linestyle="--", linewidth=1, alpha=0.5, color="white") # 0基準の点線

if smooth and len(ys) >= 3:
    sm = []
    for i in range(len(ys)):
        a = max(0, i-1); b = min(len(ys), i+2)
        sm.append(sum(ys[a:b])/(b-a))
    ax.plot(xs, sm)

st.pyplot(fig)
st.caption("誤差率 = (実績h − 概算h) / 概算h。横軸は記録順（更新日時の昇順）。")
