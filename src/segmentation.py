from __future__ import annotations

import pandas as pd


def add_clv_segments(customer_metrics: pd.DataFrame) -> pd.DataFrame:
    """Segment customers into Low/Medium/High observed CLV using percentile ranks.

    The rank-based implementation avoids qcut failures when many customers share
    identical CLV values, while preserving the intended 20/60/20 split as closely
    as the data permits.
    """
    df = customer_metrics.copy()
    if df.empty:
        df["clv_segment"] = pd.Series(dtype="object")
        return df

    percentile_rank = df["historical_clv"].rank(method="first", pct=True)
    df["clv_segment"] = "Medium"
    df.loc[percentile_rank <= 0.20, "clv_segment"] = "Low Value"
    df.loc[percentile_rank > 0.80, "clv_segment"] = "High Value"
    return df


def segment_summary(customer_metrics: pd.DataFrame) -> pd.DataFrame:
    """Summarize customer count, revenue, and value metrics by CLV segment."""
    summary = (
        customer_metrics.groupby("clv_segment", as_index=False)
        .agg(
            customers=("customer_id", "nunique"),
            total_revenue=("historical_clv", "sum"),
            avg_clv=("historical_clv", "mean"),
            median_clv=("historical_clv", "median"),
            avg_aov=("aov", "mean"),
            avg_purchase_frequency=("purchase_frequency", "mean"),
        )
    )
    total_revenue = summary["total_revenue"].sum()
    summary["revenue_share"] = (
        summary["total_revenue"] / total_revenue if total_revenue else 0.0
    )
    order = ["Low Value", "Medium", "High Value"]
    summary["sort_order"] = summary["clv_segment"].map({k: i for i, k in enumerate(order)})
    return summary.sort_values("sort_order").drop(columns="sort_order").reset_index(drop=True)
