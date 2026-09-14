from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "transaction_id",
    "customer_id",
    "transaction_date",
    "amount",
    "acquisition_channel",
    "product_category",
    "order_status",
}
VALID_CHANNELS = {
    "Organic",
    "Paid Search",
    "Social Media",
    "Email",
    "Referral",
    "Affiliate",
}


def clean_transactions(path: str | Path) -> pd.DataFrame:
    """Load and clean transactions, keeping completed positive-value orders."""
    df = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    df = df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # Transaction IDs must be unique; keep the first record if source data is duplicated.
    df = df.drop_duplicates(subset="transaction_id", keep="first")
    df = df.dropna(subset=["transaction_id", "customer_id", "transaction_date", "amount"])
    df = df[df["amount"] > 0]
    df = df[df["order_status"].eq("Completed")]
    df = df[df["acquisition_channel"].isin(VALID_CHANNELS)]
    df = df.sort_values(["customer_id", "transaction_date", "transaction_id"])

    if df.empty:
        raise ValueError("Cleaning produced zero usable completed transactions.")

    return df.reset_index(drop=True)
