from __future__ import annotations

import pandas as pd
import pytest

from src.clv import (
    add_clv_cac,
    add_clv_metrics,
    channel_clv_cac,
    revenue_concentration,
)
from src.customer_metrics import build_customer_metrics
from src.segmentation import add_clv_segments


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": ["T1", "T2", "T3", "T4"],
            "customer_id": ["C1", "C1", "C2", "C2"],
            "transaction_date": pd.to_datetime(
                ["2025-01-01", "2025-01-31", "2025-02-01", "2025-03-01"]
            ),
            "amount": [100.0, 200.0, 300.0, 100.0],
            "acquisition_channel": ["Organic", "Organic", "Referral", "Referral"],
        }
    )


def test_total_revenue_and_frequency() -> None:
    metrics = build_customer_metrics(sample_transactions())
    c1 = metrics.loc[metrics["customer_id"] == "C1"].iloc[0]
    assert c1["total_revenue"] == 300.0
    assert c1["purchase_frequency"] == 2


def test_aov() -> None:
    metrics = build_customer_metrics(sample_transactions())
    c1 = metrics.loc[metrics["customer_id"] == "C1"].iloc[0]
    assert c1["aov"] == 150.0


def test_lifespan() -> None:
    metrics = build_customer_metrics(sample_transactions())
    c1 = metrics.loc[metrics["customer_id"] == "C1"].iloc[0]
    assert c1["lifespan_days"] == 30


def test_historical_clv_equals_observed_revenue() -> None:
    metrics = add_clv_metrics(build_customer_metrics(sample_transactions()))
    assert (metrics["historical_clv"] == metrics["total_revenue"]).all()


def test_clv_segments_cover_customers() -> None:
    metrics = add_clv_metrics(build_customer_metrics(sample_transactions()))
    segmented = add_clv_segments(metrics)
    assert segmented["clv_segment"].notna().all()
    assert set(segmented["clv_segment"]) <= {"Low Value", "Medium", "High Value"}


def test_revenue_concentration() -> None:
    metrics = add_clv_metrics(build_customer_metrics(sample_transactions()))
    share = revenue_concentration(metrics, top_fraction=0.5)

    # C2 generates 400 of the total 700 revenue, so the top 50% of
    # customers (one of two customers) contribute 400 / 700 of revenue.
    assert share == pytest.approx(400 / 700)


def test_customer_clv_cac_proxy() -> None:
    metrics = add_clv_metrics(build_customer_metrics(sample_transactions()))
    cac = pd.DataFrame(
        {
            "acquisition_channel": ["Organic", "Referral"],
            "cac": [100.0, 200.0],
        }
    )
    enriched = add_clv_cac(metrics, cac)
    c1 = enriched.loc[enriched["customer_id"] == "C1"].iloc[0]
    assert c1["customer_clv_cac_proxy"] == pytest.approx(3.0)


def test_channel_clv_cac_uses_average_clv() -> None:
    metrics = add_clv_metrics(build_customer_metrics(sample_transactions()))
    cac = pd.DataFrame(
        {
            "acquisition_channel": ["Organic", "Referral"],
            "cac": [100.0, 200.0],
        }
    )
    enriched = add_clv_cac(metrics, cac)
    summary = channel_clv_cac(enriched)
    organic = summary.loc[summary["acquisition_channel"] == "Organic"].iloc[0]

    # Organic has one customer in this fixture, so average CLV is 300.
    assert organic["avg_clv"] == pytest.approx(300.0)
    assert organic["clv_cac"] == pytest.approx(3.0)
