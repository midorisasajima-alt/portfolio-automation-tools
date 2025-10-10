import streamlit as st
import matplotlib.pyplot as plt
from db import (
    get_available_months, get_month_total, get_monthly_genre_totals,
    get_month_genre_item_totals, get_monthly_payment_totals
)

st.set_page_config(page_title="Household Ledger", layout="wide")

months = get_available_months()
if not months:
    st.info("No data available. Please record first in 'Shopping_Record'.")
    st.stop()

def darken_axes(ax):
    # Black background, white axes, ticks, and labels
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
            st.info("No expenditure breakdown for this month.")
            continue

        # ── Top row: Side-by-side pie charts ─────────────────────────────
        # ── Common parameters ────────────────────────────────────────────
        PIE_FIGSIZE = (5, 5)
        PIE_RADIUS  = 1.0

        # ── Top row: 3 columns ───────────────────────────────────────────
        col_left, col_mid, col_right = st.columns([10,10,6])

        # Left: Breakdown by genre (pie chart)
        with col_left:
            st.text("Breakdown by Genre")
            labels = [gname for (_, gname, total) in genre_rows]
            sizes = [float(total) for (_, gname, total) in genre_rows]
            if sum(sizes) <= 0:
                st.info("No valid amounts to display in pie chart.")
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
                darken_axes(ax)

                # Make percentage labels white
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
                st.pyplot(fig, use_column_width_width=False)


        # Middle: Tabs by genre with bar charts
        with col_mid:
            g_tabs = st.tabs([gname for (_, gname, _) in genre_rows])

            for g_tab, (gid, gname, gtotal) in zip(g_tabs, genre_rows):
                with g_tab:
                    items = get_month_genre_item_totals(month, gid)
                    if not items:
                        st.write("No records")
                        continue

                    items_sorted = sorted(items, key=lambda x: float(x[1]), reverse=True)
                    names = [name for name, total in items_sorted]
                    totals = [float(total) for name, total in items_sorted]

                    fig2, ax2 = plt.subplots()
                    y_pos = list(range(len(names)))
                    bars = ax2.barh(y_pos, totals)

                    darken_axes(ax2)

                    ax2.set_yticks(y_pos, labels=names)
                    ax2.set_xlabel("Amount")
                    ax2.set_ylabel("Item")
                    ax2.invert_yaxis()

                    for bar, val in zip(bars, totals):
                        x = bar.get_width()
                        y = bar.get_y() + bar.get_height() / 2
                        ax2.text(x / 2, y, f"{val:,.2f}", va="center", ha="center", color="white")

                    fig2.subplots_adjust(left=0.35)
                    fig2.tight_layout()
                    st.pyplot(fig2)


        # Right: Total by genre (text)
        with col_right:
            genre_sum_total = sum(float(t) for (_, _, t) in genre_rows)
            st.write(f"Total: {genre_sum_total:,.2f}")
            for _, gname, total in sorted(genre_rows, key=lambda x: float(x[2]), reverse=True):
                st.write(f"- {gname}: {float(total):,.2f}")

        
        st.markdown("---")
        st.text("Breakdown by Payment Method")
        c1, _, c2 = st.columns([10,2,10])

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
                    darken_axes(axp)

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

                    st.pyplot(figp, use_column_width_width=False)

                else:
                    st.caption("No payment method amounts available.")
            else:
                st.caption("No data by payment method available.")
                
        with c2:
            pay_rows = get_monthly_payment_totals(month)
            if pay_rows:
                pay_total = sum(float(t) for (_, _, t) in pay_rows)
                st.write(f"Total: {pay_total:,.2f}")

                for _, name, total in pay_rows:
                    st.write(f"- {name}: {float(total):,.2f}")
            else:
                st.caption("No data by payment method available.")
