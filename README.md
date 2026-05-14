# P&C Insurance Executive Dashboard

A Power BI executive dashboard for a fictional P&C insurer (Apex Insurance Group), backed by a Python ETL pipeline that generates a realistic star-schema dataset.

## Preview

[📄 View Report PDF](./report.pdf)

## Overview

| Layer | Tools |
|-------|-------|
| Data prep | Python · pandas · numpy · faker · scikit-learn |
| BI & visuals | Power BI Desktop · DAX · Vertipaq |
| Data model | Star schema — 2 fact tables, 4 dimension tables |

## Dashboard Pages

1. **Executive Summary** — GWP, loss ratio, combined ratio KPIs
2. **Claims Analysis** — frequency, severity, CAT & fraud flags
3. **Premium & Revenue** — written vs earned, cession rates by LOB
4. **Customer Insights** — CLV scores, retention, geographic heatmap
5. **Risk Overview** — risk score distribution, high-risk segment drill-down

## Data Pipeline

```
data/raw/ (Kaggle CSVs)
    └── prepare_data.py (ETL)
            └── data/clean/ (6 CSVs → Power BI)
```

`prepare_data.py` builds ~10K claims and ~14K premium records with synthetic fraud flags, CAT flags, and CLV/risk scores.

## Running the Pipeline

```bash
pip install pandas numpy faker scikit-learn
python prepare_data.py
```

Then open `Report.pbix` in Power BI Desktop and refresh the data source to `data/clean/`.
