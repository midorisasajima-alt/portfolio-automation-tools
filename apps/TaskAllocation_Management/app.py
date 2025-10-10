
import streamlit as st
from graphviz import Digraph
from data_store import count_active, SIX_MINISTRIES

st.set_page_config(page_title="Task allocation", layout="wide")
st.subheader("約束不明、申令不熟、将之罪也。既已明而不如法者、吏士之罪也。")

st.text("")
st.text("If an order is unclear and instructions are not thoroughly conveyed, it is the fault of the general.")
st.text("If the order has already been made clear yet the law is not obeyed, it is the fault of the soldiers.")

st.markdown("---")

def color_by_count(n: int) -> str:
    if n >= 20: return "#ff3b30"
    if n >= 10: return "#ff9500"
    if n >= 5:  return "#ffd60a"
    if n >= 1:  return "#34c759"
    return "#111111"

cnt_king = count_active("王")
cnt_min = {m: count_active(m) for m in SIX_MINISTRIES}
cnt_hyakushi = count_active("百司")
cnt_yushidai = count_active("御史台")

g = Digraph(
    "TaskMap",
    node_attr={
        "style":"filled,rounded",
        "fontname":"MS Gothic",
        "shape":"box",
        "color":"#2c2c2e",
        "penwidth":"1.2"
    },
    graph_attr={
        "bgcolor":"#000000",
        "rankdir":"TB",
        "splines":"spline",
        "nodesep":"0.5",
        "ranksep":"0.6"
    },
    edge_attr={
        "color":"#aaaaaa",
        "penwidth":"1.4",
        "arrowsize":"0.8"
    }
)

def add_node(name: str, count: int):
    col = color_by_count(count)
    label = f"""<
<B>{name}</B>
<BR/><FONT POINT-SIZE='10'>({count})</FONT>
>"""
    g.node(name, label=label, fillcolor=col, fontcolor="#ffffff")

with g.subgraph(name="cluster_rank0") as s0:
    s0.attr(rank="same")
    add_node("王", cnt_king)

with g.subgraph(name="cluster_rank1") as s1:
    s1.attr(rank="same")
    for m in SIX_MINISTRIES:
        add_node(m, cnt_min[m])

with g.subgraph(name="cluster_rank2") as s2:
    s2.attr(rank="same")
    add_node("百司", cnt_hyakushi)
    add_node("御史台", cnt_yushidai)

for m in SIX_MINISTRIES:
    g.edge("王", m)
    g.edge(m, "百司")
g.edge("百司", "御史台")
g.edge("御史台", "王")

st.graphviz_chart(g, use_container_width_width=True)
