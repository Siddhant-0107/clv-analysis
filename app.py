from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.cleaning import clean_transactions
from src.customer_metrics import build_customer_metrics
from src.clv import add_clv_cac, add_clv_metrics, channel_clv_cac, revenue_concentration
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

col1, col2, col3, col4, col5 = st.columns(5)
total_customers = len(filtered)
total_revenue = filtered["historical_clv"].sum()
avg_clv = filtered["historical_clv"].mean() if total_customers else 0
median_clv = filtered["historical_clv"].median() if total_customers else 0
top10_share = revenue_concentration(filtered) if total_customers else 0

col1.metric("Customers", f"{total_customers:,}")
col2.metric("Observed Revenue", f"₹{total_revenue:,.0f}")
col3.metric("Average Historical CLV", f"₹{avg_clv:,.0f}")
col4.metric("Median Historical CLV", f"₹{median_clv:,.0f}")
col5.metric("Top 10% Revenue Share", f"{top10_share:.1%}")

st.divider()

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
st.caption("The long right tail indicates that customer value is highly skewed: a relatively small group of customers contributes substantially more observed revenue than the typical customer.")

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
st.dataframe(
    seg_summary.style.format(
        {
            "total_revenue": "₹{:,.0f}",
            "avg_clv": "₹{:,.0f}",
            "median_clv": "₹{:,.0f}",
            "avg_aov": "₹{:,.0f}",
            "revenue_share": "{:.1%}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.subheader("3. Acquisition Channel Quality")
channel_summary = channel_clv_cac(filtered)
channel_col1, channel_col2 = st.columns(2)
with channel_col1:
    fig_channel = px.bar(
        channel_summary.sort_values("avg_clv", ascending=False),
        x="acquisition_channel",
        y="avg_clv",
        title="Average Historical CLV by Channel",
        labels={"avg_clv": "Average Historical CLV (₹)", "acquisition_channel": "Channel"},
    )
    st.plotly_chart(fig_channel, use_container_width=True)
with channel_col2:
    fig_ratio = px.bar(
        channel_summary.sort_values("clv_cac", ascending=False),
        x="acquisition_channel",
        y="clv_cac",
        title="Observed CLV:CAC Proxy by Acquisition Channel",
        labels={"clv_cac": "Average CLV / CAC", "acquisition_channel": "Channel"},
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
st.info("**Methodology:** Observed CLV:CAC = channel average historical CLV ÷ synthetic channel CAC. This is a retrospective unit-economics proxy, not a predictive CLV model or live marketing ROI measurement.")

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
    "customer_clv_cac_proxy",
]
explorer = filtered[view_columns].sort_values("historical_clv", ascending=False).head(100)
st.dataframe(
    explorer.style.format(
        {
            "historical_clv": "₹{:,.0f}",
            "aov": "₹{:,.0f}",
            "revenue_per_active_month": "₹{:,.0f}",
            "customer_clv_cac_proxy": "{:.1f}x",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.subheader("5. Business Interpretation")
highest_channel = channel_summary.sort_values("avg_clv", ascending=False).iloc[0] if not channel_summary.empty else None
best_ratio_channel = channel_summary.sort_values("clv_cac", ascending=False).iloc[0] if not channel_summary.empty else None
weakest_ratio_channel = channel_summary.sort_values("clv_cac", ascending=True).iloc[0] if not channel_summary.empty else None

high_value_revenue = filtered.loc[filtered["clv_segment"] == "High Value", "historical_clv"].sum()
high_value_share = high_value_revenue / total_revenue if total_revenue > 0 else 0

if highest_channel is not None:
    st.info(
        f"**Acquisition quality:** {highest_channel['acquisition_channel']} has the highest observed average CLV at approximately **₹{highest_channel['avg_clv']:,.0f}** per customer."
    )
if best_ratio_channel is not None:
    st.info(
        f"**Unit economics:** {best_ratio_channel['acquisition_channel']} has the strongest observed CLV:CAC at approximately **{best_ratio_channel['clv_cac']:.1f}x**, based on synthetic CAC assumptions."
    )
if weakest_ratio_channel is not None:
    st.warning(
        f"**Optimization opportunity:** {weakest_ratio_channel['acquisition_channel']} has the weakest observed CLV:CAC at approximately **{weakest_ratio_channel['clv_cac']:.1f}x**. Before scaling this channel, validate conversion quality and acquisition economics with real spend data."
    )
st.success(
    f"**Retention priority:** High Value customers account for approximately **{high_value_share:.1%}** of observed revenue in the current view. Retention and loyalty efforts should prioritize protecting this revenue base."
)
st.caption("Interpretation is based on observed transaction history. Historical CLV measures realized revenue during the observation window; it does not predict future customer purchases.")
