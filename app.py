import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import plotly.express as px

# 中文显示
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

st.set_page_config(layout="wide")
st.title("🛢️ Advanced Reservoir Analysis Tool")

# =========================
# 自动识别sheet
# =========================
def find_netpay_sheet(file):

    xls = pd.ExcelFile(file)

    for sheet in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet, nrows=10)
        if "ZONE" in df.columns and "TVDSS_THK" in df.columns:
            return sheet

    return None

# =========================
# Cutoff
# =========================
st.sidebar.header("⚙️ Cutoff Settings")

vsh_cut = st.sidebar.slider("VSH max", 0.0, 1.0, 0.2)
phie_cut = st.sidebar.slider("PHIE min", 0.0, 0.3, 0.08)
swe_cut = st.sidebar.slider("SWE max", 0.0, 1.0, 0.5)

# =========================
# 上传文件
# =========================
files = st.file_uploader(
    "上传多个井数据",
    type=["xlsx"],
    accept_multiple_files=True
)

if files:

    all_results = []

    # =========================
    # 逐井处理
    # =========================
    for file in files:

        st.subheader(f"📂 {file.name}")

        sheet = find_netpay_sheet(file)

        if sheet is None:
            st.error("未找到 Net Pay Summary Table")
            continue

        df = pd.read_excel(file, sheet_name=sheet, skiprows=[1])

        cols = ["MD_THK","TVDSS_THK","TVDSS_TOP","TVDSS_BOTTOM",
                "VSH","PHIE","SWE"]

        df = df[["ZONE"] + cols]

        for col in cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna()

        df["VSH"] /= 100
        df["PHIE"] /= 100
        df["SWE"] /= 100

        # NetPay
        df["NetPay"] = (
            (df["VSH"] < vsh_cut) &
            (df["PHIE"] > phie_cut) &
            (df["SWE"] < swe_cut)
        )

        df_net = df[df["NetPay"]]

        results = []

        for zone, g in df_net.groupby("ZONE"):

            thk = g["TVDSS_THK"].sum()
            if thk == 0:
                continue

            results.append({
                "Well": file.name,
                "ZONE": zone,
                "TVDSS_THK": thk,
                "VSH": round((g["VSH"]*thk).sum()/thk,3),
                "PHIE": round((g["PHIE"]*thk).sum()/thk,3),
                "SWE": round((g["SWE"]*thk).sum()/thk,3)
            })

        df_res = pd.DataFrame(results)
        st.dataframe(df_res)

        all_results.append(df_res)

    # =========================
    # 合并多井
    # =========================
    final_df = pd.concat(all_results, ignore_index=True)

    # =========================
    # 左侧导航
    # =========================
    st.sidebar.title("📌 导航栏")

    page = st.sidebar.radio(
        "导航",
        ["📂 数据", "🎯 ZONE分析", "📈 可视化"]
    )

    # =========================
    # 页面1 数据
    # =========================
    if page == "📂 数据":
        st.dataframe(final_df)

    # =========================
    # 页面2 ZONE分析
    # =========================
    elif page == "🎯 ZONE分析":

        all_zones = sorted(final_df["ZONE"].unique())

        zones_selected = st.multiselect(
            "选择ZONE",
            options=all_zones,
            default=all_zones[:3],
            key="zone_selector"
        )

        if zones_selected:

            df_filtered = final_df[final_df["ZONE"].isin(zones_selected)]

            combined_results = []

            if len(zones_selected) >= 2:

                for well, g in df_filtered.groupby("Well"):

                    thk = g["TVDSS_THK"].sum()

                    if thk > 0:
                        combined_results.append({
                            "Well": well,
                            "ZONE": "+".join(zones_selected),
                            "TVDSS_THK": thk,
                            "VSH": (g["VSH"] * g["TVDSS_THK"]).sum() / thk,
                            "PHIE": (g["PHIE"] * g["TVDSS_THK"]).sum() / thk,
                            "SWE": (g["SWE"] * g["TVDSS_THK"]).sum() / thk
                        })

            df_combined = pd.DataFrame(combined_results)

            df_final_compare = pd.concat(
                [df_filtered, df_combined],
                ignore_index=True
            )

            # ✅ 存入 session
            st.session_state["df_final_compare"] = df_final_compare
            st.session_state["zones_selected"] = zones_selected

            st.subheader("📋 对比结果")
            st.dataframe(df_final_compare)

    # =========================
    # 页面3 可视化
    # =========================
    elif page == "📈 可视化":

        if "df_final_compare" not in st.session_state:
            st.info("请先在 ZONE分析 中选择ZONE")
        
        else:
            df_final_compare = st.session_state["df_final_compare"]
            zones_selected = st.session_state["zones_selected"]

            metric = st.selectbox(
                "选择参数",
                ["TVDSS_THK","PHIE","SWE","VSH"],
                key="metric_select"
            )

            # 排序处理
            order = zones_selected.copy()
            if len(zones_selected) >= 2:
                order.append("+".join(zones_selected))

            
            df_final_compare["ZONE"] = pd.Categorical(
                df_final_compare["ZONE"],
                categories=order,
                ordered=True
            )

            # Plotly图
            fig = px.bar(
                df_final_compare,
                x="ZONE",
                y=metric,
                color="Well",
                barmode="group",
                text=metric,
            )
            
            # 数值显示优化
           
            fig.update_traces(
                texttemplate='%{text:.2f}',
                textposition='outside'
            )

            fig.update_layout(
                title=f"{metric} Comparison",
                xaxis_title="ZONE",
                yaxis_title=metric,
                legend_title="Well",
                height=500,
                template="plotly_white"
            )

        st.plotly_chart(fig, use_container_width=True)



else:
    st.info("请先上传Excel文件")
