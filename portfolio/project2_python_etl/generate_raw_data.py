"""
generate_raw_data.py — Creates intentionally messy raw data files
Author: Sriman Reddy Rondla

Simulates realistic data quality issues found in enterprise logistics systems:
- Mixed date formats
- Inconsistent status strings
- Missing carrier codes
- Negative/outlier freight costs
- Duplicate tracking numbers
- Non-standard column names per source
"""

import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
from config import RAW_CSV_PATH, RAW_EXCEL_PATH, RAW_JSON_PATH

np.random.seed(42)
random.seed(42)

N = 5000
CARRIERS  = ["UPS", "FEDEX", "USPS", "DHL", "XPO", None, "ups", "fedex"]
REGIONS   = ["Midwest", "Northeast", "Southeast", "Southwest", "West Coast", "MIDWEST", "midwest"]
STATUSES  = ["Delivered", "In Transit", "Delayed", "Cancelled", "delivered", "DELIVERED", "in transit", "late", "canceled"]

def rand_date(start="2023-01-01", days=730):
    base = datetime.strptime(start, "%Y-%m-%d")
    return base + timedelta(days=random.randint(0, days))

def messy_date(d):
    """Return date in one of several formats to simulate source inconsistency"""
    fmt = random.choice(["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y%m%d"])
    return d.strftime(fmt)

rows = []
tracking_pool = [f"TRK{str(i).zfill(9)}" for i in range(1, N + 1)]
# Introduce ~3% duplicates
tracking_pool += random.sample(tracking_pool, int(N * 0.03))
random.shuffle(tracking_pool)

for i, trk in enumerate(tracking_pool[:N]):
    ship   = rand_date()
    prom   = ship + timedelta(days=random.randint(1, 7))
    actual = prom + timedelta(days=random.randint(-2, 5)) if random.random() > 0.15 else None

    freight = round(random.uniform(50, 900), 2)
    # Inject outliers and negatives
    if random.random() < 0.01:
        freight = round(random.uniform(5000, 15000), 2)   # outlier
    if random.random() < 0.005:
        freight = -abs(freight)                             # negative (data error)

    carrier = random.choice(CARRIERS)
    # Blank out ~4% of carriers
    if random.random() < 0.04:
        carrier = None

    rows.append({
        "tracking_no":    trk,
        "ship_date":      messy_date(ship),
        "promised_del":   messy_date(prom),
        "actual_del":     messy_date(actual) if actual else None,
        "status":         random.choice(STATUSES),
        "carrier":        carrier,
        "region":         random.choice(REGIONS),
        "wt_lbs":         round(random.uniform(1, 600), 2),
        "freight_usd":    freight,
        "item_cnt":       random.randint(1, 50),
    })

csv_df = pd.DataFrame(rows)
csv_df.to_csv(RAW_CSV_PATH, index=False)
print(f"✓ Raw CSV written:   {RAW_CSV_PATH}  ({len(csv_df):,} rows)")

# ─── CARRIER LOOKUP EXCEL ────────────────────────────────────
carrier_df = pd.DataFrame({
    "carrier_code":    ["UPS",      "FEDEX",      "USPS",         "DHL",      "XPO"],
    "carrier_name":    ["UPS Inc.", "FedEx Corp", "US Postal Svc","DHL Express","XPO Logistics"],
    "default_region":  ["Midwest",  "Northeast",  "Southeast",    "Southwest", "West Coast"],
})
carrier_df.to_excel(RAW_EXCEL_PATH, index=False)
print(f"✓ Carrier Excel written: {RAW_EXCEL_PATH}")

# ─── JSON (API SIM) ──────────────────────────────────────────
api_records = []
for i in range(500):
    s = rand_date()
    api_records.append({
        "TrackingNumber":   f"API{str(i).zfill(6)}",
        "ShipDate":         s.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "PromisedDelivery": (s + timedelta(days=random.randint(1,5))).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ActualDelivery":   None if random.random() < 0.2 else
                            (s + timedelta(days=random.randint(1,8))).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "Status":           random.choice(["Delivered", "In Transit", "Delayed"]),
        "Carrier":          random.choice(["UPS", "FEDEX", "DHL"]),
        "Region":           random.choice(["Midwest", "Northeast", "West Coast"]),
        "FreightCost":      round(random.uniform(80, 700), 2),
        "item_cnt":         random.randint(1, 30),
        "wt_lbs":           round(random.uniform(5, 400), 2),
    })

with open(RAW_JSON_PATH, "w") as f:
    json.dump(api_records, f, indent=2)
print(f"✓ API JSON written:  {RAW_JSON_PATH}  ({len(api_records):,} records)")
print("\nAll raw source files generated. Run pipeline.py to process them.")
