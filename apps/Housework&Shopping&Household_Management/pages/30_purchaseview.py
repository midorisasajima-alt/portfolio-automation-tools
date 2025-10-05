import streamlit as st
from db import list_genres, list_items_by_genre, get_item_timeseries_by_store
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator
from datetime import datetime
from collections import defaultdict

# Page config
st.set_page_config(page_title="Purchases — View", layout="wide")

# Dark page background (global)



# Load categories
genres = list_genres()
if not genres:
    st.error("No categories configured.")
    st.stop()

# Create tabs per category
tab_labels = [g[1] for g in genres]
tabs = st.tabs(tab_labels)

for tab, (genre_id, genre_name) in zip(tabs, genres):
    with tab:

        # Items under this category
        items = list_items_by_genre(genre_id)
        if not items:
            st.info("No items under this category.")
            continue

        labels = [f"{name} ({unit})" for (_id, name, unit) in items]
        # Unique key per tab to avoid widget collisions
        iidx = st.selectbox(
            "Item",
            options=list(range(len(items))),
            format_func=lambda i: labels[i],
            key=f"item_select_{genre_id}"
        )
        item_id, item_name, unit = items[iidx]

        st.markdown(f"#### {item_name}  (Unit: {unit})")

        # Fetch timeseries for the selected item
        rows = get_item_timeseries_by_store(item_id)
        if not rows:
            st.info("No records for this item.")
            continue

        qty_by_date = defaultdict(float)
        series_by_store = defaultdict(list)
        for d, store, qty, up in rows:
            dt = datetime.fromisoformat(d)
            qty_by_date[dt] += float(qty or 0.0)
            series_by_store[store].append((dt, float(up) if up is not None else 0.0))
        dates_sorted = sorted(qty_by_date.keys())
        qtys = [qty_by_date[d] for d in dates_sorted]

        # Dark matplotlib theme
        plt.rcParams.update({
            "figure.facecolor": "black",
            "axes.facecolor": "black",
            "axes.edgecolor": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "grid.color": "#555555",
            "text.color": "white",
            "axes.titlecolor": "white",
        })

        fig, ax1 = plt.subplots()

        # Quantity bars (back)
        bar = ax1.bar(dates_sorted, qtys, width=0.8, color="#3FA7D6", alpha=0.6, zorder=1)
        ax1.set_xlabel("Date")
        ax1.set_ylabel(f"Quantity ")
        ax1.grid(True, axis="y", linestyle="--", linewidth=0.5)

        # Unit price line (front)
        ax2 = ax1.twinx()
        ax2.patch.set_alpha(0.0)  # keep bars visible
        palette = ["#FFD166", "#EF476F", "#06D6A0", "#118AB2", "#C77DFF",
                "#F4A261", "#EE964B", "#8E7CC3", "#50C878", "#FF6F61"]
        store_lines, store_labels = [], []
        for idx, (store, points) in enumerate(sorted(series_by_store.items(), key=lambda x: x[0])):
            pts = sorted(points, key=lambda t: t[0])
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            line, = ax2.plot(xs, ys, linewidth=2.5, marker="o", markersize=4,
                            color=palette[idx % len(palette)], zorder=4)
            store_lines.append(line); store_labels.append(store)
        ax2.set_ylabel("Unit price")
        ax2.set_zorder(ax1.get_zorder() + 1)

        # Date formatting
        locator = AutoDateLocator()
        formatter = DateFormatter("%Y-%m-%d")
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)
        fig.autofmt_xdate()

        # Legend
        ax1.legend([bar] + store_lines, [f"Quantity"] + store_labels, loc="upper left")

        st.pyplot(fig, clear_figure=True)
