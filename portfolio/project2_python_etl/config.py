# config.py — Pipeline Configuration
# Author: Sriman Reddy Rondla

from pathlib import Path

# ─── PATHS ──────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
RAW_DIR     = BASE_DIR / "data" / "raw"
OUTPUT_DIR  = BASE_DIR / "data" / "output"
LOG_DIR     = BASE_DIR / "logs"

for d in [RAW_DIR, OUTPUT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RAW_CSV_PATH    = RAW_DIR / "shipments_raw.csv"
RAW_EXCEL_PATH  = RAW_DIR / "carrier_lookup.xlsx"
RAW_JSON_PATH   = RAW_DIR / "api_shipments.json"
OUTPUT_PARQUET  = OUTPUT_DIR / "shipments_clean.parquet"
OUTPUT_CSV      = OUTPUT_DIR / "shipments_clean.csv"
VALIDATION_RPT  = OUTPUT_DIR / "validation_report.csv"
LOG_FILE        = LOG_DIR   / "pipeline.log"

# ─── COLUMN MAPPING ─────────────────────────────────────────
# Maps messy source column names → clean standard names
COLUMN_MAP = {
    "tracking_no":       "tracking_number",
    "TrackingNumber":    "tracking_number",
    "TRACKING":          "tracking_number",
    "ship_date":         "shipment_date",
    "ShipDate":          "shipment_date",
    "promised_del":      "promised_delivery_date",
    "PromisedDelivery":  "promised_delivery_date",
    "actual_del":        "actual_delivery_date",
    "ActualDelivery":    "actual_delivery_date",
    "carrier":           "carrier_code",
    "Carrier":           "carrier_code",
    "region":            "dest_region",
    "Region":            "dest_region",
    "wt_lbs":            "weight_lbs",
    "freight_usd":       "freight_cost_usd",
    "FreightCost":       "freight_cost_usd",
    "item_cnt":          "item_count",
    "status":            "status",
    "Status":            "status",
}

# ─── VALIDATION RULES ────────────────────────────────────────
VALID_STATUSES  = {"Delivered", "In Transit", "Delayed", "Cancelled"}
VALID_CARRIERS  = {"UPS", "FEDEX", "USPS", "DHL", "XPO"}
VALID_REGIONS   = {"Midwest", "Northeast", "Southeast", "Southwest", "West Coast"}
DATE_MIN        = "2022-01-01"
OUTLIER_SIGMA   = 3.0   # Flag freight cost outliers beyond N std deviations
MAX_WEIGHT_LBS  = 10000

# ─── STATUS NORMALIZATION MAP ────────────────────────────────
STATUS_MAP = {
    "delivered":   "Delivered",
    "DELIVERED":   "Delivered",
    "in transit":  "In Transit",
    "IN TRANSIT":  "In Transit",
    "intransit":   "In Transit",
    "delayed":     "Delayed",
    "DELAYED":     "Delayed",
    "late":        "Delayed",
    "cancelled":   "Cancelled",
    "CANCELLED":   "Cancelled",
    "canceled":    "Cancelled",
}
