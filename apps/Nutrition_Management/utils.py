from datetime import date, timedelta, datetime
import pandas as pd
import math
import matplotlib.pyplot as plt
from typing import Tuple, Dict, List
from db import daily_totals_between, read_goals
from config import COLORS, LIGHT_COLORS, NUTRIENTS
import matplotlib as mpl

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
    




def daterange_days(start: date, end: date) -> int:
    return (end - start).days + 1


def bin_edges(start: date, end: date, window_days: int) -> List[tuple]:
    assert window_days >= 1
    edges = []
    cur = start
    while cur <= end:
        right = min(cur + timedelta(days=window_days-1), end)
        edges.append((cur, right))
        cur = right + timedelta(days=1)
    return edges


def compute_binned_totals(start: date, end: date, window_days: int) -> pd.DataFrame:
    # 日毎合計を取得
    rows = daily_totals_between(start.isoformat(), end.isoformat())
    day_df = pd.DataFrame(rows, columns=["date","Energy","Protein","Fat","Carbohydrate"]).fillna(0)
    if day_df.empty:
        # 空のDFを返す
        return pd.DataFrame(columns=["period_end"] + NUTRIENTS)
    day_df["date"] = pd.to_datetime(day_df["date"])

    periods = bin_edges(start, end, window_days)
    out = []
    for (l, r) in periods:
        mask = (day_df["date"] >= pd.Timestamp(l)) & (day_df["date"] <= pd.Timestamp(r))
        s = day_df.loc[mask, NUTRIENTS].sum()
        out.append({"period_end": r, **s.to_dict()})
    return pd.DataFrame(out)


def plot_line_with_goal(df: pd.DataFrame, nutrient: str, window_days: int):
    fig, ax = plt.subplots()
    if df.empty:
        ax.set_title(f"{nutrient}：no data")
        return fig
    ax.plot(df["period_end"], df[nutrient], marker="o", label=nutrient, color=COLORS[nutrient])
    # 目標線
    goals = read_goals()
    goal_val = goals[nutrient] * window_days
    ax.axhline(goal_val, linestyle="--", label=f"goal({window_days}days)", color=LIGHT_COLORS[nutrient])
    ax.set_xlabel("date")
    ax.set_ylabel(nutrient)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    return fig


def summarize_by_item(start: date, end: date) -> pd.DataFrame:
    # records×itemsから品目別の合計栄養素を集計
    from db import get_conn
    conn = get_conn()
    sql = """
        SELECT i.name, i.genre,
               SUM(r.quantity*i.energy) AS Energy,
               SUM(r.quantity*i.protein) AS Protein,
               SUM(r.quantity*i.fat) AS Fat,
               SUM(r.quantity*i.carbohydrate) AS Carbohydrate
        FROM records r JOIN items i ON r.item_id=i.id
        WHERE r.date BETWEEN ? AND ?
        GROUP BY i.name, i.genre
        ORDER BY i.genre, i.name
    """
    df = pd.read_sql_query(sql, conn, params=(start.isoformat(), end.isoformat()))
    conn.close()
    return df


def plot_pie_breakdown(df_item: pd.DataFrame, nutrient: str, days: int):
    # 目標値と達成の内訳（上位3+その他達成+未達）
    achieved = df_item[nutrient].sum() if not df_item.empty else 0.0
    goals = read_goals()
    target = goals[nutrient] * days
    top = df_item.sort_values(nutrient, ascending=False).head(3)
    other = max(0.0, achieved - top[nutrient].sum())
    unmet = max(0.0, target - achieved)

    labels = []
    sizes = []
    # 上位3
    for _, row in top.iterrows():
        if row[nutrient] > 0:
            labels.append(f"{row['name']} ")
            sizes.append(row[nutrient])
    # その他達成
    if other > 0:
        labels.append("else")
        sizes.append(other)
    # 未達
    if unmet > 0:
        labels.append(" ")
        sizes.append(unmet)

    colors = []
    for lab in labels:
        if lab == " ":
            colors.append(LIGHT_COLORS[nutrient])
        else:
            colors.append(COLORS[nutrient])

    fig, ax = plt.subplots()
    if sum(sizes) == 0:
        ax.set_title(f"{nutrient}：データなし")
        return fig
    ax.pie(
        sizes,
        labels=labels,
        autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(edgecolor="white", linewidth=0.5) # 追加
    )
    ax.axis('equal')
    ax.set_title(f"{nutrient} (target={target:.0f})")
    return fig


def plot_bar_top_items(
    df_item: pd.DataFrame,
    nutrient: str,
    topk: int = 15,
    total_scope: str = "all",  # "topk" または "all"
):
    if df_item.empty:
        fig, ax = plt.subplots()
        ax.set_title(f"{nutrient}：データなし")
        ax.set_xlabel(nutrient)
        return fig
    total_val = float(df_item[nutrient].sum())

    # 上位 topk を抽出
    df_sorted = df_item.sort_values(nutrient, ascending=False).head(topk)

    # 合計の算出（表示中の合計 or 全体合計）
    """
    if total_scope == "all":
        total_val = float(df_item[nutrient].sum())
        scope_label = ""
    else:
        total_val = float(df_sorted[nutrient].sum())
        scope_label = f"上位{len(df_sorted)}合計"
    """

    fig, ax = plt.subplots()
    bars = ax.barh(df_sorted["name"], df_sorted[nutrient], color=COLORS[nutrient])

    ax.invert_yaxis()
    # 合計をラベルに併記
    ax.set_xlabel(f"")
    ax.set_ylabel("")
    ax.set_title(f"{nutrient} (Sum={total_val})")
    ax.margins(x=0.05)  # 内側ラベル向けに余白は控えめ

    # 棒の中に数値（白字）を表示
    for rect in bars:
        val = rect.get_width()
        if val <= 0:
            continue
        y = rect.get_y() + rect.get_height() / 2
        ax.annotate(
            f"{val:.0f}",
            xy=(val, y),
            xytext=(-6, 0),              # 右端から内側へ6pt
            textcoords="offset points",
            va="center", ha="right",
            color="white",
            clip_on=True,
        )

    return fig
