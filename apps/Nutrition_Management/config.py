NUTRIENTS = ["Energy", "Protein", "Fat", "Carbohydrate"]

# 1日の目標値
DAILY_GOALS = {
    "Energy": 2300.0,
    "Protein": 86.0,
    "Fat": 64.0,
    "Carbohydrate": 345.0,
}

# 表示色（必要なら任意で変更）
COLORS = {
    "Energy": "#F39C12",        # Orange
    "Protein": "#2E86C1",       # Blue
    "Fat": "#28B463",           # Green
    "Carbohydrate": "#9B59B6",  # Purple
}

# 薄い色（未達部分用）
LIGHT_COLORS = {
    k: c + "55" for k, c in COLORS.items()  # 33% 透明度
}
