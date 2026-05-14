# Apex Insurance Group — P&C Executive Dashboard
## Tech Stack Reference v1.0 | April 2026

---

## Stack Summary

| Layer | Tool / Library | Version | Role |
|-------|---------------|---------|------|
| Data Preparation | Python 3.10+ | 3.10+ | ETL pipeline |
| Data Manipulation | pandas | ≥2.0 | DataFrame transforms, CSV I/O |
| Numeric Synthesis | numpy | ≥1.24 | Random generation, vectorised ops |
| Synthetic IDs | uuid (stdlib) | — | UUID generation for PKs |
| Date Generation | pandas.date_range | — | dim_date construction |
| CLV/Risk Scoring | scikit-learn (optional) | ≥1.3 | Min-max normalization of risk_score |
| Fake Data Fallback | faker | ≥20.0 | Synthetic names/IDs if raw CSVs absent |
| BI & Reporting | Power BI Desktop | Nov 2024+ | Model, visuals, DAX |
| DAX Engine | Vertipaq (embedded) | — | In-memory columnar store |
| Theming | JSON (apex_insurance_theme.json) | — | Custom palette |
| Documentation | Markdown | — | Implementation plan, DAX reference |
| Version Control | Git | — | Source control for pipeline + docs |

---

## Python Environment

### Required Packages
```
pandas>=2.0
numpy>=1.24
faker>=20.0
scikit-learn>=1.3
pathlib  # stdlib, no install needed
uuid     # stdlib, no install needed
```

### Install Command
```bash
pip install pandas numpy faker scikit-learn
```

### Python Version Compatibility
- Minimum: **Python 3.10** (uses `match` not required, but `pathlib` and walrus operator used)
- Tested: Python 3.12
- Not compatible: Python 2.x

---

## Data Flow

```
[Kaggle CSVs — /data/raw/]
        │
        ▼
[prepare_data.py]
  ├── Load & Audit (Step 1)
  ├── Build fact_claims (Step 2)
  ├── Build fact_premiums (Step 3)
  ├── Build dim_policy, dim_customer, dim_geography, dim_date (Step 4)
  ├── Referential Integrity Check (Step 5)  ← GATE
  └── Write 6 CSVs → /data/clean/ (Step 6)
        │
        ▼
[Power BI Desktop]
  ├── Import CSVs (Text/CSV connector)
  ├── Power Query: explicit type casting
  ├── Model: 6 single-direction relationships
  ├── DAX: 25+ measures in display folders
  └── 5 report pages → ApexInsurance_Dashboard.pbix
```

---

## Power BI Technical Details

### DAX Engine Constraints
| Constraint | Setting |
|-----------|---------|
| Bidirectional relationships | **Forbidden** (breaks filter propagation in star schema) |
| Auto date/time | Disable (we supply `dim_date`) |
| Auto-detect types in Power Query | Disable (set explicitly) |
| Load staging queries | Disable (only load final 6 tables) |

### Connector Used
- **Text/CSV** connector (not Excel, not SharePoint)
- File paths: relative to PBIX save location or absolute `/data/clean/*.csv`
- Encoding: UTF-8 (no BOM) — set in Python `to_csv(encoding='utf-8')`

### Map Visual Requirements
- **Filled Map** (choropleth): requires Bing Maps integration enabled
  - Power BI Desktop → File → Options → Security → **Use Map and Filled Map visuals**
- **Bubble Map**: uses `latitude`/`longitude` from `dim_geography`
- Geographic field: `dim_geography[state_full]` for choropleth recognition

### Theme File
- `apex_insurance_theme.json` — apply via View → Themes → Browse for themes
- Primary color: `#0072CE` (Apex Blue)
- Accent: `#1B3A6B` (Navy)
- Font: Segoe UI throughout

---

## File Encoding & Formats

| File | Format | Encoding | Delimiter |
|------|--------|----------|-----------|
| All `/data/raw/` files | CSV | UTF-8 | comma |
| All `/data/clean/` files | CSV | UTF-8 (no BOM) | comma |
| `apex_insurance_theme.json` | JSON | UTF-8 | — |
| `dax_measures_reference.md` | Markdown | UTF-8 | — |
| `ApexInsurance_Dashboard.pbix` | Binary (ZIP) | — | — |

---

## Key Design Decisions

### Why Star Schema (No Snowflake)?
- Vertipaq compresses repeated strings efficiently — no normalization win
- Simpler DAX: no multi-hop `RELATED()` chains
- Single-direction filter flow matches Power BI's default engine behavior
- Easier to maintain for non-technical Power BI consumers

### Why Synthetic Data Instead of Real Kaggle Data Verbatim?
- Kaggle datasets have inconsistent schemas — transformation required regardless
- Synthetic enrichment (fraud flags, CAT flags, CLV scores) adds insurance domain realism
- Row count targets (8K–12K claims, 10K–18K premiums) may require upsampling

### Why UUID for PKs?
- Collision-proof across all three source datasets when merging
- Power BI stores as Text — no integer overflow risk
- Easily traceable during debugging

### Why disable Auto Date/Time in Power BI?
- Auto Date/Time creates a hidden date table per date column
- Multiple hidden tables conflict with our `dim_date` and bloat the model
- Our `dim_date` with `date_key` (YYYYMMDD integer) gives full control

---

## Synthetic Data Quality Design

### LOB GWP Ranges (used in Step 3 synthesis)
| LOB | GWP Range | Expense Ratio | Cession Rate |
|-----|-----------|--------------|-------------|
| Auto | $800–$3,200 | 27% | 8% |
| Homeowners | $1,200–$4,800 | 29% | 12% |
| Commercial | $5,000–$45,000 | 32% | 18% |
| Liability | $2,500–$18,000 | 30% | 15% |

### Fraud Flagging Logic
- 5% random baseline (uniform across all claims)
- Auto-flag: `incurred_loss > $80,000 AND days_to_close < 7`

### CAT Flagging Logic
- Claims with `claim_type = "Weather"` in states FL, TX, LA, CA → 60% probability flag
- All other weather claims → 15% probability flag
- All other claim types → never flagged

### CLV Score Formula
```
clv_score = tenure_years × avg_premium_paid × (1 − loss_ratio)
```
Normalized to a 0–1000 range for readability.

### Risk Score Formula
```
raw_risk = claim_frequency × avg_incurred_loss
risk_score = MinMaxScaler(raw_risk) × 100 → integer 1–100
```
