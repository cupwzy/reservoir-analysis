import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =========================
# 1. 读取数据
# =========================
df = pd.read_excel(
    r"D:\测井结果可视化\FH-44井解释成果表.xlsx",
    sheet_name="Net Pay Summary Table",
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

# 单位转换
df["PHIE"] = df["PHIE"] / 100
df["SWE"] = df["SWE"] / 100
df["VSH"] = df["VSH"] / 100

# 深度用 TVDSS
df["DEPTH"] = (df["TVDSS_TOP"] + df["TVDSS_BOTTOM"]) / 2

# 排序
df = df.sort_values("DEPTH")

# =========================
# 3. 储层分类
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
# 4. 绘制专业测井曲线
# =========================
fig, axes = plt.subplots(1, 3, figsize=(12, 10), sharey=True)

# 深度向下
for ax in axes:
    ax.invert_yaxis()
    ax.grid(True)

# -------------------------
# Track 1: VSH
# -------------------------
axes[0].plot(df["VSH"], df["DEPTH"], color='green', linewidth=1.5)
axes[0].fill_betweenx(df["DEPTH"], 0, df["VSH"], color='green', alpha=0.3)
axes[0].set_xlim(0, 1)
axes[0].set_xlabel("VSH")
axes[0].set_title("Shale Volume")

# -------------------------
# Track 2: PHIE
# -------------------------
axes[1].plot(df["PHIE"], df["DEPTH"], color='blue', linewidth=1.5)
axes[1].fill_betweenx(df["DEPTH"], 0, df["PHIE"], color='blue', alpha=0.3)
axes[1].set_xlim(0, 0.3)
axes[1].set_xlabel("PHIE")
axes[1].set_title("Porosity")

# -------------------------
# Track 3: SWE
# -------------------------
axes[2].plot(df["SWE"], df["DEPTH"], color='red', linewidth=1.5)
axes[2].fill_betweenx(df["DEPTH"], 0, df["SWE"], color='red', alpha=0.3)
axes[2].set_xlim(0, 1)
axes[2].set_xlabel("SWE")
axes[2].set_title("Water Saturation")

# 深度轴
axes[0].set_ylabel("Depth (TVDSS)")

# =========================
# 5. 标注优质储层
# =========================
for i, row in df.iterrows():
    if row["Class"] == "Good":
        axes[1].scatter(row["PHIE"], row["DEPTH"], color="yellow", edgecolors="black", zorder=3)

# =========================
# 输出
# =========================
plt.tight_layout()
plt.savefig("professional_log.png", dpi=300)
plt.show()