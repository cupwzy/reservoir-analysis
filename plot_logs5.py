import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =========================
# 1. 读取 Net Pay Summary Table
# =========================
file_path = r"D:\测井结果可视化\FH-44井解释成果表.xlsx"

# 读取第2个sheet
df = pd.read_excel(file_path, sheet_name=1, skiprows=[1])

# =========================
# 2. 数据处理
# =========================
cols = ["MD_TOP", "MD_BOTTOM", "MD_THK",
        "TVDSS_TOP", "TVDSS_BOTTOM", "TVDSS_THK",
        "VSH", "PHIE", "SWE"]

df = df[["ZONE"] + cols]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=cols)

# 转换为比例
df["VSH"] /= 100
df["PHIE"] /= 100
df["SWE"] /= 100

# 深度
df["DEPTH"] = (df["TVDSS_TOP"] + df["TVDSS_BOTTOM"]) / 2

# =========================
# 3. 按ZONE分组计算
# =========================
results = []

groups = df.groupby("ZONE")

for zone, g in groups:

    md_sum = g["MD_THK"].sum()
    tvd_sum = g["TVDSS_THK"].sum()

    # 加权平均
    weight = g["TVDSS_THK"]

    vsh_avg = (g["VSH"] * weight).sum() / weight.sum()
    phie_avg = (g["PHIE"] * weight).sum() / weight.sum()
    swe_avg = (g["SWE"] * weight).sum() / weight.sum()

    results.append({
        "ZONE": zone,
        "MD_THK_SUM": md_sum,
        "TVDSS_THK_SUM": tvd_sum,
        "VSH": vsh_avg,
        "PHIE": phie_avg,
        "SWE": swe_avg
    })

df_res = pd.DataFrame(results)

# =========================
# 4. 输出到终端
# =========================
print("\n====== ZONE SUMMARY ======")
print(df_res.to_string(index=False))

# =========================
# 5. 生成颜色
# =========================
zones = df_res["ZONE"].unique()

colors = plt.cm.tab20(np.linspace(0, 1, len(zones)))
color_map = dict(zip(zones, colors))

# =========================
# 6. 绘图
# =========================
fig, ax = plt.subplots(figsize=(6, 10))

# 深度方向
min_d, max_d = df["DEPTH"].min(), df["DEPTH"].max()
ax.set_ylim(max_d, min_d)

# 绘制不同ZONE
for zone, g in df.groupby("ZONE"):
    ax.barh(
        g["DEPTH"],
        1,
        height=g["TVDSS_THK"],
        color=color_map[zone],
        edgecolor='none'
    )

# =========================
# 7. 图例（含加权值）
# =========================
legend_elements = []

for _, row in df_res.iterrows():

    label = (
        f"{row['ZONE']}\n"
        f"VSH={row['VSH']:.2f}  "
        f"PHIE={row['PHIE']:.2f}  "
        f"SWE={row['SWE']:.2f}"
    )

    legend_elements.append(
        plt.Line2D([0], [0],
                   color=color_map[row["ZONE"]],
                   lw=6,
                   label=label)
    )

ax.legend(
    handles=legend_elements,
    loc='upper right',
    fontsize=8,
    frameon=True
)

ax.set_title("ZONE Reservoir Distribution")
ax.set_xticks([])
ax.set_ylabel("TVDSS Depth (m)")

plt.tight_layout()
plt.savefig("zone_reservoir_plot.png", dpi=300)
plt.show()