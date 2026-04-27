"""
pipeline.py — ETL Orchestrator: Extract → Transform → Validate → Load
Author: Sriman Reddy Rondla

Run this file to execute the full pipeline end-to-end.
"""

import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from config import (
    RAW_CSV_PATH, RAW_EXCEL_PATH, RAW_JSON_PATH,
    OUTPUT_PARQUET, OUTPUT_CSV, VALIDATION_RPT, LOG_FILE,
    COLUMN_MAP, VALID_STATUSES, VALID_CARRIERS, VALID_REGIONS,
    DATE_MIN, OUTLIER_SIGMA, STATUS_MAP
)

# ─── LOGGING ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# EXTRACT
# ═══════════════════════════════════════════════════════════════
def extract_csv(path) -> pd.DataFrame:
    log.info(f"Extracting CSV: {path}")
    df = pd.read_csv(path, dtype=str)
    log.info(f"  CSV rows loaded: {len(df):,}")
    return df

def extract_excel_lookup(path) -> pd.DataFrame:
    log.info(f"Extracting carrier lookup: {path}")
    return pd.read_excel(path, dtype=str)

def extract_json(path) -> pd.DataFrame:
    log.info(f"Extracting JSON: {path}")
    with open(path) as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    log.info(f"  JSON rows loaded: {len(df):,}")
    return df


# ═══════════════════════════════════════════════════════════════
# TRANSFORM
# ═══════════════════════════════════════════════════════════════
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to standard names using COLUMN_MAP"""
    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})
    return df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse multiple date formats → standard ISO date"""
    date_cols = ["shipment_date", "promised_delivery_date", "actual_delivery_date"]
    for col in date_cols:
        if col in df.columns:
            # Coerce to string first, then parse — handles ISO8601, d-m-Y, m/d/Y, Ymd
            series = df[col].astype(str).replace({"None": pd.NA, "nan": pd.NA, "NaT": pd.NA})
            # Strip timezone info for uniform naive datetime handling
            series = series.str.replace(r"T\d{2}:\d{2}:\d{2}Z?$", "", regex=True)
            df[col] = pd.to_datetime(series, format="mixed", dayfirst=False, errors="coerce")
    return df

def normalize_status(df: pd.DataFrame) -> pd.DataFrame:
    """Map inconsistent status strings to standard enum values"""
    if "status" in df.columns:
        df["status"] = (
            df["status"]
            .str.strip()
            .map(lambda x: STATUS_MAP.get(x, x) if isinstance(x, str) else x)
        )
    return df

def normalize_carriers(df: pd.DataFrame) -> pd.DataFrame:
    """Uppercase carrier codes, impute missing from region mode"""
    if "carrier_code" not in df.columns:
        return df
    df["carrier_code"] = df["carrier_code"].str.upper().str.strip()
    # Impute missing carrier from region mode
    if "dest_region" in df.columns:
        mode_map = (
            df.dropna(subset=["carrier_code"])
            .groupby("dest_region")["carrier_code"]
            .agg(lambda x: x.mode().iloc[0] if len(x.mode()) else "UPS")
        )
        missing = df["carrier_code"].isna()
        df.loc[missing, "carrier_code"] = df.loc[missing, "dest_region"].map(mode_map)
        log.info(f"  Imputed {missing.sum():,} missing carrier codes from region mode")
    return df

def normalize_regions(df: pd.DataFrame) -> pd.DataFrame:
    """Title-case regions, map unknowns to 'UNKNOWN'"""
    if "dest_region" in df.columns:
        df["dest_region"] = df["dest_region"].str.strip().str.title()
        df.loc[~df["dest_region"].isin(VALID_REGIONS), "dest_region"] = "UNKNOWN"
    return df

def clean_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric cols, flag negatives and outliers"""
    for col in ["freight_cost_usd", "weight_lbs", "item_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Flag negative freight
    df["is_negative_freight"] = df["freight_cost_usd"] < 0
    neg_count = df["is_negative_freight"].sum()
    if neg_count > 0:
        log.warning(f"  Found {neg_count} negative freight costs — flagged")

    # Flag outliers (z-score > OUTLIER_SIGMA)
    mean = df["freight_cost_usd"].mean()
    std  = df["freight_cost_usd"].std()
    df["is_freight_outlier"] = (
        (df["freight_cost_usd"] - mean).abs() > OUTLIER_SIGMA * std
    )
    log.info(f"  Freight outliers flagged: {df['is_freight_outlier'].sum():,}")
    return df

def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate tracking numbers — keep latest by shipment_date"""
    before = len(df)
    df = df.sort_values("shipment_date", ascending=False)
    df = df.drop_duplicates(subset=["tracking_number"], keep="first")
    removed = before - len(df)
    if removed > 0:
        log.info(f"  Removed {removed:,} duplicate tracking numbers")
    return df

def derive_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add calculated fields useful for reporting"""
    if "actual_delivery_date" in df.columns and "promised_delivery_date" in df.columns:
        df["days_to_deliver"] = (
            df["actual_delivery_date"] - df["shipment_date"]
        ).dt.days
        df["on_time"] = (
            (df["status"] == "Delivered") &
            (df["actual_delivery_date"] <= df["promised_delivery_date"])
        )
        df["delay_days"] = (
            df["actual_delivery_date"] - df["promised_delivery_date"]
        ).dt.days.clip(lower=0)
    df["pipeline_run_ts"] = datetime.now().isoformat()
    return df


# ═══════════════════════════════════════════════════════════════
# VALIDATE
# ═══════════════════════════════════════════════════════════════
def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    checks = {}
    issues = []

    # Invalid statuses
    bad_status = ~df["status"].isin(VALID_STATUSES) & df["status"].notna()
    checks["invalid_status_count"] = int(bad_status.sum())

    # Invalid carriers
    bad_carrier = ~df["carrier_code"].isin(VALID_CARRIERS) & df["carrier_code"].notna()
    checks["invalid_carrier_count"] = int(bad_carrier.sum())

    # Future shipment dates
    future_ship = df["shipment_date"] > pd.Timestamp.now()
    checks["future_shipment_date_count"] = int(future_ship.sum())

    # Too-old dates
    min_ts = pd.Timestamp(DATE_MIN)
    old_dates = df["shipment_date"] < min_ts
    checks["pre_min_date_count"] = int(old_dates.sum())

    # Negative freight
    checks["negative_freight_count"] = int(df["is_negative_freight"].sum())
    checks["freight_outlier_count"]  = int(df["is_freight_outlier"].sum())

    # Null critical fields
    for col in ["tracking_number", "shipment_date", "status", "dest_region"]:
        if col in df.columns:
            checks[f"null_{col}"] = int(df[col].isna().sum())

    total_issues = sum(v for k, v in checks.items()
                       if k not in ("freight_outlier_count",))  # outliers are warnings
    log.info(f"  Validation complete — {total_issues:,} issues found")

    # Build report df
    report = pd.DataFrame([
        {"check": k, "count": v, "pass": v == 0}
        for k, v in checks.items()
    ])
    return report, checks


# ═══════════════════════════════════════════════════════════════
# LOAD
# ═══════════════════════════════════════════════════════════════
def load(df: pd.DataFrame, report: pd.DataFrame):
    df.to_parquet(OUTPUT_PARQUET, index=False)
    df.to_csv(OUTPUT_CSV, index=False)
    report.to_csv(VALIDATION_RPT, index=False)
    log.info(f"  Loaded {len(df):,} rows → {OUTPUT_PARQUET}")
    log.info(f"  Validation report → {VALIDATION_RPT}")


# ═══════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════
def run_pipeline():
    start = datetime.now()
    log.info("=" * 60)
    log.info("PIPELINE START")
    log.info("=" * 60)

    # EXTRACT
    df_csv  = extract_csv(RAW_CSV_PATH)
    df_json = extract_json(RAW_JSON_PATH)
    carrier_lookup = extract_excel_lookup(RAW_EXCEL_PATH)

    # COMBINE SOURCES — standardize columns per source BEFORE concat to avoid duplicates
    df_csv  = standardize_columns(df_csv)
    df_json = standardize_columns(df_json)
    df = pd.concat([df_csv, df_json], ignore_index=True)
    # Drop any remaining duplicate column names (keep first occurrence)
    df = df.loc[:, ~df.columns.duplicated()]
    log.info(f"Combined source rows: {len(df):,}")

    # TRANSFORM
    log.info("--- TRANSFORM ---")
    df = parse_dates(df)
    df = normalize_status(df)
    df = normalize_regions(df)
    df = normalize_carriers(df)
    df = clean_numeric(df)
    df = deduplicate(df)
    df = derive_fields(df)

    # VALIDATE
    log.info("--- VALIDATE ---")
    report, checks = validate(df)

    # LOAD
    log.info("--- LOAD ---")
    load(df, report)

    elapsed = (datetime.now() - start).total_seconds()
    log.info(f"PIPELINE COMPLETE in {elapsed:.1f}s | {len(df):,} rows loaded")
    log.info("=" * 60)
    return df, report

if __name__ == "__main__":
    df, report = run_pipeline()
    print("\n--- VALIDATION SUMMARY ---")
    print(report.to_string(index=False))
