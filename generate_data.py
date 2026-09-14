from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_CUSTOMERS = 10_000
START_DATE = pd.Timestamp("2025-01-01")
END_DATE = pd.Timestamp("2026-06-30")

CHANNELS = ["Organic", "Paid Search", "Social Media", "Email", "Referral", "Affiliate"]
CHANNEL_PROBS = [0.24, 0.23, 0.18, 0.10, 0.11, 0.14]
CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Beauty", "Sports"]
CATEGORY_PROBS = [0.22, 0.27, 0.21, 0.15, 0.15]
CAC_BY_CHANNEL = {
    "Organic": 80.0,
    "Paid Search": 350.0,
    "Social Media": 250.0,
    "Email": 50.0,
    "Referral": 120.0,
    "Affiliate": 180.0,
}


def generate_transactions(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate a deterministic synthetic customer + transaction dataset."""
    rng = np.random.default_rng(seed)

    customers = pd.DataFrame(
        {
            "customer_id": [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
            "acquisition_channel": rng.choice(
                CHANNELS, size=N_CUSTOMERS, p=CHANNEL_PROBS
            ),
        }
    )

    # Customer-level propensity creates realistic variation in frequency and spend.
    segment = rng.choice(
        ["low", "medium", "high"], size=N_CUSTOMERS, p=[0.30, 0.55, 0.15]
    )
    base_lambda = np.select(
        [segment == "low", segment == "medium", segment == "high"],
        [1.4, 4.0, 10.0],
    )
    spend_multiplier = np.select(
        [segment == "low", segment == "medium", segment == "high"],
        [0.75, 1.0, 1.55],
    )

    channel_retention = customers["acquisition_channel"].map(
        {
            "Organic": 1.10,
            "Paid Search": 0.88,
            "Social Media": 0.82,
            "Email": 1.02,
            "Referral": 1.28,
            "Affiliate": 0.95,
        }
    ).to_numpy()

    rows: list[dict[str, object]] = []
    transaction_counter = 1

    for idx, customer_id in enumerate(customers["customer_id"]):
        channel = customers.loc[idx, "acquisition_channel"]
        acquisition_date = START_DATE + pd.Timedelta(
            days=int(rng.integers(0, (END_DATE - START_DATE).days - 30))
        )

        # High-value / referral customers have a slightly longer active window.
        remaining_days = max((END_DATE - acquisition_date).days, 1)
        active_fraction = np.clip(
            rng.beta(2.2, 1.5) * channel_retention[idx], 0.18, 1.0
        )
        last_possible_date = min(
            END_DATE,
            acquisition_date + pd.Timedelta(days=max(int(remaining_days * active_fraction), 1)),
        )

        expected_orders = base_lambda[idx] * (0.65 + remaining_days / 365.0)
        n_orders = max(1, int(rng.poisson(expected_orders)))
        dates = pd.to_datetime(
            rng.integers(
                acquisition_date.value // 86_400_000_000_000,
                (last_possible_date.value // 86_400_000_000_000) + 1,
                size=n_orders,
            ),
            unit="D",
        )
        dates = np.sort(dates)

        for date in dates:
            category = rng.choice(CATEGORIES, p=CATEGORY_PROBS)
            category_multiplier = {
                "Electronics": 1.55,
                "Fashion": 0.82,
                "Home & Kitchen": 1.15,
                "Beauty": 0.74,
                "Sports": 0.95,
            }[category]
            amount = (
                rng.lognormal(mean=np.log(750), sigma=0.58)
                * spend_multiplier[idx]
                * category_multiplier
            )
            status = "Cancelled" if rng.random() < 0.055 else "Completed"

            rows.append(
                {
                    "transaction_id": f"T{transaction_counter:07d}",
                    "customer_id": customer_id,
                    "transaction_date": date,
                    "amount": round(float(amount), 2),
                    "acquisition_channel": channel,
                    "product_category": category,
                    "order_status": status,
                }
            )
            transaction_counter += 1

    transactions = pd.DataFrame(rows)

    # Add a tiny amount of realistic data quality noise to validate cleaning logic.
    if len(transactions) >= 100:
        missing_idx = rng.choice(transactions.index, size=25, replace=False)
        transactions.loc[missing_idx, "product_category"] = None

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    customers.to_csv(output_dir / "customers.csv", index=False)
    transactions.to_csv(output_dir / "transactions.csv", index=False)
    pd.DataFrame(
        [{"acquisition_channel": k, "cac": v} for k, v in CAC_BY_CHANNEL.items()]
    ).to_csv(output_dir / "channel_cac.csv", index=False)

    return customers, transactions


if __name__ == "__main__":
    customers_df, transactions_df = generate_transactions()
    print(f"Generated {len(customers_df):,} customers")
    print(f"Generated {len(transactions_df):,} transactions")
    print("Saved files to data/")
