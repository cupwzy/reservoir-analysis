import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# =========================
# 1. 读取数据
# =========================
df = pd.read_excel(
    r"D:\测井结果可视化\FH-44井解释成果表.xlsx",
    sheet_name="Net Pay Summary Table",
    skiprows=[1]
)

# =========================
# 2. 数据处理
# =========================
cols = ["MD_TOP", "MD_BOTTOM", "MD_THK",
        "TVDSS_TOP", "TVDSS_BOTTOM",
        "VSH", "PHIE", "SWE"]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 单位转换
df["PHIE"] = df["PHIE"] / 100
df["SWE"] = df["SWE"] / 100
df["VSH"] = df["VSH"] / 100

# 深度
df["DEPTH"] = (df["TVDSS_TOP"] + df["TVDSS_BOTTOM"]) / 2

# 排序
df = df.sort_values("DEPTH")

# =========================
# 3. 分类（岩性/储层）
# =========================
def classify(row):
    if row["VSH"] < 0.3 and row["PHIE"] > 0.15 and row["SWE"] < 0.4:
        return "Good"
    elif row["SWE"] > 0.6:
        return "Water"
    else:
        return "Poor"

df["Class"] = df.apply(classify, axis=1)

# =========================
# 4. Matplotlib 专业图（含岩性条带）
# =========================

fig, axes = plt.subplots(1, 4, figsize=(14, 10), sharey=True)

# 深度方向
for ax in axes:
    ax.invert_yaxis()
    ax.grid(True)

# ---- Track 0: 岩性条带 ----
color_map = {
    "Good": "yellow",
    "Poor": "orange",
    "Water": "red"
}

for i, row in df.iterrows():
    axes[0].barh(
        row["DEPTH"],
        1,
        height=row["MD_THK"],
        color=color_map[row["Class"]]
    )

axes[0].set_title("Lithology")
axes[0].set_xlim(0, 1)
axes[0].set_xticks([])

# ---- Track 1: VSH ----
axes[1].plot(df["VSH"], df["DEPTH"], color='green')
axes[1].fill_betweenx(df["DEPTH"], 0, df["VSH"], color='green', alpha=0.3)
axes[1].set_xlim(0, 1)
axes[1].set_title("VSH")

# ---- Track 2: PHIE ----
axes[2].plot(df["PHIE"], df["DEPTH"], color='blue')
axes[2].fill_betweenx(df["DEPTH"], 0, df["PHIE"], color='blue', alpha=0.3)
axes[2].set_xlim(0, 0.3)
axes[2].set_title("PHIE")

# ---- Track 3: SWE ----
axes[3].plot(df["SWE"], df["DEPTH"], color='red')
axes[3].fill_betweenx(df["DEPTH"], 0, df["SWE"], color='red', alpha=0.3)
axes[3].set_xlim(0, 1)
axes[3].set_title("SWE")

axes[0].set_ylabel("Depth (TVDSS)")

# =========================
# ✅ 自动标注层名（ZONE）
# =========================
for i, row in df.iterrows():
    axes[0].text(
        0.5,
        row["DEPTH"],
        row["ZONE"],
        ha="center",
        va="center",
        fontsize=8
    )

plt.tight_layout()
plt.savefig("professional_lithology.png", dpi=300)
plt.show()

# =========================
# 5. Plotly交互版本（重点）
# =========================

fig = px.scatter(
    df,
    x="PHIE",
    y="DEPTH",
    color="Class",
    size="MD_THK",
    hover_data=["ZONE", "VSH", "SWE"],
    title="Interactive Reservoir Analysis"
)

fig.update_layout(
    yaxis=dict(autorange="reversed"),  # 深度向下
    height=800
)

fig.write_html("interactive_plot.html")
fig.show()
