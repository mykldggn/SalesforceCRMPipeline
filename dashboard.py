import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
st.set_page_config(page_title="CRM Sales Dashboard", layout="wide")

#CSS
st.markdown(
    """
    <style>
    .metric-container {
        background-color: #1e1e1e; /* dark card */
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,.3);
        text-align: center;
    }
    .metric-container p {
        color: #9ca3af; /* tailwind slate‑400 */
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    .metric-container h3 {
        margin: 0;
        font-size: 1.75rem;
        color: #e2e8f0; /* slate‑200 */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#load df
df = pd.read_parquet("data/pipeline.parquet")

#sidebar
with st.sidebar:
    st.header("🔍 Filters")

    stage_sel = st.multiselect(
        "Deal stage",
        options=df.deal_stage.unique().tolist(),
        default=df.deal_stage.unique().tolist(),
    )

    rep_sel = st.multiselect(
        "Sales rep",
        options=df.sales_agent.unique().tolist(),
        default=df.sales_agent.unique().tolist(),
    )

    date_min, date_max = st.date_input(
        "Close‑date range",
        value=(df.close_date.min(), df.close_date.max()),
    )

#convert output
date_min = pd.to_datetime(date_min)
date_max = pd.to_datetime(date_max)

#filter
mask = (
    df.deal_stage.isin(stage_sel)
    & df.sales_agent.isin(rep_sel)
    & df.close_date.between(date_min, date_max)
)
filtered = df.loc[mask]

#KPIs
pipe_total = int(filtered.close_value.sum())
won_rev = int(filtered.loc[filtered.is_won == 1, "close_value"].sum())
conv_rate = (filtered.is_won.sum() / len(filtered) * 100) if len(filtered) else 0
cycle_days = round(filtered.loc[filtered.is_won == 1, "deal_age"].mean() or 0)

#KPI HTML
kpi_cols = st.columns(4)
for col, label, value in zip(
    kpi_cols,
    ["Pipeline $", "Won Revenue", "Conversion %", "Avg Cycle (days)"],
    [f"${pipe_total:,}", f"${won_rev:,}", f"{conv_rate:.1f}%", cycle_days],
):
    col.markdown(
        f"<div class='metric-container'><p>{label}</p><h3>{value}</h3></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

#Visual
col1, col2 = st.columns([1, 1])

#Funnel
funnel_order = [
    "Prospecting",
    "Engaging",
    "Proposal",
    "Negotiation",
    "Won",
    "Lost",
]
funnel_df = (
    filtered.groupby("deal_stage")["close_value"].sum().reindex(funnel_order)
)
funnel_df = funnel_df[funnel_df.notna()].reset_index()

if not funnel_df.empty:
    fig_funnel = px.funnel(
        funnel_df,
        x="close_value",
        y="deal_stage",
        title="Pipeline Funnel",
        color_discrete_sequence=["#38bdf8"],
        height=400,
    )
    fig_funnel.update_layout(margin=dict(l=0, r=40, t=60, b=20))
    col1.plotly_chart(fig_funnel, use_container_width=True)
else:
    col1.info("No data for funnel with current filters.")

#Won-Rev Trend
trend = (
    filtered.loc[filtered.is_won == 1]
    .groupby(pd.Grouper(key="close_date", freq="M"))["close_value"]
    .sum()
    .reset_index()
)

if not trend.empty:
    fig_trend = px.line(
        trend,
        x="close_date",
        y="close_value",
        title="Won Revenue by Month",
        markers=True,
        height=400,
    )
    fig_trend.update_yaxes(tickprefix="$", separatethousands=True)
    fig_trend.update_layout(margin=dict(l=0, r=40, t=60, b=20))
    col2.plotly_chart(fig_trend, use_container_width=True)
else:
    col2.info("No won‑revenue in selected period.")

#Footer
st.markdown(
    "<p style='text-align:center;font-size:0.8rem;color:#6b7280;'>"
    "Built with ❤️ using Streamlit & Plotly • Data source: Kaggle CRM Sales Predictive Analytics"
    "</p>",
    unsafe_allow_html=True,
)
