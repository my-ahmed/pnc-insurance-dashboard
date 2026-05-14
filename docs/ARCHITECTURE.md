# Apex Insurance Group — P&C Executive Dashboard
## Architecture Design Document v1.0 | April 2026

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  ┌──────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │ auto_insurance_  │  │ insurance_claims_ │  │ ny_pc_      │  │
│  │ claims.csv       │  │ policy.csv        │  │ premiums.csv│  │
│  │ (Kaggle)         │  │ (Kaggle)          │  │ (Kaggle)    │  │
│  └────────┬─────────┘  └────────┬──────────┘  └──────┬──────┘  │
└───────────┼──────────────────────┼────────────────────┼─────────┘
            │                      │                    │
            └──────────────────────┼────────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   prepare_data.py   │
                        │   ETL PIPELINE      │
                        │                     │
                        │  Step 1: Audit      │
                        │  Step 2: fact_claims│
                        │  Step 3: fact_prems │
                        │  Step 4: dimensions │
                        │  Step 5: RI CHECK ◄─┼── GATE
                        │  Step 6: write CSV  │
                        └──────────┬──────────┘
                                   │
            ┌──────────────────────┼────────────────────┐
            │              /data/clean/                  │
            │  ┌──────────────┐  ┌──────────────────┐   │
            │  │ fact_claims  │  │ fact_premiums     │   │
            │  │ .csv         │  │ .csv              │   │
            │  └──────────────┘  └──────────────────┘   │
            │  ┌──────────────┐  ┌──────────────────┐   │
            │  │ dim_policy   │  │ dim_customer      │   │
            │  │ .csv         │  │ .csv              │   │
            │  └──────────────┘  └──────────────────┘   │
            │  ┌──────────────┐  ┌──────────────────┐   │
            │  │ dim_geography│  │ dim_date          │   │
            │  │ .csv         │  │ .csv              │   │
            │  └──────────────┘  └──────────────────┘   │
            └──────────────────────┬─────────────────────┘
                                   │
                   ┌───────────────▼───────────────┐
                   │      POWER BI DESKTOP          │
                   │                                │
                   │  ┌──────────────────────────┐  │
                   │  │   VERTIPAQ IN-MEMORY DB  │  │
                   │  │   (Star Schema)          │  │
                   │  └──────────────────────────┘  │
                   │  ┌──────────────────────────┐  │
                   │  │   DAX MEASURE LIBRARY    │  │
                   │  │   25+ measures, 6 folders│  │
                   │  └──────────────────────────┘  │
                   │  ┌──────────────────────────┐  │
                   │  │   5 REPORT PAGES         │  │
                   │  │   40+ visuals            │  │
                   │  └──────────────────────────┘  │
                   └───────────────────────────────┘
```

---

## 2. Star Schema Data Model

### 2.1 Entity-Relationship Diagram

```
                        ┌─────────────────┐
                        │    dim_date     │
                        │─────────────────│
                        │ date_key (PK)   │
                        │ date            │
                        │ year            │
                        │ quarter         │
                        │ quarter_label   │
                        │ month           │
                        │ month_name      │
                        │ month_short     │
                        │ week            │
                        │ day_of_week     │
                        │ is_weekday      │
                        │ fiscal_year     │
                        │ fiscal_quarter  │
                        └────────┬────────┘
                                 │ 1
                    ─────────────┼─────────────
                    │            │             │
                    │ ∞          │ ∞           │ ∞
    ┌───────────────┴─┐  ┌───────┴──────────┐  └──────────────┐
    │   dim_policy    │  │   fact_claims    │  │ dim_geography │
    │─────────────────│  │──────────────────│  │───────────────│
    │ policy_id (PK)  ├──┤ claim_id (PK)    │  │ geography_id  │
    │ policy_type     │  │ policy_id (FK)   ├──┤ (PK)          │
    │ line_of_business│  │ customer_id (FK) │  │ state         │
    │ policy_start_   │  │ date_key (FK)    │  │ state_full    │
    │   date          │  │ geography_id (FK)│  │ region        │
    │ policy_end_date │  │ claim_status     │  │ cat_zone      │
    │ agent_id        │  │ claim_type       │  │ latitude      │
    │ channel         │  │ incurred_loss    │  │ longitude     │
    │ premium_tier    │  │ paid_loss        │  └───────────────┘
    └─────────────────┘  │ reserved_loss   │
           │ 1           │ claim_open_date  │
           │             │ claim_close_date │
           │ ∞           │ days_to_close    │
    ┌──────┴──────────┐  │ fraud_flag       │
    │  fact_premiums  │  │ line_of_business │
    │─────────────────│  │ catastrophe_flag │
    │ premium_id (PK) │  └──────────────────┘
    │ policy_id (FK)  │         │ ∞
    │ date_key (FK)   │         │
    │ gross_written_  │  ┌──────┴────────┐
    │   premium       │  │ dim_customer  │
    │ net_earned_     │  │───────────────│
    │   premium       │  │ customer_id   │
    │ ceded_premium   │  │ (PK)          │
    │ expense_amount  │  │ age_band      │
    │ line_of_business│  │ gender        │
    │ renewal_flag    │  │ customer_     │
    └─────────────────┘  │   segment     │
                         │ tenure_years  │
                         │ clv_score     │
                         │ risk_score    │
                         └───────────────┘
```

### 2.2 Relationship Cardinalities

| Relationship | Type | Direction | Cardinality |
|-------------|------|-----------|------------|
| `fact_claims → dim_date` | FK→PK | Single (→) | Many-to-One |
| `fact_claims → dim_policy` | FK→PK | Single (→) | Many-to-One |
| `fact_claims → dim_customer` | FK→PK | Single (→) | Many-to-One |
| `fact_claims → dim_geography` | FK→PK | Single (→) | Many-to-One |
| `fact_premiums → dim_date` | FK→PK | Single (→) | Many-to-One |
| `fact_premiums → dim_policy` | FK→PK | Single (→) | Many-to-One |

**Constraint:** No bidirectional cross-filtering. Filter context flows fact → dim only.

---

## 3. DAX Architecture

### 3.1 Measure Dependency Graph

```
[LOW — No dependencies]
  GWP
  Net Earned Premium
  Total Incurred Losses
  Total Paid Losses
  Total Reserve
  Total Claim Count
        │
        ▼
[MEDIUM — Reference LOW measures]
  Loss Ratio ─────────────────┐
  Expense Ratio               ├──► Combined Ratio
  YoY GWP Growth %            │
  Avg Claim Severity          │
  Claim Frequency             │
  Open Claims                 │
  Renewal Rate %              │
  CAT Loss Contribution %     │
  MTD Losses                  │
  QTD GWP                     │
  YTD Combined Ratio ◄────────┘
        │
        ▼
[HARD — Reference MEDIUM + engine patterns]
  Rolling 12M Loss Ratio    (DATESINPERIOD + LASTDATE)
  Rolling 3M Claims         (DATESINPERIOD)
  State Risk Rank           (RANKX + ALL)
  Is Top 5 State            (TOPN + INTERSECT)
  Loss % of Grand Total     (ALL + DIVIDE)
  Customer LTV              (AVERAGEX + VALUES)
  Premium Trend Slope       (ADDCOLUMNS + regression)
  Reserve Adequacy Ratio    (VAR/RETURN)
  New Business Mix %        (CALCULATE filter)
  CR Variance vs Target     (arithmetic on Combined Ratio)
```

### 3.2 Filter Context Flow

```
[Slicer: Year]         [Slicer: LOB]         [Slicer: Region]
       │                     │                      │
       ▼                     ▼                      ▼
  dim_date               fact_claims           dim_geography
  (date_key)         (line_of_business)           (region)
       │                     │
       └─────────────────────┘
                    ▼
             [Visual Filter Context]
                    │
                    ▼
         DAX Measures evaluate
         within filtered context
```

---

## 4. Report Page Architecture

### Page Template (Applied to All 5 Pages)

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER BAR  │  #1B3A6B (Navy)  │  White page title text    │
├──────┬──────┬──────┬──────┬──────────────────────────────┤
│ KPI  │ KPI  │ KPI  │ KPI  │  [Year Slicer] [LOB Slicer]  │  ← KPI Strip
│ Card │ Card │ Card │ Card │                               │
├──────┴──────┴──────┴──────┴──────────────────────────────┤
│                                                             │
│              PRIMARY CONTENT AREA                           │
│         (Charts, matrices, maps, gauges)                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  FOOTER  │  "Last Refreshed: [date]"  │  Segoe UI 9pt       │
└─────────────────────────────────────────────────────────────┘
```

### Page-by-Page Visual Inventory

| Page | Audience | Key Visuals | DAX Tier |
|------|----------|------------|---------|
| 1 — Executive KPI Scorecard | CEO, Board | KPI Cards, Gauge, Line+Column combo, Donut | Low–Med |
| 2 — Claims Deep Dive | CFO, Claims VP | Donut, Bar, Stacked Bar, Area, Matrix, Waterfall | Medium |
| 3 — Underwriting Performance | CUO | Bar, Waterfall, Gauge, Stacked Column, Matrix, Small Multiples | Med–Hard |
| 4 — Geographic Risk Intelligence | Risk Committee, Actuaries | Filled Map, Table, Bar, Treemap, Bubble Map, Small Multiples | Hard |
| 5 — Portfolio Profitability & Forecast | CEO, CFO, IR | Line, Card, Bar+Matrix, Scatter, Area | Very Hard |

---

## 5. ETL Pipeline Architecture

### 5.1 Pipeline Stages

```
┌────────────────────────────────────────────────────────────┐
│                    prepare_data.py                         │
│                                                            │
│  STAGE 1: LOAD & AUDIT                                     │
│  ├── Try load /data/raw/*.csv                              │
│  ├── If missing → full synthetic fallback                  │
│  └── Print: columns, dtypes, nulls, shape per file        │
│                                                            │
│  STAGE 2: FACT_CLAIMS BUILD                                │
│  ├── Map claim fields → target schema                      │
│  ├── Generate UUIDs for claim_id                           │
│  ├── Calc days_to_close (null-safe)                        │
│  ├── Derive reserved_loss = max(incurred - paid, 0)        │
│  ├── Synthesize fraud_flag (5% random + >80K/<7days rule)  │
│  └── Synthesize catastrophe_flag (weather+state rules)     │
│                                                            │
│  STAGE 3: FACT_PREMIUMS BUILD                              │
│  ├── One row per policy per active year                     │
│  ├── GWP: use source if available, else LOB-range synthesis │
│  ├── ceded_premium = GWP × cession_rate                    │
│  ├── expense_amount = GWP × expense_ratio                  │
│  └── net_earned_premium = (GWP - ceded) × earning_factor   │
│                                                            │
│  STAGE 4: DIMENSION BUILD                                  │
│  ├── dim_policy: extract + qcut premium_tier (3 buckets)   │
│  ├── dim_customer: extract + synthesize clv_score,         │
│  │    risk_score                                           │
│  ├── dim_geography: hardcoded 50-state lookup dict         │
│  └── dim_date: pd.date_range(2020-01-01, 2025-12-31)      │
│                                                            │
│  STAGE 5: REFERENTIAL INTEGRITY CHECK ◄── GATE            │
│  ├── fact_claims.policy_id ⊆ dim_policy.policy_id          │
│  ├── fact_claims.customer_id ⊆ dim_customer.customer_id    │
│  ├── fact_claims.date_key ⊆ dim_date.date_key              │
│  ├── fact_claims.geography_id ⊆ dim_geography.geography_id │
│  ├── fact_premiums.policy_id ⊆ dim_policy.policy_id        │
│  ├── fact_premiums.date_key ⊆ dim_date.date_key            │
│  └── Print PASS/FAIL table → abort if any FAIL             │
│                                                            │
│  STAGE 6: WRITE OUTPUT                                     │
│  ├── Write 6 CSVs to /data/clean/ (UTF-8, no BOM)         │
│  └── Print final row count summary                         │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Null Handling Policy

| Scenario | Handling |
|---------|---------|
| FK columns in fact tables | Assert non-null; raise ValueError if any found |
| `claim_close_date` | Nullable — open claims have null close date |
| `days_to_close` | Null when `claim_close_date` is null |
| Source columns not in target schema | Drop silently after mapping |
| Source columns with nulls in non-FK fields | Fill with mode (categorical) or median (numeric) |

### 5.3 Referential Integrity Check Output Format

```
╔══════════════════════════════════════════════════════╗
║          REFERENTIAL INTEGRITY CHECK RESULTS         ║
╠══════════════╦═══════════════════╦══════════╦═══════╣
║ Fact Table   ║ FK Column         ║ Orphans  ║ Status║
╠══════════════╬═══════════════════╬══════════╬═══════╣
║ fact_claims  ║ policy_id         ║ 0        ║ PASS  ║
║ fact_claims  ║ customer_id       ║ 0        ║ PASS  ║
║ fact_claims  ║ date_key          ║ 0        ║ PASS  ║
║ fact_claims  ║ geography_id      ║ 0        ║ PASS  ║
║ fact_premiums║ policy_id         ║ 0        ║ PASS  ║
║ fact_premiums║ date_key          ║ 0        ║ PASS  ║
╚══════════════╩═══════════════════╩══════════╩═══════╝
All referential integrity checks PASSED. Safe to open Power BI.
```

---

## 6. Governance & Quality Controls

### Synthetic Data Quality Targets
| Metric | Target | Enforcement |
|--------|--------|------------|
| Overall Loss Ratio | 62%–74% | Assert in pipeline |
| Combined Ratio | 94%–103% | Assert in pipeline |
| Fraud Rate | 4%–7% | Assert in pipeline |
| CAT Loss Share | 12%–20% | Assert in pipeline |
| Renewal Rate | 82%–88% | Assert in pipeline |
| Auto LOB GWP Share | 40%–50% | Assert in pipeline |

### Key Assertions in Pipeline
1. `dim_date` row count == 2192 (exactly 6 years, 2020–2025)
2. `dim_geography` row count == 50 (all US states)
3. `fact_claims` row count in [8000, 12000]
4. `fact_premiums` row count in [10000, 18000]
5. No null values in any FK column
6. All 6 referential integrity checks PASS

---

## 7. File-Level Schema Reference

### fact_claims.csv
| Column | Type | Nullable | FK Target |
|--------|------|---------|----------|
| claim_id | str | No | — (PK) |
| policy_id | str | No | dim_policy |
| customer_id | str | No | dim_customer |
| date_key | int | No | dim_date |
| geography_id | str | No | dim_geography |
| claim_status | str | No | — |
| claim_type | str | No | — |
| incurred_loss | float | No | — |
| paid_loss | float | No | — |
| reserved_loss | float | No | — |
| claim_open_date | date | No | — |
| claim_close_date | date | Yes | — |
| days_to_close | int | Yes | — |
| fraud_flag | bool | No | — |
| line_of_business | str | No | — |
| catastrophe_flag | bool | No | — |

### fact_premiums.csv
| Column | Type | Nullable | FK Target |
|--------|------|---------|----------|
| premium_id | str | No | — (PK) |
| policy_id | str | No | dim_policy |
| date_key | int | No | dim_date |
| gross_written_premium | float | No | — |
| net_earned_premium | float | No | — |
| ceded_premium | float | No | — |
| expense_amount | float | No | — |
| line_of_business | str | No | — |
| renewal_flag | bool | No | — |

### dim_policy.csv
| Column | Type | Nullable |
|--------|------|---------|
| policy_id | str | No (PK) |
| policy_type | str | No |
| line_of_business | str | No |
| policy_start_date | date | No |
| policy_end_date | date | No |
| agent_id | str | No |
| channel | str | No |
| premium_tier | str | No |

### dim_customer.csv
| Column | Type | Nullable |
|--------|------|---------|
| customer_id | str | No (PK) |
| age_band | str | No |
| gender | str | No |
| customer_segment | str | No |
| tenure_years | int | No |
| clv_score | float | No |
| risk_score | int | No |

### dim_geography.csv
| Column | Type | Nullable |
|--------|------|---------|
| geography_id | str | No (PK) |
| state | str | No |
| state_full | str | No |
| region | str | No |
| cat_zone | str | No |
| latitude | float | No |
| longitude | float | No |

### dim_date.csv
| Column | Type | Nullable |
|--------|------|---------|
| date_key | int | No (PK) |
| date | date | No |
| year | int | No |
| quarter | int | No |
| quarter_label | str | No |
| month | int | No |
| month_name | str | No |
| month_short | str | No |
| week | int | No |
| day_of_week | str | No |
| is_weekday | bool | No |
| fiscal_year | int | No |
| fiscal_quarter | str | No |
