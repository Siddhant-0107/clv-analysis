# Customer Lifetime Value Analysis

A product analytics project that measures observed customer value, segments customers by lifetime value, compares acquisition channels, and evaluates simple customer economics through CLV:CAC.

## Business Problem

Customer acquisition volume does not necessarily translate into customer value. This project uses transaction history to answer:

- How much revenue does each customer generate?
- How frequently do customers purchase?
- Which customer groups contribute the most revenue?
- Which acquisition channels generate higher-value customers?
- Which channels show the strongest observed CLV:CAC?

## Methodology

### 1. Data cleaning
Only completed transactions with valid customer IDs, dates, positive transaction amounts, and recognized acquisition channels are used in revenue analysis.

### 2. Customer metrics
For each customer we calculate:

- Total revenue
- Purchase frequency
- Average order value (AOV)
- First and last purchase date
- Observed lifespan in days
- Active months
- Purchases per active month
- Revenue per active month

### 3. Historical CLV
The primary metric is **historical CLV**:

`Historical CLV = cumulative completed customer revenue during the observation window`

This is a measure of realized value, not a prediction of future revenue.

### 4. CLV segmentation
Customers are ranked by observed CLV and grouped into approximately:

- Low Value: bottom 20%
- Medium: middle 60%
- High Value: top 20%

### 5. Acquisition channel analysis
We compare customer volume, average/median CLV, AOV, purchase frequency, and observed CLV:CAC across acquisition channels.

### 6. CLV:CAC
Channel-level CAC is intentionally synthetic for portfolio demonstration. Observed CLV:CAC is calculated as:

`Average observed CLV / CAC`

It should not be interpreted as a live marketing attribution measurement.

## Dashboard

The Streamlit dashboard includes:

- KPI cards for customers, revenue, mean/median CLV, and top-10% revenue share
- CLV distribution
- CLV segment analysis
- Acquisition-channel comparison
- CLV:CAC analysis
- Customer explorer with filters
- Automated business interpretation

## Limitations

- Historical CLV is realized value and does not forecast future customer behavior.
- Customer lifespan is based on observed transaction dates and may understate the true customer relationship.
- Synthetic CAC assumptions are used for unit-economics demonstration.
- No predictive churn, survival, BG/NBD, Gamma-Gamma, or discounted-cash-flow model is included.

## Project Structure

```text
clv-analysis/
├── data/
│   ├── customers.csv
│   ├── transactions.csv
│   └── channel_cac.csv
├── src/
│   ├── __init__.py
│   ├── cleaning.py
│   ├── customer_metrics.py
│   ├── clv.py
│   └── segmentation.py
├── tests/
│   └── test_clv.py
├── app.py
├── generate_data.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Run Locally

```bash
py -3.10 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python generate_data.py
python -m pytest -q
python -m streamlit run app.py
```

## Portfolio Positioning

This project complements a product analytics portfolio by focusing on customer economics:

**Product Performance → Customer Behavior → Customer Economics**

## Interview Topics

Be prepared to explain:

1. Why historical CLV was used instead of predictive CLV.
2. Why median CLV is shown alongside average CLV.
3. Why one-purchase customers need a minimum calculation lifespan for rate metrics.
4. How CLV segments are constructed.
5. Why high customer volume does not necessarily mean high acquisition quality.
6. What CLV:CAC can and cannot tell us.
7. How synthetic CAC differs from real marketing-spend data.
