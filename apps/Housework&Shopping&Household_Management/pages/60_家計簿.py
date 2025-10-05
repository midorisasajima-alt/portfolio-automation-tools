import streamlit as st
import matplotlib.pyplot as plt
from db import (
    get_available_months, get_month_total, get_monthly_genre_totals,
    get_month_genre_item_totals, get_monthly_payment_totals
)

st.set_page_config(page_title="家計簿", layout="wide")

months = get_available_months()
if not months:
    st.info("データがありません。先に『買い物_記録』で記録してください。")
    st.stop()

def darken_axes(ax):
    # 背景だけ黒、軸・目盛・ラベルは白に
    ax.set_facecolor('black')
    ax.figure.set_facecolor('black')
    for s in ax.spines.values():
        s.set_color('white')
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')


months_desc = list(sorted(months, reverse=True))
tabs = st.tabs(months_desc)

for tab, month in zip(tabs, months_desc):
    with tab:
        month_total = get_month_total(month)
        
        genre_rows = get_monthly_genre_totals(month)
        if not genre_rows:
            st.info("この月の支出内訳はありません。")
            continue

        # ── 上段：円グラフを横並び ─────────────────────────────
        # ── 共通パラメータ（ファイル先頭付近・円グラフ前などに定義可）
        PIE_FIGSIZE = (5, 5)   # 同一サイズに固定（必要なら6,6等に調整）
        PIE_RADIUS  = 1.0      # 半径を固定
        # 左：ジャンル別内訳 円グラフ
        # ── 上段：3カラム ─────────────────────────────────────────
        col_left, col_mid, col_right = st.columns([10,10,6])

        # 左：ジャンル別の内訳（円グラフ）
        with col_left:
            st.text("ジャンル別の内訳")
            labels = [gname for (_, gname, total) in genre_rows]
            sizes = [float(total) for (_, gname, total) in genre_rows]
            if sum(sizes) <= 0:
                st.info("円グラフに表示できる金額がありません。")
            else:
                fig, ax = plt.subplots(figsize=PIE_FIGSIZE)
                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=None,
                    autopct=lambda p: f"{p:.1f}%",
                    startangle=90,
                    counterclock=False,
                    radius=PIE_RADIUS
                )
                darken_axes(ax)  # ← 追加

                # パーセンテージ表示を白に
                for t in (texts or []):
                    t.set_color("white")
                for t in (autotexts or []):
                    t.set_color("white")

                ax.set_aspect('equal', adjustable='box')
                ax.set_xlim(-1.1, 1.1)
                ax.set_ylim(-1.1, 1.1)

                leg = ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False)
                for txt in leg.get_texts():
                    txt.set_color("white")
                st.pyplot(fig, use_container_width=False)


        # 中央：支払い手段の割合（円グラフ）
        with col_mid:
                # ── 中段：ジャンル別タブ ──────────────────────────────────
            g_tabs = st.tabs([gname for (_, gname, _) in genre_rows])

            # ── 下段：各タブ内の棒グラフ（高額順） ─────────────────────
            for g_tab, (gid, gname, gtotal) in zip(g_tabs, genre_rows):
                with g_tab:
                    items = get_month_genre_item_totals(month, gid)
                    if not items:
                        st.write("記録なし")
                        continue

                    items_sorted = sorted(items, key=lambda x: float(x[1]), reverse=True)
                    names = [name for name, total in items_sorted]
                    totals = [float(total) for name, total in items_sorted]

                    fig2, ax2 = plt.subplots()
                    y_pos = list(range(len(names)))
                    bars = ax2.barh(y_pos, totals)

                    darken_axes(ax2)  # ← 追加

                    ax2.set_yticks(y_pos, labels=names)
                    ax2.set_xlabel("Amount")
                    ax2.set_ylabel("Item")
                    ax2.invert_yaxis()

                    for bar, val in zip(bars, totals):
                        x = bar.get_width()
                        y = bar.get_y() + bar.get_height() / 2
                        ax2.text(x / 2, y, f"{val:,.2f}", va="center", ha="center", color="white")  # ← 文字を白

                    fig2.subplots_adjust(left=0.35)
                    fig2.tight_layout()
                    st.pyplot(fig2)


        # 右：ジャンル別 合計（テキスト）
        with col_right:
            genre_sum_total = sum(float(t) for (_, _, t) in genre_rows)
            st.write(f"合計：{genre_sum_total:,.2f}")
            for _, gname, total in sorted(genre_rows, key=lambda x: float(x[2]), reverse=True):
                st.write(f"- {gname}: {float(total):,.2f}")

        

        st.markdown("---")
        st.text("支払方法の内訳")
        c1,_, c2 = st.columns([10,2,10])
        with c1:
            pay_rows = get_monthly_payment_totals(month)
            if pay_rows:
                pay_labels = [name for (_, name, total) in pay_rows]
                pay_sizes  = [float(total) for (_, name, total) in pay_rows]
                if sum(pay_sizes) > 0:
                    figp, axp = plt.subplots(figsize=PIE_FIGSIZE)
                    wedges_p, texts_p, autotexts_p = axp.pie(
                        pay_sizes,
                        labels=None,
                        autopct=lambda p: f"{p:.1f}%",
                        startangle=90,
                        counterclock=False,
                        radius=PIE_RADIUS
                    )
                    darken_axes(axp)  # ← 追加

                    for t in (texts_p or []):
                        t.set_color("white")
                    for t in (autotexts_p or []):
                        t.set_color("white")

                    axp.set_aspect('equal', adjustable='box')
                    axp.set_xlim(-1.1, 1.1)
                    axp.set_ylim(-1.1, 1.1)

                    legp = axp.legend(wedges_p, pay_labels, loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False)
                    for txt in legp.get_texts():
                        txt.set_color("white")

                    st.pyplot(figp, use_container_width=False)

                else:
                    st.caption("支払い手段別の金額がありません。")
            else:
                st.caption("支払い手段別のデータはありません。")
                
        with c2:
            pay_rows = get_monthly_payment_totals(month)
            if pay_rows:
                # 合計金額（参考）
                pay_total = sum(float(t) for (_, _, t) in pay_rows)
                st.write(f"合計：{pay_total:,.2f}")

                # 各支払方法の合計金額を列挙
                for _, name, total in pay_rows:
                    st.write(f"- {name}: {float(total):,.2f}")
            else:
                st.caption("支払い手段別のデータはありません。")