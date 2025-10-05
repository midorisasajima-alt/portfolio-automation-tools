# ========================= utils.py（タイル式リング：丸が複数増える方式） =========================
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from typing import List, Dict
import math
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from config import GOAL_METS_MIN_PER_DAY, COLORS, LIGHT_COLORS
from db import list_walking, list_activity

# ---- Matplotlib 全体テーマ（ダークスタイル） ----
mpl.rcParams.update({
    "figure.facecolor": "black",
    "axes.facecolor": "black",
    "axes.edgecolor": "#888888",
    "axes.labelcolor": "white",
    "axes.titlecolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "text.color": "white",
    "grid.color": "#444444",
    "legend.facecolor": "#111111",
    "legend.edgecolor": "#444444",
})

# ---- 物理量の変換 ----
# ACSM 平地歩行 VO2式: VO2 (ml/kg/min) = 3.5 + 0.1 * v(m/min)
# METs = VO2 / 3.5 = 1 + 0.0285714 * v
def speed_to_mets(speed_m_per_min: float) -> float:
    return 1.0 + 0.0285714 * speed_m_per_min

def walking_mets_min(steps: int, step_length_m: float, speed_m_per_min: float) -> float:
    """
    運動中のみのMETs・分を計上（安静の1 METは控除）
    METs・分 = (METs - 1) * 分
    """
    if speed_m_per_min <= 0:
        return 0.0
    dist_m = steps * step_length_m
    minutes = dist_m / speed_m_per_min
    mets_excess = max(0.0, speed_to_mets(speed_m_per_min) - 1.0)
    return mets_excess * minutes

def activity_mets_min(mets: float, minutes: float) -> float:
    """
    その他種目は「運動中のみ」を入力想定として、そのまま METs × 分で計上
    （安静 1 MET を含めない）
    """
    return max(0.0, mets) * max(0.0, minutes)

# ---- 集計ユーティリティ ----
def daterange_days(start: date, end: date) -> int:
    return (end - start).days + 1

def load_daily_totals(start: date, end: date) -> pd.DataFrame:
    """
    指定期間の1日単位合計（歩行・その他・合計）を返す
    """
    days = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"date": days.date})
    df["date_str"] = df["date"].astype(str)

    w = list_walking(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    a = list_activity(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

    wm: Dict[str, float] = {}
    for r in w:
        dstr = r["date"]
        wm.setdefault(dstr, 0.0)
        wm[dstr] += walking_mets_min(r["steps"], r["step_length_m"], r["speed_m_per_min"])

    am: Dict[str, float] = {}
    for r in a:
        dstr = r["date"]
        am.setdefault(dstr, 0.0)
        am[dstr] += activity_mets_min(r["mets"], r["minutes"])

    df["walking_mets_min"]  = df["date_str"].map(lambda d: wm.get(d, 0.0))
    df["activity_mets_min"] = df["date_str"].map(lambda d: am.get(d, 0.0))
    df["total_mets_min"]    = df["walking_mets_min"] + df["activity_mets_min"]
    return df[["date", "walking_mets_min", "activity_mets_min", "total_mets_min"]]

def compute_binned_totals(start: date, end: date, window: int) -> pd.DataFrame:
    """
    推移グラフ用：window日ごとの移動合計と目標
    出力: period_end, window_total, goal_total
    """
    base = load_daily_totals(start, end).sort_values("date")
    base["window_total"] = base["total_mets_min"].rolling(window=window, min_periods=1).sum()
    base["goal_total"]   = GOAL_METS_MIN_PER_DAY * window
    out = base[["date", "window_total", "goal_total"]].rename(columns={"date": "period_end"})
    return out

def summarize_by_item(start: date, end: date) -> pd.DataFrame:
    """
    内訳用：歩行（1項目）＋その他の運動（種目名ごと）で期間合計を返す
    columns: [name, mets_min]
    """
    rows = []

    # Walking
    w = list_walking(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    w_tot = 0.0
    for r in w:
        w_tot += walking_mets_min(r["steps"], r["step_length_m"], r["speed_m_per_min"])
    rows.append({"name": "Walking", "mets_min": w_tot})

    # Activities by type
    a = list_activity(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    agg: Dict[str, float] = {}
    for r in a:
        agg.setdefault(r["activity_type"], 0.0)
        agg[r["activity_type"]] += activity_mets_min(r["mets"], r["minutes"])
    for k, v in agg.items():
        rows.append({"name": k, "mets_min": v})

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame([{"name": "(no data)", "mets_min": 0.0}])
    return df

# ---- 描画（折れ線・棒） ----
def plot_line_with_goal(df: pd.DataFrame, window_days: int):
    fig, ax = plt.subplots()
    if df.empty:
        ax.set_title("Total: no data")
        return fig

    ax.plot(
        df["period_end"],
        df["window_total"],
        marker="o",
        label=f"Total ({window_days}d sum)",
        color=COLORS.get("activity")
    )
    ax.axhline(
        float(df["goal_total"].iloc[0]) if "goal_total" in df and len(df) else GOAL_METS_MIN_PER_DAY * window_days,
        linestyle="--",
        label=f"Goal ({window_days}d)",
        color=LIGHT_COLORS.get("activity")
    )
    ax.set_xlabel("date")
    ax.set_ylabel("METs·min")
    ax.set_title("METs·min Trend (rolling sum)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    return fig

def plot_bar_top_items(df_items: pd.DataFrame, topk: int = 15):
    fig, ax = plt.subplots()
    if df_items.empty:
        ax.set_title("Items: no data")
        ax.set_xlabel("METs·min")
        return fig

    df_sorted = df_items.sort_values("mets_min", ascending=False).head(topk)
    bars = ax.barh(
        df_sorted["name"],
        df_sorted["mets_min"],
        color=COLORS.get("activity", "#d62728")
    )
    ax.invert_yaxis()
    total_val = float(df_items["mets_min"].sum())
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(f"Items (sum={total_val:.0f} METs·min)")

    for rect in bars:
        val = rect.get_width()
        if val <= 0:
            continue
        y = rect.get_y() + rect.get_height() / 2
        ax.annotate(
            f"{val:.0f}",
            xy=(val, y),
            xytext=(-6, 0),
            textcoords="offset points",
            va="center", ha="right",
            color="white",
            clip_on=True,
        )
    ax.grid(True, axis="x", alpha=0.2)
    return fig

from matplotlib.colors import to_rgba

def _dim(color, alpha=0.45):
    r, g, b, _ = to_rgba(color)
    return (r, g, b, alpha)




# ---- タイル式リング（丸が複数並ぶ）：1枚=1日目標、達成に応じて丸を増やす ----
def plot_pie_goaltile(df_items: pd.DataFrame, days: int, cols: int = 5):
    """
    タイル式リング：1タイル(丸)=1日目標(GOAL_METS_MIN_PER_DAY)

    充填方針：
      - タイル数 n_tiles = max(days, ceil(total/GOAL))
      - 各タイル容量は GOAL で一定
      - 充填順序：左上 → 右へ → 次行左端 → …
      - Walking 最優先で逐次充填（溢れたら次タイルへ）
      - その他種目は“残量の大きい順”で逐次充填（詰め切り）
      - 空きは各タイルごとに Unmet（青）で充填
    """
    # --- 入力と目標 ---
    total = float(df_items["mets_min"].sum()) if not df_items.empty else 0.0
    GOAL = float(GOAL_METS_MIN_PER_DAY)
    if GOAL <= 0:
        fig, ax = plt.subplots()
        ax.set_title("Goal Tiles: The goal is below 0")
        return fig

    # --- データ整形 ---
    parts = df_items.copy()
    parts = parts[parts["mets_min"] > 0]
    if parts.empty:
        parts = pd.DataFrame([{"name": "(no data)", "mets_min": 1.0}])

    walking_total = float(parts.loc[parts["name"] == "Walking", "mets_min"].sum())
    others_df = parts[parts["name"] != "Walking"].copy()
    other_totals = {row["name"]: float(row["mets_min"]) for _, row in others_df.iterrows()}
    other_order = sorted(other_totals.keys(), key=lambda k: other_totals[k], reverse=True)

    # --- タイル数・容量 ---
    tiles_by_total = math.ceil(total / GOAL) if total > 0 else 1
    n_tiles = max(int(days) if days is not None else 1, tiles_by_total)
    n_tiles = max(1, n_tiles)
    caps = [GOAL] * n_tiles

    # --- グリッド配置と“左上起点”の充填順序 ---
    rows = math.ceil(n_tiles / cols)
    grid_indices = []
    for r in range(rows):
        for c in range(0, cols):  # ← 左から右へ
            idx = r * cols + c
            if idx < n_tiles:
                grid_indices.append(idx)

    # --- 色 ---
    walking_color = COLORS.get("activity")
    unmet_color   = COLORS.get("unmet")
    other_color_map = {name: COLORS.get("activity") for name in other_order}

    # 超過タイル用の減光色（存在しない場合は半透明化で代替）
    walking_color_over = COLORS.get("activity_over", _dim(walking_color, 0.45))
    unmet_color_over   = COLORS.get("unmet_over",   _dim(unmet_color,   0.35))
    other_color_map_over = {
        name: COLORS.get(f"{name}_over", _dim(other_color_map[name], 0.45))
        for name in other_order
    }

    # --- 逐次割当 ---
    rem_walk = walking_total
    rem_others = other_totals.copy()
    per_tile_vals = [None] * n_tiles

    for idx in grid_indices:
        cap = caps[idx]
        vals, cols_ = [], []

        # 1) Walking
        if rem_walk > 1e-9 and cap > 1e-9:
            take = min(rem_walk, cap)
            vals.append(take); cols_.append(walking_color)
            rem_walk -= take
            cap -= take

        # 2) Others（残量大きい順に詰め切り）
        if cap > 1e-9:
            for name in other_order:
                if cap <= 1e-9:
                    break
                rem = rem_others.get(name, 0.0)
                if rem <= 1e-9:
                    continue
                take = min(rem, cap)
                vals.append(take); cols_.append(other_color_map[name])
                rem_others[name] = rem - take
                cap -= take

        # 3) Unmet（青で充填）
        if cap > 1e-9:
            vals.append(cap); cols_.append(unmet_color)

        per_tile_vals[idx] = (vals, cols_)

    # --- 描画 ---
    fig_rows, fig_cols = rows, cols
    fig, axes = plt.subplots(fig_rows, fig_cols, figsize=(fig_cols * 2.2, fig_rows * 2.2))
    if fig_rows == 1 and fig_cols == 1:
        axes = [[axes]]
    elif fig_rows == 1:
        axes = [axes]
    elif fig_cols == 1:
        axes = [[ax] for ax in axes]

    for r in range(fig_rows):
        for c in range(fig_cols):
            ax = axes[r][c]
            idx = r * cols + c
            if idx >= n_tiles:
                ax.axis("off"); continue
            vals, cols_tile = per_tile_vals[idx]
            if vals is None or sum(vals) <= 0:
                ax.axis("off"); continue

            # ここで「超過タイル」判定して色を差し替え
            is_overflow = (idx >= int(days) if days is not None else False)
            if is_overflow:
                new_cols = []
                for col in cols_tile:
                    if col == walking_color:
                        new_cols.append(walking_color_over)
                    elif col == unmet_color:
                        new_cols.append(unmet_color_over)
                    else:
                        # other 種目（activity 色）の減光版に置換
                        # 同一色が複数種目で共有される前提なのでマップで判定
                        # 見つからない場合は汎用的に減光
                        replaced = None
                        for name, base_col in other_color_map.items():
                            if col == base_col:
                                replaced = other_color_map_over[name]
                                break
                        new_cols.append(replaced if replaced is not None else _dim(col, 0.45))
                cols_tile = new_cols

            ax.pie(
                vals, labels=None, startangle=90, counterclock=False,
                colors=cols_tile, wedgeprops=dict(edgecolor="none", linewidth=0.6),
            )
            circle = plt.Circle((0, 0), 0.55, color=mpl.rcParams["axes.facecolor"])
            circle.set_edgecolor("none")
            ax.add_artist(circle)
            ax.axis("equal"); ax.set_xticks([]); ax.set_yticks([])

            used_i = sum(v for v, col in zip(vals, cols_tile) if (col != unmet_color and col != unmet_color_over))
            pct = used_i / GOAL * 100.0 if GOAL > 0 else 0.0
            ax.set_title(f"{idx+1} ({pct:.0f}%)", fontsize=9, pad=2, color="white")


    fig.suptitle(
        f"1 tile = {GOAL:.0f} METs·min",
        color="white", y=0.97
    )

    handles = [plt.Line2D([0], [0], marker='o', linestyle='', markerfacecolor=walking_color,
                           markeredgecolor='white', label="Walking")]
    for name in other_order:
        handles.append(plt.Line2D([0], [0], marker='o', linestyle='',
                                  markerfacecolor=other_color_map[name],
                                  markeredgecolor='white', label=name))
    handles.append(plt.Line2D([0], [0], marker='o', linestyle='',
                              markerfacecolor=unmet_color, markeredgecolor='white', label="Unmet"))
    
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    return fig
