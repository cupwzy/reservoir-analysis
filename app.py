import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import plotly.express as px
import re


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

# =========================
# 主逻辑
# =========================
if files:

    all_results = []

    # =========================
    # 逐井处理（这里只处理，不展示）
    # =========================
    for file in files:

        sheet = find_netpay_sheet(file)

        if sheet is None:
            st.error(f"{file.name} 未找到 Net Pay Summary Table")
            continue

        df = pd.read_excel(file, sheet_name=sheet, skiprows=[1])

        cols = ["MD_THK","TVDSS_THK","TVDSS_TOP","TVDSS_BOTTOM",
                "VSH","PHIE","SWE"]

        df = df[["ZONE"] + cols]

        # 转数值
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna()

        # 转比例
        df["VSH"] /= 100
        df["PHIE"] /= 100
        df["SWE"] /= 100

        # NetPay判断
        df["NetPay"] = (
            (df["VSH"] < vsh_cut) &
            (df["PHIE"] > phie_cut) &
            (df["SWE"] < swe_cut)
        )

        df_net = df[df["NetPay"]]

        # =========================
        # ZONE统计
        # =========================
        results = []

        for zone, g in df_net.groupby("ZONE"):

            thk = g["TVDSS_THK"].sum()

            if thk == 0:
                continue

            results.append({
                "Well": file.name,
                "ZONE": zone,
                "TVDSS_THK": thk,
                "VSH": round((g["VSH"] * thk).sum() / thk, 3),
                "PHIE": round((g["PHIE"] * thk).sum() / thk, 3),
                "SWE": round((g["SWE"] * thk).sum() / thk, 3)
            })

        df_res = pd.DataFrame(results)

        # 只存数据，不显示
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
        ["📂 数据", "🎯 ZONE分析", "📈 可视化", "📍 井位关系"]
    )

    # =========================
    # 页面1 数据（优化版）
    # =========================
    if page == "📂 数据":

        st.subheader("📊 数据总览")

        # =========================
        # KPI指标
        # =========================
        col1, col2, col3 = st.columns(3)

        col1.metric("井数量", final_df["Well"].nunique())
        col2.metric("层数", final_df["ZONE"].nunique())
        col3.metric("总净厚 (m)", round(final_df["TVDSS_THK"].sum(), 1))

        st.markdown("---")

        # =========================
        # 每井数据
        # =========================
        st.markdown("### 📂 各井 Net Pay 统计")

        for file, df_res in zip(files, all_results):
            st.markdown(f"#### 📂 {file.name}")
            st.dataframe(df_res, use_container_width=True)

        st.markdown("---")

        # =========================
        # 汇总数据
        # =========================
        st.markdown("### 📋 汇总数据表")

        st.dataframe(final_df, use_container_width=True)

        # =========================
        # 下载
        # =========================
        csv = final_df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            "📥 下载全部结果",
            csv,
            "all_well_results.csv",
            "text/csv"
        )

    # =========================
    # 页面2 ZONE分析
    # =========================
    elif page == "🎯 ZONE分析":

        st.subheader("🎯 ZONE 对比分析")

        # =========================
        # 选择ZONE
        # =========================
        all_zones = sorted(final_df["ZONE"].unique())

        zones_selected = st.multiselect(
            "选择ZONE",
            options=all_zones,
            default=all_zones[:3],
            key="zone_selector"
        )

        if not zones_selected:
            st.warning("请选择至少一个ZONE")
            st.stop()

        # =========================
        # 筛选数据
        # =========================
        df_filtered = final_df[
            final_df["ZONE"].isin(zones_selected)
        ]

        # =========================
        # 组合层计算
        # =========================
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

        # =========================
        # 合并数据
        # =========================
        df_final_compare = pd.concat(
            [df_filtered, df_combined],
            ignore_index=True
        )

        # =========================
        # 排序
        # =========================
        st.markdown("### 🔽 排序")

        col1, col2 = st.columns(2)

        with col1:
            sort_col = st.selectbox(
                "排序字段",
                ["TVDSS_THK", "PHIE", "SWE", "VSH"]
            )

        with col2:
            ascending = st.checkbox("升序", value=False)

        df_final_compare = df_final_compare.sort_values(
            by=sort_col,
            ascending=ascending
        )

        # =========================
        # 高亮
        # =========================
        def highlight_max(s):
            return ['background-color: #ffe599' if v == s.max() else '' for v in s]

        st.subheader("📋 对比结果")

        st.dataframe(
            df_final_compare.style.apply(highlight_max, subset=["TVDSS_THK"]),
            use_container_width=True
        )

        # =========================
        # 保存 session
        # =========================
        st.session_state["df_final_compare"] = df_final_compare
        st.session_state["zones_selected"] = zones_selected

        # =========================
        # 下载
        # =========================
        csv = df_final_compare.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            "📥 下载结果",
            csv,
            "zone_analysis.csv",
            "text/csv"
        )
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
    # =========================
    # 页面4 井位关系
    # =========================
    elif page == "📍 井位关系":
        
        st.subheader(" 井位图（支持上传文件）")
        
        st.markdown("""
        ### ⚠️ 坐标文件格式要求     
        """)

        example_xy_basic = pd.DataFrame({
            "Name": ["A1", "B1"],
            "X": [213445.49, 213500.00],
            "Y": [3456678.22, 3456600.00]
        })

        st.markdown("### 📋 示例1：基础井位（无厚度 → 普通散点图）")
        st.dataframe(example_xy_basic)

        example_xy_bubble = pd.DataFrame({
            "Name": ["A1", "B1"],
            "X": [213445.49, 213500.00],
            "Y": [3456678.22, 3456600.00],
            "TVDSS_THK": [12.5, 8.3],   # 气泡大小
        })
        st.info("""
        ✅ 如果提供 TVDSS_THK → 自动生成气泡图，没有 TVDSS_THK → 生成普通井位图  
        """)
        st.markdown("### 📋 示例2：气泡图（含厚度 → 自动生成气泡图）")
        st.dataframe(example_xy_bubble)

        # 示例数据
        example_map = pd.DataFrame({
            "Name": ["FH-1", "FH-2", "FH-3"],
            "Well symbol": ["Oil", "Gas", "Water"],
            "X": [213445.49, 213500.00, 213470.00],
            "Y": [3456678.22, 3456600.00, 3456650.00]
        })

        st.markdown("### 📋 示例3：井位分类图（Name + Well symbol）")
        st.dataframe(example_map)

        # 上传模块
        with st.expander("📂 上传井坐标文件", expanded=True):

            uploaded_file = st.file_uploader(
                "上传井坐标文件（CSV或Excel）",
                type=["csv", "xlsx"]
            )

            if uploaded_file:

                # 读取文件
                if uploaded_file.name.endswith(".csv"):
                    df_coord = pd.read_csv(uploaded_file)
                else:
                    df_coord = pd.read_excel(uploaded_file)

                st.dataframe(df_coord)
                
                # 列名统一
                df_coord.columns = df_coord.columns.str.strip().str.lower()
                columns = set(df_coord.columns)

                # 字段识别
                name_col = "name" if "name" in columns else None

                symbol_col = None
                for col in columns:
                    if "symbol" in col:
                        symbol_col = col
                        break

                # =========================
                # 分类井位图
                # =========================
                
                unique_symbols = df_coord[symbol_col].unique()

                color_map = {k: v for k, v in zip(unique_symbols, px.colors.qualitative.Set2)}

                fig = px.scatter(
                    df_coord,
                    x="x",
                    y="y",
                    text=name_col,
                    color=symbol_col,                 # ✅ 核心（启用图例交互）
                    color_discrete_map=color_map
                )

                # =========================
                # 样式
                # =========================
                fig.update_yaxes(scaleanchor="x", scaleratio=1)

                fig.update_traces(
                    textposition="top center",
                    textfont=dict(color="black", size=12),
                    marker=dict(
                        size=10,
                        opacity=0.85,
                        line=dict(width=1, color="black")
                    )
                )

                fig.update_layout(
                    height=650,
                    template="plotly_white",

                    legend=dict(
                        orientation="h",
                        x=0.5,
                        xanchor="center",
                        y=-0.30,
                        yanchor="top",
                        title="Well Symbol"
                    )
                )

                st.plotly_chart(fig, use_container_width=True)


            # =========================
            # ❌ 错误
            # =========================
            else:
                    st.error("❌ 请提供 X, Y 坐标字段")

else:
    st.info("请先上传Excel文件")
