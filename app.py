from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.cleaning import clean_transactions
from src.customer_metrics import build_customer_metrics
from src.clv import add_clv_cac, add_clv_metrics, revenue_concentration
from src.segmentation import add_clv_segments, segment_summary

st.set_page_config(page_title="Customer Lifetime Value Analysis", page_icon="📈", layout="wide")

DATA_PATH = Path("data/transactions.csv")
CAC_PATH = Path("data/channel_cac.csv")


@st.cache_data
def load_analysis() -> tuple[pd.DataFrame, pd.DataFrame]:
    transactions = clean_transactions(DATA_PATH)
    customers = build_customer_metrics(transactions)
    customers = add_clv_metrics(customers)
    customers = add_clv_segments(customers)
    customers = add_clv_cac(customers, pd.read_csv(CAC_PATH))
    return transactions, customers


st.title("Customer Lifetime Value Analysis")
st.caption("Observed customer economics, revenue concentration, acquisition quality, and CLV:CAC")

if not DATA_PATH.exists() or not CAC_PATH.exists():
    st.warning("Data files are not present yet.")
    st.code("python generate_data.py\npython -m streamlit run app.py")
    st.stop()

transactions, customers = load_analysis()

# Sidebar controls
st.sidebar.header("Filters")
segments = ["All"] + sorted(customers["clv_segment"].unique().tolist())
channels = ["All"] + sorted(customers["acquisition_channel"].unique().tolist())
selected_segment = st.sidebar.selectbox("CLV Segment", segments)
selected_channel = st.sidebar.selectbox("Acquisition Channel", channels)

filtered = customers.copy()
if selected_segment != "All":
    filtered = filtered[filtered["clv_segment"] == selected_segment]
if selected_channel != "All":
    filtered = filtered[filtered["acquisition_channel"] == selected_channel]

# KPI cards
col1, col2, col3, col4, col5 = st.columns(5)
total_customers = len(filtered)
total_revenue = filtered["historical_clv"].sum()
avg_clv = filtered["historical_clv"].mean() if total_customers else 0
median_clv = filtered["historical_clv"].median() if total_customers else 0
top10_share = revenue_concentration(filtered) if total_customers else 0

col1.metric("Customers", f"{total_customers:,}")
col2.metric("Revenue", f"₹{total_revenue:,.0f}")
col3.metric("Average CLV", f"₹{avg_clv:,.0f}")
col4.metric("Median CLV", f"₹{median_clv:,.0f}")
col5.metric("Top 10% Revenue Share", f"{top10_share:.1%}")

st.divider()

# CLV distribution
st.subheader("1. Customer Value Distribution")
fig_dist = px.histogram(
    filtered,
    x="historical_clv",
    nbins=50,
    title="Historical CLV Distribution",
    labels={"historical_clv": "Historical CLV (₹)"},
)
fig_dist.update_layout(bargap=0.04)
st.plotly_chart(fig_dist, use_container_width=True)

# Segment analysis
st.subheader("2. CLV Segments")
seg_summary = segment_summary(filtered)
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    fig_seg = px.bar(seg_summary, x="clv_segment", y="customers", title="Customers by CLV Segment")
    st.plotly_chart(fig_seg, use_container_width=True)
with chart_col2:
    fig_rev = px.bar(
        seg_summary,
        x="clv_segment",
        y="total_revenue",
        title="Revenue by CLV Segment",
        labels={"total_revenue": "Revenue (₹)"},
    )
    st.plotly_chart(fig_rev, use_container_width=True)
st.dataframe(seg_summary.style.format({"total_revenue": "₹{:,.0f}", "avg_clv": "₹{:,.0f}", "median_clv": "₹{:,.0f}", "avg_aov": "₹{:,.0f}", "revenue_share": "{:.1%}"}), use_container_width=True, hide_index=True)

# Acquisition analysis
st.subheader("3. Acquisition Channel Quality")
channel_summary = (
    filtered.groupby("acquisition_channel", as_index=False)
    .agg(
        customers=("customer_id", "nunique"),
        avg_clv=("historical_clv", "mean"),
        median_clv=("historical_clv", "median"),
        avg_aov=("aov", "mean"),
        avg_frequency=("purchase_frequency", "mean"),
        cac=("cac", "first"),
        clv_cac=("clv_cac_ratio", "mean"),
    )
)
channel_col1, channel_col2 = st.columns(2)
with channel_col1:
    fig_channel = px.bar(
        channel_summary.sort_values("avg_clv", ascending=False),
        x="acquisition_channel",
        y="avg_clv",
        title="Average Historical CLV by Channel",
        labels={"avg_clv": "Average CLV (₹)", "acquisition_channel": "Channel"},
    )
    st.plotly_chart(fig_channel, use_container_width=True)
with channel_col2:
    fig_ratio = px.bar(
        channel_summary.sort_values("clv_cac", ascending=False),
        x="acquisition_channel",
        y="clv_cac",
        title="Observed CLV:CAC by Channel",
        labels={"clv_cac": "CLV:CAC Ratio", "acquisition_channel": "Channel"},
    )
    st.plotly_chart(fig_ratio, use_container_width=True)

st.dataframe(
    channel_summary.style.format(
        {
            "avg_clv": "₹{:,.0f}",
            "median_clv": "₹{:,.0f}",
            "avg_aov": "₹{:,.0f}",
            "cac": "₹{:,.0f}",
            "clv_cac": "{:.1f}x",
            "avg_frequency": "{:.2f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

# Customer explorer
st.subheader("4. Customer Explorer")
view_columns = [
    "customer_id",
    "acquisition_channel",
    "clv_segment",
    "historical_clv",
    "purchase_frequency",
    "aov",
    "lifespan_days",
    "revenue_per_active_month",
    "clv_cac_ratio",
]
explorer = filtered[view_columns].sort_values("historical_clv", ascending=False).head(100)
st.dataframe(
    explorer.style.format(
        {
            "historical_clv": "₹{:,.0f}",
            "aov": "₹{:,.0f}",
            "revenue_per_active_month": "₹{:,.0f}",
            "clv_cac_ratio": "{:.1f}x",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.subheader("5. Business Interpretation")
highest_channel = channel_summary.sort_values("avg_clv", ascending=False).iloc[0] if not channel_summary.empty else None
best_ratio_channel = channel_summary.sort_values("clv_cac", ascending=False).iloc[0] if not channel_summary.empty else None

if highest_channel is not None:
    st.info(
        f"Highest observed average CLV channel: **{highest_channel['acquisition_channel']}** "
        f"at approximately **₹{highest_channel['avg_clv']:,.0f}** per customer."
    )
if best_ratio_channel is not None:
    st.info(
        f"Strongest observed CLV:CAC channel: **{best_ratio_channel['acquisition_channel']}** "
        f"at approximately **{best_ratio_channel['clv_cac']:.1f}x**."
    )
st.caption("CLV:CAC uses synthetic channel-level CAC assumptions included in this portfolio project; it is not a live marketing-spend measurement.")
