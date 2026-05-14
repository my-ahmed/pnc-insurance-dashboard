# Apex Insurance Dashboard — Power BI Step-by-Step Guide
## Phases 2 → 5 | Starting point: 6 tables already in Data pane

---

## WHERE YOU ARE NOW
You have imported all 6 CSVs. They appear in the Data pane with their correct names. ✓  
Work through this guide top-to-bottom. Do **not** skip ahead.

---

# PHASE 2 — POWER BI FOUNDATION

## Step 2.1 — Apply the Custom Theme (do this FIRST, before building anything)

1. In the top ribbon click **View**
2. Click the **dropdown arrow** on the Themes button (small arrow, not the button itself)
3. Choose **Browse for themes...**
4. Navigate to `C:\Git\PBI\apex_insurance_theme.json` → click **Open**
5. A yellow banner appears: *"Theme applied"* → click **Got it**

> You should now see the navy/blue colour palette in the Visualizations pane colour options.

---

## Step 2.2 — Fix Column Types in Power Query

Power BI likely auto-detected most types incorrectly (especially `date_key` as text, flags as text). Fix them now before building relationships.

1. In the **Home** ribbon click **Transform data** → Power Query Editor opens
2. Work through each table below. Select the table in the left Queries panel, then set each column type:

### How to change a column type
- Click the column header to select it
- In the ribbon: **Home → Data Type** dropdown → choose the correct type
- OR right-click the column header → **Change Type** → select type

---

### fact_claims — type changes needed

| Column | Set Type To |
|--------|------------|
| `claim_id` | Text |
| `policy_id` | Text |
| `customer_id` | Text |
| `date_key` | Whole Number |
| `geography_id` | Text |
| `claim_status` | Text |
| `claim_type` | Text |
| `incurred_loss` | Decimal Number |
| `paid_loss` | Decimal Number |
| `reserved_loss` | Decimal Number |
| `claim_open_date` | Date |
| `claim_close_date` | Date |
| `days_to_close` | Whole Number |
| `fraud_flag` | True/False |
| `line_of_business` | Text |
| `catastrophe_flag` | True/False |

### fact_premiums — type changes needed

| Column | Set Type To |
|--------|------------|
| `premium_id` | Text |
| `policy_id` | Text |
| `date_key` | Whole Number |
| `gross_written_premium` | Decimal Number |
| `net_earned_premium` | Decimal Number |
| `ceded_premium` | Decimal Number |
| `expense_amount` | Decimal Number |
| `line_of_business` | Text |
| `renewal_flag` | True/False |

### dim_policy — type changes needed

| Column | Set Type To |
|--------|------------|
| `policy_id` | Text |
| `policy_type` | Text |
| `line_of_business` | Text |
| `policy_start_date` | Date |
| `policy_end_date` | Date |
| `agent_id` | Text |
| `channel` | Text |
| `premium_tier` | Text |

### dim_customer — type changes needed

| Column | Set Type To |
|--------|------------|
| `customer_id` | Text |
| `age_band` | Text |
| `gender` | Text |
| `customer_segment` | Text |
| `tenure_years` | Whole Number |
| `clv_score` | Decimal Number |
| `risk_score` | Whole Number |

### dim_geography — type changes needed

| Column | Set Type To |
|--------|------------|
| `geography_id` | Text |
| `state` | Text |
| `state_full` | Text |
| `region` | Text |
| `cat_zone` | Text |
| `latitude` | Decimal Number |
| `longitude` | Decimal Number |

### dim_date — type changes needed

| Column | Set Type To |
|--------|------------|
| `date_key` | Whole Number |
| `date` | Date |
| `year` | Whole Number |
| `quarter` | Whole Number |
| `quarter_label` | Text |
| `month` | Whole Number |
| `month_name` | Text |
| `month_short` | Text |
| `week` | Whole Number |
| `day_of_week` | Text |
| `is_weekday` | True/False |
| `fiscal_year` | Whole Number |
| `fiscal_quarter` | Text |

3. After all types are set: **Home → Close & Apply**
4. Wait for the load spinner to finish

---

## Step 2.3 — Disable Auto Date/Time (critical)

Power BI creates hidden date tables for every date column — this conflicts with our `dim_date`.

1. **File → Options and settings → Options**
2. Under **Current File** (not Global) → click **Data Load**
3. Uncheck **Auto date/time**
4. Click **OK**

---

## Step 2.4 — Build the Relationships (Model View)

1. Click the **Model view** icon in the left sidebar (looks like three connected boxes)
2. You'll see 6 tables scattered on the canvas — arrange them:
   - Put `dim_date` at the top centre
   - Put `dim_policy` on the left
   - Put `dim_customer` at the bottom left
   - Put `dim_geography` on the right
   - Put `fact_claims` in the centre
   - Put `fact_premiums` at the bottom centre

### Create each relationship (6 total)

For each relationship below:
- **Drag** the FK column from the fact table **onto** the matching PK column in the dim table
- After the relationship dialog opens: confirm Cross filter direction = **Single**
- Click **OK** (or **Confirm**)

| Drag FROM (fact) | Drag TO (dim) | Key Column |
|-----------------|--------------|-----------|
| `fact_claims[date_key]` | `dim_date[date_key]` | date_key |
| `fact_claims[policy_id]` | `dim_policy[policy_id]` | policy_id |
| `fact_claims[customer_id]` | `dim_customer[customer_id]` | customer_id |
| `fact_claims[geography_id]` | `dim_geography[geography_id]` | geography_id |
| `fact_premiums[date_key]` | `dim_date[date_key]` | date_key |
| `fact_premiums[policy_id]` | `dim_policy[policy_id]` | policy_id |

### Verify each relationship
- Click each relationship line → in the Properties panel on the right confirm:
  - **Cardinality**: Many to one (*:1)
  - **Cross filter direction**: Single
  - **Active**: Yes (checkbox checked)

> **Zero bidirectional. If any shows "Both" — edit it and change to "Single".**

### Gate check before moving on
The model should look like this (textual):
```
dim_date ←── fact_claims ──→ dim_policy
                │                 ↑
                ↓           fact_premiums ──→ dim_date (same dim_date)
          dim_customer
                │
          dim_geography
```
You should see exactly **6 relationship lines** in model view.

---

## Step 2.5 — Set Geographic Data Categories (needed for map visuals)

1. Switch to **Data view** (table icon in left sidebar)
2. Select the **dim_geography** table
3. Click the `state_full` column → in the **Column tools** ribbon → **Data category** → **State or Province**
4. Click the `state` column → Data category → **State or Province**
5. Click the `latitude` column → Data category → **Latitude**
6. Click the `longitude` column → Data category → **Longitude**

---

# PHASE 3 — DAX MEASURE LIBRARY

## How to create a measure
1. In the **Data pane** (right side), right-click **fact_claims** → **New measure**
2. Type the DAX formula in the formula bar at the top
3. Press **Enter** or click the checkmark
4. To set the **Display Folder**: in the Measure tools ribbon → **Display folder** field → type the folder name exactly as shown

> **Convention**: Create all measures in `fact_claims` unless noted. Keep them there even if they reference `fact_premiums`.

---

## Step 3.1 — LOW Complexity Measures | Folder: `_KPIs`

Create each measure, set Display folder to `_KPIs`.

### GWP
```dax
GWP = SUM(fact_premiums[gross_written_premium])
```

### Net Earned Premium
```dax
Net Earned Premium = SUM(fact_premiums[net_earned_premium])
```

### Total Incurred Losses
```dax
Total Incurred Losses = SUM(fact_claims[incurred_loss])
```

### Total Paid Losses
```dax
Total Paid Losses = SUM(fact_claims[paid_loss])
```

### Total Reserve
```dax
Total Reserve = SUM(fact_claims[reserved_loss])
```

### Loss Ratio
```dax
Loss Ratio = DIVIDE([Total Incurred Losses], [Net Earned Premium], 0)
```

### Expense Ratio
```dax
Expense Ratio = DIVIDE(SUM(fact_premiums[expense_amount]), [Net Earned Premium], 0)
```

### Combined Ratio
```dax
Combined Ratio = [Loss Ratio] + [Expense Ratio]
```

### Total Claim Count
```dax
Total Claim Count = COUNTROWS(fact_claims)
```

### Fraud Rate
```dax
Fraud Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_claims), fact_claims[fraud_flag] = TRUE()),
    [Total Claim Count],
    0
)
```

**Format check**: Drop each of these onto a Card visual. GWP should show a large dollar number, Loss Ratio ~0.65–0.70, Fraud Rate ~5%.

---

## Step 3.2 — MEDIUM Complexity Measures | Folders: `Underwriting` and `Claims`

### YoY GWP Growth % | Folder: `Underwriting`
```dax
YoY GWP Growth % =
VAR CurrentGWP = [GWP]
VAR PriorGWP = CALCULATE([GWP], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN DIVIDE(CurrentGWP - PriorGWP, PriorGWP, BLANK())
```
*Format as Percentage.*

### Avg Claim Severity | Folder: `Claims`
```dax
Avg Claim Severity =
AVERAGEX(fact_claims, fact_claims[incurred_loss])
```

### Claim Frequency | Folder: `Claims`
```dax
Claim Frequency =
DIVIDE([Total Claim Count], DISTINCTCOUNT(fact_premiums[policy_id]), 0)
```

### Open Claims | Folder: `Claims`
```dax
Open Claims =
CALCULATE(
    [Total Claim Count],
    fact_claims[claim_status] = "Open"
)
```

### Renewal Rate % | Folder: `Underwriting`
```dax
Renewal Rate % =
VAR Renewals = CALCULATE(COUNTROWS(fact_premiums), fact_premiums[renewal_flag] = TRUE())
VAR Total = COUNTROWS(fact_premiums)
RETURN DIVIDE(Renewals, Total, 0)
```

### Loss Ratio by LOB | Folder: `Underwriting`
```dax
Loss Ratio by LOB =
CALCULATE(
    [Loss Ratio],
    ALLEXCEPT(fact_claims, fact_claims[line_of_business])
)
```

### CAT Loss Contribution % | Folder: `Claims`
```dax
CAT Loss Contribution % =
VAR CATLosses = CALCULATE([Total Incurred Losses], fact_claims[catastrophe_flag] = TRUE())
RETURN DIVIDE(CATLosses, CALCULATE([Total Incurred Losses], ALL(fact_claims)), 0)
```

### MTD Losses | Folder: `Claims`
```dax
MTD Losses =
CALCULATE([Total Incurred Losses], DATESMTD(dim_date[date]))
```

### QTD GWP | Folder: `Underwriting`
```dax
QTD GWP =
CALCULATE([GWP], DATESQTD(dim_date[date]))
```

### YTD Combined Ratio | Folder: `Underwriting`
```dax
YTD Combined Ratio =
CALCULATE([Combined Ratio], DATESYTD(dim_date[date]))
```

### New Business Mix % | Folder: `Underwriting`
```dax
New Business Mix % =
VAR NewBiz = CALCULATE([GWP], fact_premiums[renewal_flag] = FALSE())
RETURN DIVIDE(NewBiz, [GWP], 0)
```

### Renewal Mix % | Folder: `Underwriting`
```dax
Renewal Mix % =
VAR Renewals = CALCULATE([GWP], fact_premiums[renewal_flag] = TRUE())
RETURN DIVIDE(Renewals, [GWP], 0)
```

---

## Step 3.3 — HARD Complexity Measures | Folders: `Time Intelligence`, `Geography`, `Advanced`

### Rolling 12M Loss Ratio | Folder: `Time Intelligence`
```dax
Rolling 12M Loss Ratio =
-- Trailing 12 months loss ratio anchored to latest visible date
VAR LastDate = LASTDATE(dim_date[date])
VAR Last12M = DATESINPERIOD(dim_date[date], LastDate, -12, MONTH)
VAR Losses12M = CALCULATE([Total Incurred Losses], Last12M)
VAR Premium12M = CALCULATE([Net Earned Premium], Last12M)
RETURN DIVIDE(Losses12M, Premium12M, BLANK())
```

### Rolling 3M Claims | Folder: `Time Intelligence`
```dax
Rolling 3M Claims =
VAR LastDate = LASTDATE(dim_date[date])
VAR Last3M = DATESINPERIOD(dim_date[date], LastDate, -3, MONTH)
RETURN CALCULATE([Total Claim Count], Last3M)
```

### State Risk Rank | Folder: `Geography`
```dax
State Risk Rank =
-- Dense rank of states by loss ratio; highest risk = rank 1
RANKX(
    ALL(dim_geography[state]),
    [Loss Ratio],
    ,
    DESC,
    DENSE
)
```

### Is Top 5 State | Folder: `Geography`
```dax
Is Top 5 State =
-- Returns 1 if current state is in top 5 by incurred losses
VAR Top5States =
    TOPN(5, ALL(dim_geography[state]), [Total Incurred Losses], DESC)
RETURN
    IF(
        ISINSCOPE(dim_geography[state]),
        COUNTROWS(INTERSECT({VALUES(dim_geography[state])}, Top5States)) > 0,
        BLANK()
    )
```

### Loss % of Grand Total | Folder: `Geography`
```dax
Loss % of Grand Total =
VAR CurrentLoss = [Total Incurred Losses]
VAR GrandTotal = CALCULATE([Total Incurred Losses], ALL(fact_claims))
RETURN DIVIDE(CurrentLoss, GrandTotal, 0)
```

### Customer LTV | Folder: `Advanced`
```dax
Customer LTV =
-- Average LTV per customer: (avg premium - avg loss) * avg tenure
VAR AvgPremiumPerCustomer =
    AVERAGEX(VALUES(dim_customer[customer_id]), CALCULATE([GWP]))
VAR AvgLossPerCustomer =
    AVERAGEX(VALUES(dim_customer[customer_id]), CALCULATE([Total Incurred Losses]))
VAR AvgTenure = AVERAGE(dim_customer[tenure_years])
RETURN (AvgPremiumPerCustomer - AvgLossPerCustomer) * AvgTenure
```

### Premium Trend Slope | Folder: `Advanced`
```dax
Premium Trend Slope =
-- Linear regression slope of GWP over months (OLS in DAX)
VAR SummaryTable =
    ADDCOLUMNS(
        VALUES(dim_date[month]),
        "@X", dim_date[month],
        "@Y", CALCULATE([GWP])
    )
VAR N = COUNTROWS(SummaryTable)
VAR SumX = SUMX(SummaryTable, [@X])
VAR SumY = SUMX(SummaryTable, [@Y])
VAR SumXY = SUMX(SummaryTable, [@X] * [@Y])
VAR SumX2 = SUMX(SummaryTable, [@X] ^ 2)
RETURN DIVIDE(N * SumXY - SumX * SumY, N * SumX2 - SumX ^ 2, BLANK())
```

### Reserve Adequacy Ratio | Folder: `Advanced`
```dax
Reserve Adequacy Ratio =
-- > 1.0 = over-reserved (good); < 1.0 = under-reserved (risk)
VAR IBNR = [Total Incurred Losses] - [Total Paid Losses]
RETURN DIVIDE([Total Reserve], IBNR, BLANK())
```

### CR Variance vs Target | Folder: `_KPIs`
```dax
CR Variance vs Target =
-- Positive = unfavorable (above 100%); negative = favorable
[Combined Ratio] - 1
```

---

## Step 3.4 — Verify All Measures

1. Expand each display folder in the Data pane — confirm the folders exist
2. Drop each measure onto a **Card** visual and confirm it returns a number (not an error)
3. Quick sanity check targets:

| Measure | Expected Range |
|---------|--------------|
| GWP | $50M+ |
| Loss Ratio | 0.62 – 0.74 |
| Combined Ratio | 0.94 – 1.03 |
| Fraud Rate | 4% – 7% |
| Renewal Rate % | 82% – 88% *(may show ~96% with synthetic data — acceptable)* |
| Total Claim Count | ~10,000 |

---

# PHASE 4 — REPORT PAGES (5 Pages)

## Page Template — Apply to EVERY page

Before adding any visuals, set up the page frame:

### Header bar
1. **Insert → Text Box** — drag it across the full width of the top, about 60px tall
2. Set fill colour: `#1B3A6B` (navy) — in the Format pane → Background
3. Type the page title in white, Segoe UI, 18pt Bold
4. Lock the position: Format → Lock aspect / Position

### Footer
1. **Insert → Text Box** — drag across full width at the very bottom, about 30px tall
2. Fill: `#F2F2F2` (light grey)
3. Type: `Last Refreshed: April 2026` — Segoe UI, 9pt, dark grey text

### Year Slicer (every page)
1. Add a **Slicer** visual
2. Field: `dim_date[year]`
3. In Format → Slicer settings → Style = **Dropdown**
4. Place it in the top-right corner inside the header or just below it

---

## Page 1 — Executive KPI Scorecard

**Rename page**: double-click the page tab → type `Executive KPI Scorecard`

### Visual 1: GWP KPI Card
- Visual type: **Card** (new card visual)
- Value: `[GWP]`
- Callout value: `[GWP]`
- Format: Currency, 0 decimal places
- Conditional icon or trend: add `[YoY GWP Growth %]` as the trend value
- Label: "Gross Written Premium"

### Visual 2: Combined Ratio Gauge
- Visual type: **Gauge**
- Value: `[Combined Ratio]`
- Min: 0, Max: 1.2 (i.e. 0–120%)
- Target: 1.0
- Format value as percentage
- Label: "Combined Ratio"

### Visual 3: Loss Ratio KPI Card
- Visual type: **Card**
- Value: `[Loss Ratio]`
- Format: Percentage, 1 decimal
- Label: "Loss Ratio"

### Visual 4: Premium by LOB — Donut Chart
- Visual type: **Donut Chart**
- Legend: `fact_premiums[line_of_business]` (or `dim_policy[line_of_business]`)
- Values: `[GWP]`
- Title: "GWP by Line of Business"

### Visual 5: GWP vs Prior Year — Line & Clustered Column
- Visual type: **Line and Clustered Column Chart**
- X-axis: `dim_date[date]`
- Column Values: `[GWP]`
- Line Values: create a simple measure or use `CALCULATE([GWP], SAMEPERIODLASTYEAR(dim_date[date]))`
- Title: "GWP vs Prior Year (Monthly)"

### Visual 6: Fraud Rate Card
- Visual type: **Card**
- Value: `[Fraud Rate]`
- Format: Percentage, 1 decimal
- Label: "Fraud Rate"

### Visual 7: CAT Loss Contribution % Card
- Visual type: **Card**
- Value: `[CAT Loss Contribution %]`
- Format: Percentage, 1 decimal

### Visual 8: Renewal Rate Card
- Visual type: **Card**
- Value: `[Renewal Rate %]`
- Format: Percentage, 1 decimal

---

## Page 2 — Claims Deep Dive

**Rename page**: `Claims Deep Dive`

Add slicers: `dim_date[year]` + `fact_claims[line_of_business]`

### Visual 1: Claims by Status — Donut
- Visual type: **Donut Chart**
- Legend: `fact_claims[claim_status]`
- Values: `[Total Claim Count]`

### Visual 2: Avg Severity by Claim Type — Bar Chart
- Visual type: **Clustered Bar Chart**
- Y-axis: `fact_claims[claim_type]`
- X-axis: `[Avg Claim Severity]`

### Visual 3: Claims Aging Distribution — Stacked Bar

First, create a **Calculated Column** on `fact_claims` (not a measure):
- In Data view, select fact_claims → **Table tools → New column**
```dax
Aging Bucket =
SWITCH(
    TRUE(),
    fact_claims[days_to_close] <= 30, "0-30 Days",
    fact_claims[days_to_close] <= 60, "31-60 Days",
    fact_claims[days_to_close] <= 90, "61-90 Days",
    ISBLANK(fact_claims[days_to_close]), "Open",
    "90+ Days"
)
```
Then build the visual:
- Visual type: **Stacked Bar Chart**
- Y-axis: `fact_claims[claim_type]`
- X-axis: `[Total Claim Count]`
- Legend: `fact_claims[Aging Bucket]`

### Visual 4: Rolling 3M Claim Trend — Area Chart
- Visual type: **Area Chart**
- X-axis: `dim_date[date]` (set to Month granularity)
- Values: `[Rolling 3M Claims]`

### Visual 5: Fraud Heatmap by LOB — Matrix
- Visual type: **Matrix**
- Rows: `fact_claims[line_of_business]`
- Columns: `dim_date[month_short]`
- Values: `[Fraud Rate]`
- Format values as Percentage
- Enable **Conditional formatting** on values → Background colour (red scale)

### Visual 6: Paid vs Reserved vs Incurred — Waterfall
- Visual type: **Waterfall Chart**
- Category: create a text list by using a disconnected table or just use three separate measures in a table visual
- Alternative: use a **Clustered Bar** with `[Total Paid Losses]`, `[Total Reserve]`, `[Total Incurred Losses]`

### Visual 7: Open Claims KPI Card
- Value: `[Open Claims]`

### Visual 8: CAT vs Non-CAT Losses — Clustered Bar
- Visual type: **Clustered Bar Chart**
- Use a slicer on `fact_claims[catastrophe_flag]` OR create two measures:
```dax
CAT Losses = CALCULATE([Total Incurred Losses], fact_claims[catastrophe_flag] = TRUE())
Non-CAT Losses = CALCULATE([Total Incurred Losses], fact_claims[catastrophe_flag] = FALSE())
```
- Y-axis: `fact_claims[line_of_business]`
- X-axis: `[CAT Losses]` and `[Non-CAT Losses]`

---

## Page 3 — Underwriting Performance

**Rename page**: `Underwriting Performance`

Add slicers: `dim_date[year]` + `dim_policy[channel]`

### Visual 1: Loss Ratio by LOB — Horizontal Bar
- Visual type: **Clustered Bar Chart**
- Y-axis: `fact_claims[line_of_business]`
- X-axis: `[Loss Ratio]`
- Format X-axis as Percentage

### Visual 2: Reserve Adequacy Ratio — Gauge
- Visual type: **Gauge**
- Value: `[Reserve Adequacy Ratio]`
- Min: 0, Max: 2
- Target: 1.0
- Label: "Reserve Adequacy (>1 = OK)"

### Visual 3: New Biz vs Renewal Mix — Stacked Column
- Visual type: **Stacked Column Chart**
- X-axis: `dim_date[year]`
- Values: `[New Business Mix %]`, `[Renewal Mix %]`

### Visual 4: Underwriting Result Matrix
- Visual type: **Matrix**
- Rows: `fact_premiums[line_of_business]`
- Columns: `dim_date[year]`
- Values: `[GWP]`, `[Net Earned Premium]`, `[Total Incurred Losses]`, `[Combined Ratio]`
- Format Combined Ratio as Percentage, apply conditional formatting (red if > 1.0)

### Visual 5: YTD Combined Ratio Card
- Value: `[YTD Combined Ratio]`
- Format: Percentage

### Visual 6: Renewal Rate Trend — Line Chart
- Visual type: **Line Chart**
- X-axis: `dim_date[year]`
- Values: `[Renewal Rate %]`

### Visual 7: CR Variance vs Target — Card
- Value: `[CR Variance vs Target]`
- Format: Percentage
- Conditional formatting: red if positive, green if negative

---

## Page 4 — Geographic Risk Intelligence

**Rename page**: `Geographic Risk Intelligence`

Add slicers: `dim_date[year]` + `dim_geography[region]`

> **Before building map visuals**: File → Options → Security → check **Use Map and Filled Map visuals**. Restart Power BI Desktop if prompted.

### Visual 1: Loss Ratio by State — Filled Map (Choropleth)
- Visual type: **Filled Map**
- Location: `dim_geography[state_full]`
- Color saturation: `[Loss Ratio]`
- Tooltips: `[Loss Ratio]`, `[GWP]`, `[Total Incurred Losses]`
- Color scale: white (low) → red (high)

### Visual 2: State Risk Rank Table
- Visual type: **Table**
- Columns: `dim_geography[state]`, `[State Risk Rank]`, `[Loss Ratio]`, `[GWP]`, `[Total Incurred Losses]`
- Sort by `[State Risk Rank]` ascending
- Conditional formatting on Loss Ratio column (red scale)

### Visual 3: Top 5 States by Loss — Clustered Bar
- Visual type: **Clustered Bar Chart**
- Y-axis: `dim_geography[state]`
- X-axis: `[Total Incurred Losses]`
- Add a **Visual-level filter**: `[Is Top 5 State]` = TRUE

### Visual 4: % of Total Losses by Region — Treemap
- Visual type: **Treemap**
- Category: `dim_geography[region]`
- Values: `[Loss % of Grand Total]`

### Visual 5: GWP by CAT Zone — Bubble Map
- Visual type: **Map** (bubble map)
- Latitude: `dim_geography[latitude]`
- Longitude: `dim_geography[longitude]`
- Size: `[GWP]`
- Legend: `dim_geography[cat_zone]`
- Tooltips: `dim_geography[state_full]`, `[GWP]`, `[Loss Ratio]`

---

## Page 5 — Portfolio Profitability & Forecast

**Rename page**: `Portfolio Profitability & Forecast`

Add slicers: `dim_date[year]` + `fact_claims[line_of_business]`

### Visual 1: Rolling 12M Loss Ratio — Line Chart
- Visual type: **Line Chart**
- X-axis: `dim_date[date]` (Month granularity)
- Values: `[Rolling 12M Loss Ratio]`
- Format Y-axis as Percentage
- Add a constant line at 1.0 (Analytics pane → Constant line → 0.70 = target)

### Visual 2: Premium Trend Slope — Card
- Value: `[Premium Trend Slope]`
- Label: "Premium Trend Slope ($/month)"

### Visual 3: Customer LTV by Segment — Bar Chart
- Visual type: **Clustered Bar Chart**
- Y-axis: `dim_customer[customer_segment]`
- X-axis: `[Customer LTV]`

### Visual 4: Reserve Adequacy Over Time — Area Chart
- Visual type: **Area Chart**
- X-axis: `dim_date[date]` (Month granularity)
- Values: `[Reserve Adequacy Ratio]`
- Add Analytics constant line at 1.0

### Visual 5: Profitability Scatter — Scatter Plot
- Visual type: **Scatter Chart**
- X-axis: `[Loss Ratio]`
- Y-axis: `[GWP]`
- Legend: `fact_claims[line_of_business]`
- Size: `[Total Claim Count]`
- Each bubble = one LOB

### Visual 6: Total Reserve KPI Card
- Value: `[Total Reserve]`
- Label: "Reserve (Investment Float Proxy)"

---

# PHASE 5 — QA & DELIVERY

## Step 5.1 — Final Checklist

Work through each item. Do not mark done until visually confirmed.

### Python Pipeline
- [x] Script runs end-to-end with no errors
- [x] 6 CSVs present in `/data/clean/`
- [x] `fact_claims`: 10,000 rows (within 8K–12K target)
- [x] `fact_premiums`: 15,350 rows (within 10K–18K target)
- [x] `dim_date`: 2,192 rows
- [x] `dim_geography`: 50 rows
- [x] No null FK values
- [x] All 6 RI checks PASS

### Power BI File
- [ ] Custom theme applied — navy/blue palette visible
- [ ] 6 relationships set, all Single direction
- [ ] No bidirectional relationships
- [ ] All 25+ measures created in correct display folders
- [ ] Display folders: `_KPIs`, `Underwriting`, `Claims`, `Time Intelligence`, `Geography`, `Advanced`
- [ ] All 5 pages present with correct names
- [ ] Each page has header + KPI strip + footer
- [ ] Each page has at least 1 slicer
- [ ] Map visuals load without Bing error
- [ ] Spot-check Hard measures in both Card and Table context

## Step 5.2 — Save the PBIX

1. **File → Save As**
2. Navigate to `C:\Git\PBI\`
3. Filename: `ApexInsurance_Dashboard.pbix`
4. Click **Save**

## Step 5.3 — Generate the DAX Reference Sheet

The file `dax_measures_reference.md` needs to be created in `C:\Git\PBI\`.  
It should list every measure with: name, folder, complexity tier, description, full DAX code.  
Ask Claude Code to generate this file once all measures are confirmed working.

---

## COMMON ERRORS & FIXES

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| Relationship won't create — "many-to-many" warning | `date_key` column not Whole Number in both tables | Go back to Power Query, fix type, Close & Apply |
| Filled Map shows all one colour | `state_full` not set to "State or Province" data category | Data view → dim_geography → state_full → Column tools → Data category |
| `SAMEPERIODLASTYEAR` returns blank | No active relationship between fact table and dim_date | Check Model view — relationship must be Active |
| `Rolling 12M Loss Ratio` returns same value everywhere | dim_date relationship is bidirectional | Edit relationship → change to Single |
| Measure shows error in matrix but works in card | RANKX/TOPN need a filter context — expected | Put state or LOB field on rows first, then the measure |
| Map visual greyed out | Bing Maps not enabled | File → Options → Security → enable Map visuals → restart |
| Theme not applied after browsing | Clicked the main Themes button instead of dropdown arrow | View → Themes **dropdown arrow** → Browse for themes |
