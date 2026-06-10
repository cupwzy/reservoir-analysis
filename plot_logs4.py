import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import matplotlib.patches as mpatches

# =========================
# 1. 读取数据
# =========================
df = pd.read_excel(
    r"D:\测井结果可视化\FH-44井解释成果表.xlsx",
    skiprows=[1]
)

# =========================
# 2. 数据预处理
# =========================
cols = ["MD_TOP", "MD_BOTTOM", "MD_THK",
        "TVDSS_TOP", "TVDSS_BOTTOM",
        "VSH", "PHIE", "SWE"]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 删除空值
df = df.dropna(subset=cols)

# 百分比转换
df["PHIE"] /= 100
df["SWE"] /= 100
df["VSH"] /= 100

# 深度
df["DEPTH"] = (df["TVDSS_TOP"] + df["TVDSS_BOTTOM"]) / 2

# 深度排序 
df = df.sort_values("DEPTH", ascending=True)

# =========================
# 3. 地层识别
# =========================
def map_formation(zone):
    zone = str(zone).upper()

    if "MISHRIF" in zone or zone == "MB":
        return "Mishrif"
    elif any(x in zone for x in ["AMADI", "MAUDUD", "SHUAIBA"]):
        return "Amadi"
    elif "ZUBAIR" in zone:
        return "Zubair"
    elif any(x in zone for x in ["RATAWI", "YAMAMA", "MC", "MD", "ME"]):
        return "Ratawi"
    else:
        return "Unknown"

df["Formation"] = df["ZONE"].apply(map_formation)

# =========================
# 4. Cutoff
# =========================
cutoffs = {
    "Mishrif": {"VSH": 0.2, "PHIE": 0.065, "SWE": 0.55},
    "Amadi": {"VSH": 0.2, "PHIE": 0.08, "SWE": 0.55},
    "Zubair": {"VSH": 0.5, "PHIE": 0.08, "SWE": 0.5},
    "Ratawi": {"VSH": 0.2, "PHIE": 0.05, "SWE": 0.5}
}

def classify(row):
    if row["Formation"] not in cutoffs:
        return "Unknown"

    c = cutoffs[row["Formation"]]

    if row["VSH"] < c["VSH"] and row["PHIE"] > c["PHIE"] and row["SWE"] < c["SWE"]:
        return "Net Pay"
    elif row["SWE"] > c["SWE"]:
        return "Water"
    else:
        return "Non-Reservoir"

df["Class"] = df.apply(classify, axis=1)

# =========================
# 5. Net Pay
# =========================
net_pay_df = df[df["Class"] == "Net Pay"]
net_pay_thickness = net_pay_df["MD_THK"].sum()

print(f"\n Total Net Pay: {net_pay_thickness:.2f} m")

# =========================
# 绘图
# =========================
fig, axes = plt.subplots(1, 4, figsize=(14, 10), sharey=True)

for ax in axes:
    ax.grid(True)

min_depth = df["DEPTH"].min()
max_depth = df["DEPTH"].max()

for ax in axes:
    ax.set_ylim(max_depth, min_depth)

# 颜色
color_map = {
    "Net Pay": "yellow",
    "Non-Reservoir": "orange",
    "Water": "red",
    "Unknown": "gray"
}

# ---- Lithology ----
for _, row in df.iterrows():
    axes[0].barh(
        row["DEPTH"],
        1,
        height=row["MD_THK"],
        color=color_map[row["Class"]]
    )

axes[0].set_title("Lithology")


# =========================
# ZONE 标注（按层居中）
# =========================

zone_groups = df.groupby("ZONE")

for zone, group in zone_groups:
    # 层顶 & 层底
    top = group["DEPTH"].min()
    bottom = group["DEPTH"].max()

    # 中点
    mid_depth = (top + bottom) / 2

    axes[0].text(
        0.5,                      # 横向中间
        mid_depth,                # 垂向中点
        str(zone),
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        bbox=dict(
            facecolor='white',
            alpha=0.6,
            edgecolor='none'
        )
    )

# 曲线
axes[1].plot(df["VSH"], df["DEPTH"], color="green")
axes[1].fill_betweenx(df["DEPTH"], 0, df["VSH"], color="green", alpha=0.3)
axes[1].set_title("VSH")

axes[2].plot(df["PHIE"], df["DEPTH"], color="blue")
axes[2].fill_betweenx(df["DEPTH"], 0, df["PHIE"], color="blue", alpha=0.3)
axes[2].set_title("PHIE")

axes[3].plot(df["SWE"], df["DEPTH"], color="red")
axes[3].fill_betweenx(df["DEPTH"], 0, df["SWE"], color="red", alpha=0.3)
axes[3].set_title("SWE")

axes[0].set_ylabel("Depth")

# 图例
legend_elements = [
    mpatches.Patch(color='yellow', label='Net Pay'),
    mpatches.Patch(color='orange', label='Non-Reservoir'),
    mpatches.Patch(color='red', label='Water'),
    mpatches.Patch(color='gray', label='Unknown')
]

axes[0].legend(handles=legend_elements, fontsize=8)

plt.tight_layout()
plt.savefig("full_interpretation.png", dpi=300)
plt.show()

# =========================
# Plotly
# =========================
fig2 = px.scatter(
    df,
    x="PHIE",
    y="DEPTH",
    color="Class",
    size="MD_THK",
    size_max=40
)

fig2.update_layout(yaxis=dict(autorange="reversed"))
fig2.show()