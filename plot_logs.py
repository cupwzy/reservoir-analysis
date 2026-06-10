import pandas as pd
import matplotlib.pyplot as plt

# 读取数据


df = pd.read_excel(
    r"D:\测井结果可视化\FH-44井解释成果表.xlsx",
    sheet_name="Net Pay Summary Table",
    skiprows=[1]   # 跳过第2行
)



# 计算层中间深度（用于绘图）
df["MD_TOP"] = pd.to_numeric(df["MD_TOP"], errors="coerce")
df["MD_BOTTOM"] = pd.to_numeric(df["MD_BOTTOM"], errors="coerce")
df["DEPTH"] = (df["MD_TOP"] + df["MD_BOTTOM"]) / 2

print(df.head())
# =========================
# 1. 多轨道测井解释图
# =========================
fig, axes = plt.subplots(1, 3, figsize=(10, 8), sharey=True)

# 深度方向向下
for ax in axes:
    ax.invert_yaxis()

# ---- Track 1: VSH ----
axes[0].barh(df["DEPTH"], df["VSH"], height=df["MD_THK"], color='green')
axes[0].set_xlabel("VSH")
axes[0].set_title("VSH")
axes[0].set_xlim(0, 1)

# ---- Track 2: PHIE ----
axes[1].barh(df["DEPTH"], df["PHIE"], height=df["MD_THK"], color='blue')
axes[1].set_xlabel("PHIE")
axes[1].set_title("Porosity")
axes[1].set_xlim(0, 0.3)

# ---- Track 3: SWE ----
axes[2].barh(df["DEPTH"], df["SWE"], height=df["MD_THK"], color='red')
axes[2].set_xlabel("SWE")
axes[2].set_title("Water Sat")
axes[2].set_xlim(0, 1)

axes[0].set_ylabel("Depth (MD)")

plt.tight_layout()
plt.savefig("log_tracks.png", dpi=300)
plt.show()


# =========================
# 2. 交会图（PHIE vs SWE）
# =========================
plt.figure(figsize=(6, 6))

plt.scatter(df["PHIE"], df["SWE"],
            s=df["MD_THK"] * 10,   # 厚度控制点大小
            c='orange',
            edgecolors='k')

plt.xlabel("PHIE")
plt.ylabel("SWE")
plt.title("PHIE vs SWE Crossplot")

plt.grid()
plt.savefig("crossplot.png", dpi=300)
plt.show()


# =========================
# 3. 分层评价图
# =========================

def classify(row):
    if row["VSH"] < 0.3 and row["PHIE"] > 0.15 and row["SWE"] < 0.4:
        return "Good"
    elif row["SWE"] > 0.6:
        return "Water"
    else:
        return "Poor"

df["Class"] = df.apply(classify, axis=1)

color_map = {
    "Good": "green",
    "Poor": "orange",
    "Water": "red"
}

colors = df["Class"].map(color_map)

plt.figure(figsize=(5, 8))

plt.barh(df["DEPTH"], df["MD_THK"],
         color=colors)

plt.gca().invert_yaxis()
plt.xlabel("Thickness")
plt.ylabel("Depth")
plt.title("Reservoir Quality")

plt.savefig("classification.png", dpi=300)
plt.show()