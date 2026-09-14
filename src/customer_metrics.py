from __future__ import annotations

import pandas as pd


def build_customer_metrics(transactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate completed transactions into one row per customer."""
    if transactions.empty:
        raise ValueError("transactions cannot be empty")

    grouped = transactions.groupby("customer_id", as_index=False).agg(
        total_revenue=("amount", "sum"),
        purchase_frequency=("transaction_id", "nunique"),
        first_purchase=("transaction_date", "min"),
        last_purchase=("transaction_date", "max"),
        acquisition_channel=("acquisition_channel", "first"),
    )

    grouped["aov"] = grouped["total_revenue"] / grouped["purchase_frequency"]
    grouped["lifespan_days"] = (
        grouped["last_purchase"] - grouped["first_purchase"]
    ).dt.days
    grouped["calculation_lifespan_days"] = grouped["lifespan_days"].clip(lower=1)
    grouped["active_months"] = grouped["calculation_lifespan_days"] / 30.0
    grouped["purchases_per_active_month"] = (
        grouped["purchase_frequency"] / grouped["active_months"]
    )
    grouped["revenue_per_active_month"] = (
        grouped["total_revenue"] / grouped["active_months"]
    )
    grouped["annualized_clv_proxy"] = (
        grouped["revenue_per_active_month"] * 12
    )

    return grouped
