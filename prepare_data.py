"""
Apex Insurance Group — P&C Executive Dashboard
Data Preparation Pipeline v1.0 | April 2026

Outputs 6 production-ready CSVs to /data/clean/:
  fact_claims.csv, fact_premiums.csv, dim_policy.csv,
  dim_customer.csv, dim_geography.csv, dim_date.csv

Run: python prepare_data.py
Gate: All referential integrity checks must PASS before opening Power BI.
"""

import io
import sys
import uuid
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure UTF-8 output on Windows (avoids cp1252 encode errors)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

# LOB proportions tuned so Auto achieves 40-50% of total GWP dollar volume.
# Commercial has very high avg GWP ($25K), so Auto needs ~78% of policy count.
LOB_LIST = ["Auto", "Homeowners", "Commercial", "Liability"]
CLAIM_TYPES = ["Collision", "Liability", "Property", "Theft", "Weather"]
CLAIM_STATUSES = ["Open", "Closed", "Reopened", "Denied"]
CHANNELS = ["Direct", "Agent", "Broker", "Digital"]
POLICY_TYPES = ["Personal", "Commercial"]
CUSTOMER_SEGMENTS = ["New", "Loyal", "At-Risk", "Lapsed"]
AGE_BANDS = ["18-25", "26-35", "36-45", "46-60", "60+"]
GENDERS = ["M", "F", "Unknown"]
CAT_STATES = {"FL", "TX", "LA", "CA"}  # High CAT probability states

LOB_GWP_RANGES = {
    "Auto":        (800,   3_200),
    "Homeowners":  (1_200, 4_800),
    "Commercial":  (5_000, 45_000),
    "Liability":   (2_500, 18_000),
}
LOB_EXPENSE_RATIOS = {
    "Auto": 0.27, "Homeowners": 0.29, "Commercial": 0.32, "Liability": 0.30
}
LOB_CESSION_RATES = {
    "Auto": 0.08, "Homeowners": 0.12, "Commercial": 0.18, "Liability": 0.15
}
# Target loss ratios by LOB (used in synthesis to hit 62-74% overall)
LOB_TARGET_LOSS_RATIOS = {
    "Auto": 0.68, "Homeowners": 0.65, "Commercial": 0.72, "Liability": 0.60
}

# ---------------------------------------------------------------------------
# GEOGRAPHY — All 50 US States
# ---------------------------------------------------------------------------
STATES_DATA = [
    ("AL", "Alabama",        "Southeast",  "Medium", 32.806671,  -86.791130),
    ("AK", "Alaska",         "West",       "Low",    61.370716, -152.404419),
    ("AZ", "Arizona",        "Southwest",  "Medium", 33.729759, -111.431221),
    ("AR", "Arkansas",       "Southeast",  "Medium", 34.969704,  -92.373123),
    ("CA", "California",     "West",       "High",   36.116203, -119.681564),
    ("CO", "Colorado",       "West",       "Low",    39.059811, -105.311104),
    ("CT", "Connecticut",    "Northeast",  "Low",    41.597782,  -72.755371),
    ("DE", "Delaware",       "Northeast",  "Low",    39.318523,  -75.507141),
    ("FL", "Florida",        "Southeast",  "High",   27.766279,  -81.686783),
    ("GA", "Georgia",        "Southeast",  "Medium", 33.040619,  -83.643074),
    ("HI", "Hawaii",         "West",       "Medium", 21.094318, -157.498337),
    ("ID", "Idaho",          "West",       "Low",    44.240459, -114.478828),
    ("IL", "Illinois",       "Midwest",    "Low",    40.349457,  -88.986137),
    ("IN", "Indiana",        "Midwest",    "Low",    39.849426,  -86.258278),
    ("IA", "Iowa",           "Midwest",    "Low",    42.011539,  -93.210526),
    ("KS", "Kansas",         "Midwest",    "Medium", 38.526600,  -96.726486),
    ("KY", "Kentucky",       "Southeast",  "Low",    37.668140,  -84.670067),
    ("LA", "Louisiana",      "Southeast",  "High",   31.169960,  -91.867805),
    ("ME", "Maine",          "Northeast",  "Low",    44.693947,  -69.381927),
    ("MD", "Maryland",       "Northeast",  "Low",    39.063946,  -76.802101),
    ("MA", "Massachusetts",  "Northeast",  "Low",    42.230171,  -71.530106),
    ("MI", "Michigan",       "Midwest",    "Low",    43.326618,  -84.536095),
    ("MN", "Minnesota",      "Midwest",    "Low",    45.694454,  -93.900192),
    ("MS", "Mississippi",    "Southeast",  "High",   32.741646,  -89.678696),
    ("MO", "Missouri",       "Midwest",    "Medium", 38.456085,  -92.288368),
    ("MT", "Montana",        "West",       "Low",    46.921925, -110.454353),
    ("NE", "Nebraska",       "Midwest",    "Medium", 41.125370,  -98.268082),
    ("NV", "Nevada",         "West",       "Low",    38.313515, -117.055374),
    ("NH", "New Hampshire",  "Northeast",  "Low",    43.452492,  -71.563896),
    ("NJ", "New Jersey",     "Northeast",  "Low",    40.298904,  -74.521011),
    ("NM", "New Mexico",     "Southwest",  "Medium", 34.840515, -106.248482),
    ("NY", "New York",       "Northeast",  "Low",    42.165726,  -74.948051),
    ("NC", "North Carolina", "Southeast",  "Medium", 35.630066,  -79.806419),
    ("ND", "North Dakota",   "Midwest",    "Low",    47.528912,  -99.784012),
    ("OH", "Ohio",           "Midwest",    "Low",    40.388783,  -82.764915),
    ("OK", "Oklahoma",       "Southwest",  "High",   35.565342,  -96.928917),
    ("OR", "Oregon",         "West",       "Low",    44.572021, -122.070938),
    ("PA", "Pennsylvania",   "Northeast",  "Low",    40.590752,  -77.209755),
    ("RI", "Rhode Island",   "Northeast",  "Low",    41.680893,  -71.511780),
    ("SC", "South Carolina", "Southeast",  "Medium", 33.856892,  -80.945007),
    ("SD", "South Dakota",   "Midwest",    "Low",    44.299782,  -99.438828),
    ("TN", "Tennessee",      "Southeast",  "Medium", 35.747845,  -86.692345),
    ("TX", "Texas",          "Southwest",  "High",   31.054487,  -97.563461),
    ("UT", "Utah",           "West",       "Low",    40.150032, -111.862434),
    ("VT", "Vermont",        "Northeast",  "Low",    44.045876,  -72.710686),
    ("VA", "Virginia",       "Southeast",  "Low",    37.769337,  -78.169968),
    ("WA", "Washington",     "West",       "Medium", 47.400902, -121.490494),
    ("WV", "West Virginia",  "Southeast",  "Low",    38.491226,  -80.954453),
    ("WI", "Wisconsin",      "Midwest",    "Low",    44.268543,  -89.616508),
    ("WY", "Wyoming",        "West",       "Low",    42.755966, -107.302490),
]
STATE_ABBR_TO_GEO_ID = {s[0]: f"GEO-{s[0]}" for s in STATES_DATA}
STATE_ABBRS = [s[0] for s in STATES_DATA]

# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def make_uuid() -> str:
    return str(uuid.uuid4())


def print_banner(title: str) -> None:
    width = 62
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def audit_df(name: str, df: pd.DataFrame) -> None:
    """Print audit info: shape, dtypes, null counts."""
    print(f"\n--- {name} ---")
    print(f"  Shape     : {df.shape[0]:,} rows x {df.shape[1]} cols")
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if null_cols.empty:
        print(f"  Nulls     : none")
    else:
        for col, cnt in null_cols.items():
            print(f"  Null [{col}]: {cnt:,}")
    print(f"  Columns   : {list(df.columns)}")


def assert_no_nulls_in_fk(df: pd.DataFrame, fk_cols: list[str], table_name: str) -> None:
    for col in fk_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            raise ValueError(
                f"FATAL: {table_name}.{col} has {null_count} null FK values. "
                f"Repair data before continuing."
            )


# ---------------------------------------------------------------------------
# STEP 1 — LOAD & AUDIT SOURCE FILES
# ---------------------------------------------------------------------------

def load_raw_sources() -> dict[str, pd.DataFrame | None]:
    """
    Attempt to load the 3 Kaggle source CSVs.
    Returns dict with keys: 'claims', 'policy', 'premiums'
    Values are DataFrames or None if file not found.
    """
    print_banner("STEP 1 — LOAD & AUDIT SOURCE FILES")

    file_map = {
        "claims":   RAW_DIR / "auto_insurance_claims.csv",
        "policy":   RAW_DIR / "insurance_claims_policy.csv",
        "premiums": RAW_DIR / "ny_pc_premiums.csv",
    }

    sources: dict[str, pd.DataFrame | None] = {}
    for key, path in file_map.items():
        if path.exists():
            df = pd.read_csv(path, low_memory=False)
            audit_df(f"SOURCE: {path.name}", df)
            sources[key] = df
        else:
            print(f"\n  [WARNING] {path.name} not found in {RAW_DIR}")
            print(f"           Falling back to synthetic generation for '{key}'.")
            sources[key] = None

    any_loaded = any(v is not None for v in sources.values())
    if not any_loaded:
        print("\n  [INFO] No raw source files found. Running in full synthetic mode.")
    return sources


# ---------------------------------------------------------------------------
# STEP 4A — BUILD dim_date (done early, needed by other steps)
# ---------------------------------------------------------------------------

def build_dim_date() -> pd.DataFrame:
    print_banner("STEP 4A — BUILD dim_date")
    dates = pd.date_range("2020-01-01", "2025-12-31", freq="D")
    df = pd.DataFrame({"date": dates})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["quarter_label"] = "Q" + df["quarter"].astype(str) + " " + df["year"].astype(str)
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["month_short"] = df["date"].dt.strftime("%b")
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.strftime("%A")
    df["is_weekday"] = df["date"].dt.dayofweek < 5
    df["fiscal_year"] = df["year"]  # Jan-Dec fiscal
    df["fiscal_quarter"] = "FY" + df["year"].astype(str) + "-Q" + df["quarter"].astype(str)
    # Reorder columns
    df = df[[
        "date_key", "date", "year", "quarter", "quarter_label",
        "month", "month_name", "month_short", "week", "day_of_week",
        "is_weekday", "fiscal_year", "fiscal_quarter"
    ]]
    assert len(df) == 2192, f"dim_date should have 2192 rows, got {len(df)}"
    print(f"  dim_date: {len(df):,} rows (2020-01-01 to 2025-12-31) [OK]")
    return df


# ---------------------------------------------------------------------------
# STEP 4B — BUILD dim_geography
# ---------------------------------------------------------------------------

def build_dim_geography() -> pd.DataFrame:
    print_banner("STEP 4B — BUILD dim_geography")
    records = []
    for abbr, full, region, cat_zone, lat, lon in STATES_DATA:
        records.append({
            "geography_id": f"GEO-{abbr}",
            "state": abbr,
            "state_full": full,
            "region": region,
            "cat_zone": cat_zone,
            "latitude": lat,
            "longitude": lon,
        })
    df = pd.DataFrame(records)
    assert len(df) == 50, f"dim_geography should have 50 rows, got {len(df)}"
    print(f"  dim_geography: {len(df)} states [OK]")
    return df


# ---------------------------------------------------------------------------
# STEP 4C — BUILD dim_policy (synthetic or from source)
# ---------------------------------------------------------------------------

def build_dim_policy(source_policy: pd.DataFrame | None, n_policies: int = 3000) -> pd.DataFrame:
    print_banner("STEP 4C — BUILD dim_policy")

    if source_policy is not None:
        # Attempt to map from source
        df = _map_dim_policy_from_source(source_policy)
        if df is not None and len(df) > 100:
            print(f"  dim_policy: {len(df):,} rows (from source)")
            return df
        print("  Insufficient mappable columns in source; using synthetic generation.")

    return _synthesize_dim_policy(n_policies)


def _map_dim_policy_from_source(src: pd.DataFrame) -> pd.DataFrame | None:
    """Best-effort mapping from Kaggle policy CSV columns."""
    src_cols_lower = {c.lower(): c for c in src.columns}

    # Try to find a policy ID column
    policy_id_col = next(
        (src_cols_lower[k] for k in src_cols_lower if "policy" in k and "id" in k), None
    )
    if policy_id_col is None:
        return None

    df = pd.DataFrame()
    df["policy_id"] = src[policy_id_col].astype(str).str.strip()
    df = df.drop_duplicates(subset="policy_id")

    # Map LOB
    lob_col = next(
        (src_cols_lower[k] for k in src_cols_lower
         if any(x in k for x in ["lob", "line_of_business", "line"])), None
    )
    if lob_col:
        df["line_of_business"] = src.loc[
            src[policy_id_col].astype(str).str.strip().isin(df["policy_id"]), lob_col
        ].values[:len(df)]
        df["line_of_business"] = df["line_of_business"].fillna("Auto")
        df["line_of_business"] = df["line_of_business"].apply(
            lambda x: x if x in LOB_LIST else rng.choice(LOB_LIST)
        )
    else:
        df["line_of_business"] = rng.choice(LOB_LIST, size=len(df),
                                             p=[0.78, 0.10, 0.05, 0.07])

    df["policy_type"] = np.where(
        df["line_of_business"].isin(["Auto", "Homeowners"]), "Personal", "Commercial"
    )

    # Dates
    start_years = rng.integers(2018, 2025, size=len(df))
    start_days = rng.integers(0, 365, size=len(df))
    df["policy_start_date"] = pd.to_datetime(
        [f"{y}-01-01" for y in start_years]
    ) + pd.to_timedelta(start_days, unit="D")
    df["policy_end_date"] = df["policy_start_date"] + pd.DateOffset(years=1)

    df["agent_id"] = ["AGT-" + str(rng.integers(1000, 9999)) for _ in range(len(df))]
    df["channel"] = rng.choice(CHANNELS, size=len(df), p=[0.20, 0.40, 0.25, 0.15])
    # premium_tier placeholder — set after GWP is known
    df["premium_tier"] = "Mid"  # will be recalculated later

    return df


def _synthesize_dim_policy(n: int) -> pd.DataFrame:
    """Generate n fully synthetic policies."""
    policy_ids = [f"POL-{str(uuid.uuid4())[:8].upper()}" for _ in range(n)]
    lob = rng.choice(LOB_LIST, size=n, p=[0.78, 0.10, 0.05, 0.07])

    # Policies start in 2015-2021 so the majority are active throughout 2020-2025.
    # Duration: 5-10 years (auto-renewing portfolio), which means most of
    # the 2020-2025 premium rows for a given policy are renewals (target 82-88%).
    start_years = rng.choice(
        list(range(2015, 2022)),
        size=n,
        p=[0.10, 0.15, 0.18, 0.20, 0.17, 0.12, 0.08]
    )
    start_days = rng.integers(0, 365, size=n)
    start_dates = pd.to_datetime(
        [f"{y}-01-01" for y in start_years]
    ) + pd.to_timedelta(start_days, unit="D")
    # Policy duration 5-10 years so each policy covers most of the 2020-2025 window
    duration_years = rng.integers(5, 11, size=n)
    end_dates = start_dates + pd.to_timedelta(duration_years * 365, unit="D")

    gwp = np.array([
        rng.uniform(*LOB_GWP_RANGES[l]) for l in lob
    ])

    df = pd.DataFrame({
        "policy_id": policy_ids,
        "policy_type": np.where(np.isin(lob, ["Auto", "Homeowners"]), "Personal", "Commercial"),
        "line_of_business": lob,
        "policy_start_date": start_dates.date,
        "policy_end_date": end_dates.date,
        "agent_id": [f"AGT-{rng.integers(1000, 9999)}" for _ in range(n)],
        "channel": rng.choice(CHANNELS, size=n, p=[0.20, 0.40, 0.25, 0.15]),
    })

    # premium_tier based on GWP quintile (3 buckets)
    df["premium_tier"] = pd.qcut(gwp, q=3, labels=["Low", "Mid", "High"])
    print(f"  dim_policy: {len(df):,} rows (synthetic)")
    return df


# ---------------------------------------------------------------------------
# STEP 4D — BUILD dim_customer (synthetic or from source)
# ---------------------------------------------------------------------------

def build_dim_customer(source_policy: pd.DataFrame | None, n_customers: int = 2500) -> pd.DataFrame:
    print_banner("STEP 4D — BUILD dim_customer")

    if source_policy is not None:
        df = _map_dim_customer_from_source(source_policy)
        if df is not None and len(df) > 100:
            print(f"  dim_customer: {len(df):,} rows (from source)")
            return df

    return _synthesize_dim_customer(n_customers)


def _map_dim_customer_from_source(src: pd.DataFrame) -> pd.DataFrame | None:
    src_cols_lower = {c.lower(): c for c in src.columns}
    cust_col = next(
        (src_cols_lower[k] for k in src_cols_lower
         if "customer" in k and "id" in k), None
    )
    if cust_col is None:
        return None

    df = pd.DataFrame()
    df["customer_id"] = src[cust_col].astype(str).str.strip()
    df = df.drop_duplicates(subset="customer_id")
    n = len(df)

    # Try to map age
    age_col = next((src_cols_lower[k] for k in src_cols_lower if "age" in k), None)
    if age_col:
        ages = src[cust_col].astype(str).str.strip().map(
            dict(zip(src[cust_col].astype(str).str.strip(), src[age_col]))
        )
        ages = pd.to_numeric(ages, errors="coerce")
        df["age_band"] = pd.cut(
            ages.reindex(df["customer_id"]).values,
            bins=[17, 25, 35, 45, 60, 120],
            labels=AGE_BANDS
        ).astype(str).replace("nan", "36-45")
    else:
        df["age_band"] = rng.choice(AGE_BANDS, size=n, p=[0.10, 0.20, 0.30, 0.25, 0.15])

    gender_col = next(
        (src_cols_lower[k] for k in src_cols_lower if "gender" in k or "sex" in k), None
    )
    if gender_col:
        gender_map = dict(zip(
            src[cust_col].astype(str).str.strip(), src[gender_col].astype(str)
        ))
        df["gender"] = df["customer_id"].map(gender_map).fillna("Unknown")
        df["gender"] = df["gender"].apply(lambda x: x if x in GENDERS else "Unknown")
    else:
        df["gender"] = rng.choice(GENDERS, size=n, p=[0.47, 0.47, 0.06])

    df["customer_segment"] = rng.choice(
        CUSTOMER_SEGMENTS, size=n, p=[0.15, 0.55, 0.20, 0.10]
    )
    df["tenure_years"] = rng.integers(1, 16, size=n)

    # CLV score: tenure * avg_premium * (1 - avg_loss_ratio); normalize 0-1000
    avg_prem = rng.uniform(1000, 8000, size=n)
    avg_lr = rng.uniform(0.55, 0.80, size=n)
    raw_clv = df["tenure_years"] * avg_prem * (1 - avg_lr)
    clv_min, clv_max = raw_clv.min(), raw_clv.max()
    df["clv_score"] = ((raw_clv - clv_min) / (clv_max - clv_min) * 1000).round(2)

    # Risk score: normalize claim frequency proxy to 1-100
    claim_freq = rng.uniform(0, 3, size=n)
    avg_loss = rng.uniform(2000, 50000, size=n)
    raw_risk = claim_freq * avg_loss
    r_min, r_max = raw_risk.min(), raw_risk.max()
    df["risk_score"] = ((raw_risk - r_min) / (r_max - r_min) * 99 + 1).round().astype(int)

    return df


def _synthesize_dim_customer(n: int) -> pd.DataFrame:
    cust_ids = [f"CUST-{str(uuid.uuid4())[:8].upper()}" for _ in range(n)]
    tenure = rng.integers(1, 16, size=n)

    avg_prem = rng.uniform(1000, 8000, size=n)
    avg_lr = rng.uniform(0.55, 0.80, size=n)
    raw_clv = tenure * avg_prem * (1 - avg_lr)
    clv_min, clv_max = raw_clv.min(), raw_clv.max()
    clv_score = ((raw_clv - clv_min) / (clv_max - clv_min) * 1000).round(2)

    claim_freq = rng.uniform(0, 3, size=n)
    avg_loss = rng.uniform(2000, 50000, size=n)
    raw_risk = claim_freq * avg_loss
    r_min, r_max = raw_risk.min(), raw_risk.max()
    risk_score = ((raw_risk - r_min) / (r_max - r_min) * 99 + 1).round().astype(int)

    df = pd.DataFrame({
        "customer_id": cust_ids,
        "age_band": rng.choice(AGE_BANDS, size=n, p=[0.10, 0.20, 0.30, 0.25, 0.15]),
        "gender": rng.choice(GENDERS, size=n, p=[0.47, 0.47, 0.06]),
        "customer_segment": rng.choice(
            CUSTOMER_SEGMENTS, size=n, p=[0.15, 0.55, 0.20, 0.10]
        ),
        "tenure_years": tenure,
        "clv_score": clv_score,
        "risk_score": risk_score,
    })
    print(f"  dim_customer: {len(df):,} rows (synthetic)")
    return df


# ---------------------------------------------------------------------------
# STEP 2 — BUILD fact_claims
# ---------------------------------------------------------------------------

def build_fact_claims(
    source_claims: pd.DataFrame | None,
    dim_policy: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_geography: pd.DataFrame,
    target_n: int = 10_000,
) -> pd.DataFrame:
    print_banner("STEP 2 — BUILD fact_claims")

    policy_ids = dim_policy["policy_id"].values
    customer_ids = dim_customer["customer_id"].values
    date_keys = dim_date["date_key"].values
    geo_ids = dim_geography["geography_id"].values
    geo_states = dict(zip(dim_geography["geography_id"], dim_geography["state"]))

    if source_claims is not None:
        df = _map_fact_claims_from_source(
            source_claims, policy_ids, customer_ids, date_keys, geo_ids
        )
        if df is not None and len(df) >= 5000:
            # Pad if under target
            if len(df) < target_n:
                extra = _synthesize_fact_claims(
                    target_n - len(df), policy_ids, customer_ids, date_keys, geo_ids
                )
                df = pd.concat([df, extra], ignore_index=True)
            else:
                df = df.sample(min(target_n, len(df)), random_state=RANDOM_SEED).reset_index(drop=True)
        else:
            print("  Could not map source claims; using synthetic generation.")
            df = _synthesize_fact_claims(target_n, policy_ids, customer_ids, date_keys, geo_ids)
    else:
        df = _synthesize_fact_claims(target_n, policy_ids, customer_ids, date_keys, geo_ids)

    # Derive reserved_loss = max(incurred - paid, 0)
    df["reserved_loss"] = (df["incurred_loss"] - df["paid_loss"]).clip(lower=0).round(2)

    # days_to_close
    df["claim_open_date"] = pd.to_datetime(df["claim_open_date"])
    df["claim_close_date"] = pd.to_datetime(df["claim_close_date"])
    df["days_to_close"] = (df["claim_close_date"] - df["claim_open_date"]).dt.days

    # Synthesize fraud_flag
    fraud_random = rng.random(len(df)) < 0.05
    fraud_rule = (df["incurred_loss"] > 80_000) & (df["days_to_close"].fillna(999) < 7)
    df["fraud_flag"] = (fraud_random | fraud_rule).astype(bool)

    # Synthesize catastrophe_flag
    # Map geography_id → state
    df["_state"] = df["geography_id"].map(geo_states)
    weather_mask = df["claim_type"] == "Weather"
    cat_state_mask = df["_state"].isin(CAT_STATES)
    cat_prob = np.where(weather_mask & cat_state_mask, 0.60,
               np.where(weather_mask, 0.15, 0.0))
    df["catastrophe_flag"] = (rng.random(len(df)) < cat_prob).astype(bool)
    df.drop(columns=["_state"], inplace=True)

    # Map policy LOB to fact LOB
    policy_lob = dict(zip(dim_policy["policy_id"], dim_policy["line_of_business"]))
    if "line_of_business" not in df.columns or df["line_of_business"].isnull().all():
        df["line_of_business"] = df["policy_id"].map(policy_lob).fillna("Auto")

    # Ensure unique claim_ids
    df["claim_id"] = [f"CLM-{str(uuid.uuid4())[:8].upper()}" for _ in range(len(df))]

    # Reorder columns
    df = df[[
        "claim_id", "policy_id", "customer_id", "date_key", "geography_id",
        "claim_status", "claim_type", "incurred_loss", "paid_loss", "reserved_loss",
        "claim_open_date", "claim_close_date", "days_to_close",
        "fraud_flag", "line_of_business", "catastrophe_flag"
    ]]

    assert 8_000 <= len(df) <= 12_000, \
        f"fact_claims target 8K-12K rows, got {len(df)}. Adjust target_n."

    print(f"  fact_claims: {len(df):,} rows")
    print(f"    Fraud rate       : {df['fraud_flag'].mean():.1%}")
    print(f"    CAT flag rate    : {df['catastrophe_flag'].mean():.1%}")
    print(f"    Open claims      : {(df['claim_status']=='Open').sum():,}")
    return df


def _map_fact_claims_from_source(
    src: pd.DataFrame,
    policy_ids, customer_ids, date_keys, geo_ids
) -> pd.DataFrame | None:
    """Best-effort mapping from Kaggle auto insurance claims CSV."""
    src_cols_lower = {c.lower().replace(" ", "_"): c for c in src.columns}

    # We need at least a loss amount column
    loss_col = next(
        (src_cols_lower[k] for k in src_cols_lower
         if any(x in k for x in ["loss", "claim_amount", "total_claim"])), None
    )
    if loss_col is None:
        return None

    df = pd.DataFrame()
    n = len(src)

    # Assign FK values (sample from our dimension tables)
    df["policy_id"] = rng.choice(policy_ids, size=n, replace=True)
    df["customer_id"] = rng.choice(customer_ids, size=n, replace=True)
    df["date_key"] = rng.choice(date_keys, size=n, replace=True)
    df["geography_id"] = rng.choice(geo_ids, size=n, replace=True)

    # Claim status
    status_col = next(
        (src_cols_lower[k] for k in src_cols_lower if "status" in k), None
    )
    if status_col:
        df["claim_status"] = src[status_col].fillna("Open").astype(str)
        df["claim_status"] = df["claim_status"].apply(
            lambda x: x if x in CLAIM_STATUSES else rng.choice(
                CLAIM_STATUSES, p=[0.20, 0.65, 0.08, 0.07]
            )
        )
    else:
        df["claim_status"] = rng.choice(
            CLAIM_STATUSES, size=n, p=[0.20, 0.65, 0.08, 0.07]
        )

    # Claim type
    type_col = next(
        (src_cols_lower[k] for k in src_cols_lower
         if any(x in k for x in ["type", "incident_type", "claim_type"])), None
    )
    if type_col:
        df["claim_type"] = src[type_col].fillna("Property").astype(str).apply(
            lambda x: x if x in CLAIM_TYPES else rng.choice(CLAIM_TYPES)
        )
    else:
        df["claim_type"] = rng.choice(
            CLAIM_TYPES, size=n, p=[0.30, 0.25, 0.20, 0.10, 0.15]
        )

    # Loss amounts
    incurred = pd.to_numeric(src[loss_col], errors="coerce")
    incurred = incurred.fillna(incurred.median())
    df["incurred_loss"] = incurred.values.round(2)
    df["paid_loss"] = (df["incurred_loss"] * rng.uniform(0.60, 0.95, size=n)).round(2)

    # Dates
    date_keys_series = pd.Series(df["date_key"].values)
    open_dates = pd.to_datetime(date_keys_series.astype(str), format="%Y%m%d")
    df["claim_open_date"] = open_dates.dt.date

    closed_mask = df["claim_status"].isin(["Closed", "Denied"])
    close_offsets = rng.integers(10, 400, size=n)
    close_dates = open_dates + pd.to_timedelta(close_offsets, unit="D")
    df["claim_close_date"] = np.where(closed_mask, close_dates.dt.date, None)

    lob_col = next(
        (src_cols_lower[k] for k in src_cols_lower
         if any(x in k for x in ["lob", "line_of_business", "policy_type"])), None
    )
    if lob_col:
        df["line_of_business"] = src[lob_col].fillna("Auto").apply(
            lambda x: x if x in LOB_LIST else rng.choice(LOB_LIST)
        )
    else:
        df["line_of_business"] = rng.choice(LOB_LIST, size=n)

    return df


def _synthesize_fact_claims(n: int, policy_ids, customer_ids, date_keys, geo_ids) -> pd.DataFrame:
    """Fully synthesize n claim records."""
    # Sample open dates (as date_keys), then derive open_date
    sampled_dk = rng.choice(date_keys, size=n, replace=True)
    open_dates = pd.to_datetime(pd.Series(sampled_dk).astype(str), format="%Y%m%d")

    claim_status = rng.choice(CLAIM_STATUSES, size=n, p=[0.20, 0.65, 0.08, 0.07])
    closed_mask = np.isin(claim_status, ["Closed", "Denied"])
    close_offsets = rng.integers(10, 400, size=n)
    close_dates = open_dates + pd.to_timedelta(close_offsets, unit="D")

    # Synthesize loss amounts: targeting 62-74% loss ratio
    lob_assigned = rng.choice(LOB_LIST, size=n, p=[0.78, 0.10, 0.05, 0.07])
    incurred = np.zeros(n)
    for lob in LOB_LIST:
        mask = lob_assigned == lob
        lo, hi = LOB_GWP_RANGES[lob]
        target_lr = LOB_TARGET_LOSS_RATIOS[lob]
        # Loss ≈ premium × loss_ratio; vary around target
        avg_prem = (lo + hi) / 2
        base_loss = avg_prem * target_lr
        incurred[mask] = rng.gamma(
            shape=2.0,
            scale=base_loss / 2.0,
            size=mask.sum()
        ).clip(min=100)

    paid = (incurred * rng.uniform(0.60, 0.95, size=n)).round(2)

    close_date_col = np.where(
        closed_mask,
        close_dates.dt.strftime("%Y-%m-%d"),
        None
    )

    df = pd.DataFrame({
        "policy_id": rng.choice(policy_ids, size=n, replace=True),
        "customer_id": rng.choice(customer_ids, size=n, replace=True),
        "date_key": sampled_dk,
        "geography_id": rng.choice(geo_ids, size=n, replace=True),
        "claim_status": claim_status,
        "claim_type": rng.choice(CLAIM_TYPES, size=n, p=[0.30, 0.25, 0.20, 0.10, 0.15]),
        "incurred_loss": incurred.round(2),
        "paid_loss": paid,
        "claim_open_date": open_dates.dt.strftime("%Y-%m-%d"),
        "claim_close_date": close_date_col,
        "line_of_business": lob_assigned,
    })
    return df


# ---------------------------------------------------------------------------
# STEP 3 — BUILD fact_premiums
# ---------------------------------------------------------------------------

def build_fact_premiums(
    source_premiums: pd.DataFrame | None,
    dim_policy: pd.DataFrame,
    dim_date: pd.DataFrame,
    target_n: int = 14_000,
) -> pd.DataFrame:
    print_banner("STEP 3 — BUILD fact_premiums")

    policy_ids = dim_policy["policy_id"].values
    date_keys = dim_date["date_key"].values
    policy_lob = dict(zip(dim_policy["policy_id"], dim_policy["line_of_business"]))
    policy_start = dict(zip(
        dim_policy["policy_id"],
        pd.to_datetime(dim_policy["policy_start_date"])
    ))
    policy_end = dict(zip(
        dim_policy["policy_id"],
        pd.to_datetime(dim_policy["policy_end_date"])
    ))

    # Generate one row per policy per active year (2020-2025)
    years = list(range(2020, 2026))
    records = []
    for pol_id in policy_ids:
        lob = policy_lob.get(pol_id, "Auto")
        start = policy_start.get(pol_id, pd.Timestamp("2020-01-01"))
        end = policy_end.get(pol_id, pd.Timestamp("2025-12-31"))

        for year in years:
            yr_start = pd.Timestamp(f"{year}-01-01")
            yr_end = pd.Timestamp(f"{year}-12-31")

            # Compute days active in this year
            overlap_start = max(start, yr_start)
            overlap_end = min(end, yr_end)
            if overlap_start > overlap_end:
                continue
            days_active = (overlap_end - overlap_start).days + 1
            earning_factor = min(days_active / 365, 1.0)

            # GWP
            lo, hi = LOB_GWP_RANGES[lob]
            gwp = rng.uniform(lo, hi)

            exp_ratio = LOB_EXPENSE_RATIOS[lob]
            cess_rate = LOB_CESSION_RATES[lob]

            ceded = gwp * cess_rate
            expense = gwp * exp_ratio
            nep = (gwp - ceded) * earning_factor

            # date_key: use Jan 1 of the policy year
            dk_str = f"{year}0101"
            date_key_val = int(dk_str)

            records.append({
                "premium_id": f"PRM-{str(uuid.uuid4())[:8].upper()}",
                "policy_id": pol_id,
                "date_key": date_key_val,
                "gross_written_premium": round(gwp, 2),
                "net_earned_premium": round(nep, 2),
                "ceded_premium": round(ceded, 2),
                "expense_amount": round(expense, 2),
                "line_of_business": lob,
                "renewal_flag": year > start.year,  # True if not inception year
            })

    df = pd.DataFrame(records)

    # Validate date_key is in dim_date
    valid_dks = set(dim_date["date_key"].values)
    df = df[df["date_key"].isin(valid_dks)].reset_index(drop=True)

    # Adjust to target row count if needed
    if len(df) < target_n:
        # Duplicate with new premium IDs to hit target
        extra_needed = target_n - len(df)
        extra = df.sample(extra_needed, replace=True, random_state=RANDOM_SEED).copy()
        extra["premium_id"] = [f"PRM-{str(uuid.uuid4())[:8].upper()}" for _ in range(len(extra))]
        df = pd.concat([df, extra], ignore_index=True)
    elif len(df) > 18_000:
        df = df.sample(min(len(df), 18_000), random_state=RANDOM_SEED).reset_index(drop=True)

    assert 10_000 <= len(df) <= 18_000, \
        f"fact_premiums target 10K-18K rows, got {len(df)}"

    # Compute quality metrics
    total_gwp = df["gross_written_premium"].sum()
    auto_gwp = df[df["line_of_business"] == "Auto"]["gross_written_premium"].sum()
    auto_share = auto_gwp / total_gwp if total_gwp > 0 else 0
    renewal_rate = df["renewal_flag"].mean()

    print(f"  fact_premiums: {len(df):,} rows")
    print(f"    Auto LOB GWP share : {auto_share:.1%} (target 40-50%)")
    print(f"    Renewal rate       : {renewal_rate:.1%} (target 82-88%)")
    return df


# ---------------------------------------------------------------------------
# STEP 5 — REFERENTIAL INTEGRITY CHECK
# ---------------------------------------------------------------------------

def referential_integrity_check(
    fact_claims: pd.DataFrame,
    fact_premiums: pd.DataFrame,
    dim_policy: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_geography: pd.DataFrame,
    dim_date: pd.DataFrame,
) -> bool:
    print_banner("STEP 5 — REFERENTIAL INTEGRITY CHECK")

    checks = [
        ("fact_claims",   "policy_id",     fact_claims["policy_id"],     dim_policy["policy_id"]),
        ("fact_claims",   "customer_id",   fact_claims["customer_id"],   dim_customer["customer_id"]),
        ("fact_claims",   "date_key",      fact_claims["date_key"],      dim_date["date_key"]),
        ("fact_claims",   "geography_id",  fact_claims["geography_id"],  dim_geography["geography_id"]),
        ("fact_premiums", "policy_id",     fact_premiums["policy_id"],   dim_policy["policy_id"]),
        ("fact_premiums", "date_key",      fact_premiums["date_key"],    dim_date["date_key"]),
    ]

    col_widths = (14, 19, 10, 6)
    header = (
        f"{'Fact Table':<{col_widths[0]}} "
        f"{'FK Column':<{col_widths[1]}} "
        f"{'Orphans':>{col_widths[2]}} "
        f"{'Status':>{col_widths[3]}}"
    )
    sep = "-" * (sum(col_widths) + 3)

    print(f"\n  {sep}")
    print(f"  {header}")
    print(f"  {sep}")

    all_passed = True
    for fact_table, fk_col, fact_vals, dim_vals in checks:
        dim_set = set(dim_vals.astype(str))
        orphans = (~fact_vals.astype(str).isin(dim_set)).sum()
        status = "PASS" if orphans == 0 else "FAIL"
        if orphans > 0:
            all_passed = False
        print(
            f"  {fact_table:<{col_widths[0]}} "
            f"{fk_col:<{col_widths[1]}} "
            f"{orphans:>{col_widths[2]},} "
            f"{status:>{col_widths[3]}}"
        )

    print(f"  {sep}")

    if all_passed:
        print("\n  ALL REFERENTIAL INTEGRITY CHECKS PASSED.")
        print("  Safe to open Power BI and import /data/clean/ CSVs.\n")
    else:
        print("\n  ONE OR MORE CHECKS FAILED. Do NOT open Power BI.")
        print("  Investigate orphan FK values before proceeding.\n")

    return all_passed


# ---------------------------------------------------------------------------
# STEP 6 — WRITE OUTPUTS
# ---------------------------------------------------------------------------

def write_outputs(
    fact_claims: pd.DataFrame,
    fact_premiums: pd.DataFrame,
    dim_policy: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_geography: pd.DataFrame,
    dim_date: pd.DataFrame,
) -> None:
    print_banner("STEP 6 — WRITE OUTPUTS TO /data/clean/")

    tables = {
        "fact_claims.csv":    fact_claims,
        "fact_premiums.csv":  fact_premiums,
        "dim_policy.csv":     dim_policy,
        "dim_customer.csv":   dim_customer,
        "dim_geography.csv":  dim_geography,
        "dim_date.csv":       dim_date,
    }

    for filename, df in tables.items():
        out_path = CLEAN_DIR / filename
        df.to_csv(out_path, index=False, encoding="utf-8")
        print(f"  Written: {out_path.name:30s} ({len(df):,} rows)")

    print(f"\n  Output directory: {CLEAN_DIR}")


# ---------------------------------------------------------------------------
# FINAL ROW COUNT SUMMARY
# ---------------------------------------------------------------------------

def print_summary(
    fact_claims, fact_premiums, dim_policy, dim_customer, dim_geography, dim_date
) -> None:
    print_banner("FINAL ROW COUNT SUMMARY")
    rows = [
        ("fact_claims",   len(fact_claims),   "8,000 – 12,000"),
        ("fact_premiums", len(fact_premiums),  "10,000 – 18,000"),
        ("dim_policy",    len(dim_policy),     "—"),
        ("dim_customer",  len(dim_customer),   "—"),
        ("dim_geography", len(dim_geography),  "50"),
        ("dim_date",      len(dim_date),       "2,192"),
    ]
    print(f"\n  {'Table':<20} {'Rows':>8}   {'Target':>15}")
    print(f"  {'-'*50}")
    for name, n, target in rows:
        print(f"  {name:<20} {n:>8,}   {target:>15}")
    print()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print_banner("APEX INSURANCE GROUP — DATA PREPARATION PIPELINE v1.0")
    print(f"  Input : {RAW_DIR}")
    print(f"  Output: {CLEAN_DIR}")

    # Step 1: Load & audit sources
    sources = load_raw_sources()

    # Step 4A & 4B: Build date and geography dimensions first (no source dependencies)
    dim_date = build_dim_date()
    dim_geography = build_dim_geography()

    # Step 4C & 4D: Policy and customer dims (use source policy CSV if available)
    dim_policy = build_dim_policy(sources.get("policy"))
    dim_customer = build_dim_customer(sources.get("policy"))

    # Recalculate premium_tier now that we have consistent policy data
    # (qcut on a proxy GWP per LOB)
    def assign_premium_tier(lob):
        lo, hi = LOB_GWP_RANGES.get(lob, (1000, 5000))
        return rng.uniform(lo, hi)

    proxy_gwp = dim_policy["line_of_business"].apply(assign_premium_tier)
    dim_policy["premium_tier"] = pd.qcut(
        proxy_gwp, q=3, labels=["Low", "Mid", "High"]
    ).astype(str)

    # Step 2: fact_claims
    fact_claims = build_fact_claims(
        sources.get("claims"),
        dim_policy, dim_customer, dim_date, dim_geography,
        target_n=10_000,
    )

    # Step 3: fact_premiums
    fact_premiums = build_fact_premiums(
        sources.get("premiums"),
        dim_policy, dim_date,
        target_n=14_000,
    )

    # Validate no nulls in FK columns
    print_banner("FK NULL VALIDATION")
    assert_no_nulls_in_fk(fact_claims,   ["policy_id", "customer_id", "date_key", "geography_id"], "fact_claims")
    assert_no_nulls_in_fk(fact_premiums, ["policy_id", "date_key"], "fact_premiums")
    print("  No null FK values found in fact tables. [OK]")

    # Step 5: Referential Integrity Check (GATE)
    ri_passed = referential_integrity_check(
        fact_claims, fact_premiums,
        dim_policy, dim_customer, dim_geography, dim_date
    )

    if not ri_passed:
        raise SystemExit(
            "\nPipeline aborted: referential integrity check FAILED.\n"
            "Fix FK orphans before writing output or opening Power BI."
        )

    # Step 6: Write outputs
    write_outputs(fact_claims, fact_premiums, dim_policy, dim_customer, dim_geography, dim_date)

    # Summary
    print_summary(fact_claims, fact_premiums, dim_policy, dim_customer, dim_geography, dim_date)

    print("=" * 62)
    print("  Pipeline complete. Open Power BI and import /data/clean/.")
    print("=" * 62)


if __name__ == "__main__":
    main()
