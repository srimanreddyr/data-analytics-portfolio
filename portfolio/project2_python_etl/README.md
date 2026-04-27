# Project 2: Python ETL Pipeline — Supply Chain Data Cleaning

## Overview

A production-style Python ETL pipeline that ingests raw supply chain data from multiple source formats (CSV, Excel, JSON/API simulation), cleans and validates it, and loads it into a structured target. Mirrors the daily data prep work done in enterprise logistics analytics environments.

**Domain:** Supply Chain / Logistics  
**Tools:** Python 3.10+ · Pandas · NumPy · logging  
**Skills:** ETL design · Data quality validation · Automation · Error handling

---

## Pipeline Architecture

```
[Raw CSV]──┐
[Raw Excel]─┼──► EXTRACT ──► TRANSFORM/CLEAN ──► VALIDATE ──► LOAD (Parquet/DB)
[API JSON]─┘         │              │                │
                      ▼              ▼                ▼
                  extract.py    transform.py     validate.py
```

---

## Files

| File | Description |
|------|-------------|
| `config.py` | Pipeline configuration (paths, thresholds, column maps) |
| `generate_raw_data.py` | Generates synthetic dirty raw data for demo |
| `extract.py` | Ingests CSV, Excel, and JSON sources |
| `transform.py` | Cleans, standardizes, and enriches data |
| `validate.py` | Data quality checks with pass/fail reporting |
| `load.py` | Outputs to Parquet and summary CSV |
| `pipeline.py` | Orchestrator — runs the full pipeline end-to-end |
| `requirements.txt` | Python dependencies |

---

## Common Data Quality Issues Handled

| Issue | Fix Applied |
|-------|-------------|
| Missing carrier codes | Imputed from mode by region |
| Negative freight costs | Flagged and excluded from aggregation |
| Duplicate tracking numbers | De-duplicated, kept latest record |
| Mixed date formats | Normalized to ISO 8601 (YYYY-MM-DD) |
| Status field inconsistencies | Mapped to standard enum values |
| Freight cost outliers (>3σ) | Flagged with `is_outlier` column |
| Invalid region codes | Mapped via lookup table, unmapped = 'UNKNOWN' |

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample dirty data
python generate_raw_data.py

# Run full pipeline
python pipeline.py

# Output: data/output/shipments_clean.parquet
#         data/output/validation_report.csv
#         logs/pipeline.log
```

---

## Sample Validation Report Output

```
Pipeline Run: 2025-01-15 09:32:11
Source records:      10,247
After dedup:          9,891
Failed validation:      312 (3.0%)
Loaded to target:     9,579

CHECKS PASSED:
  ✓ No negative freight costs
  ✓ Date range valid (2023-01-01 to today)
  ✓ All status values in allowed enum
  ✓ Tracking number uniqueness

CHECKS FAILED:
  ✗ Missing carrier code: 187 records → imputed
  ✗ Freight cost outliers (>3σ): 125 records → flagged
```
