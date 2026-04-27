# Project 3: Supply Chain EDA — Warehouse KPI Analysis

## Overview

Exploratory data analysis of 5,000 logistics shipments across 5 regions and 5 carriers. Surfaces actionable KPIs: on-time delivery rates, freight cost distributions, monthly trends, and carrier performance — the same type of analysis that feeds Tableau and Power BI dashboards.

**Domain:** Supply Chain / Logistics  
**Tools:** Python · Pandas · NumPy · Matplotlib · Seaborn  
**Skills:** EDA · Statistical analysis · Data visualization · KPI reporting

---

## Key Findings

| KPI | Value |
|-----|-------|
| Overall on-time delivery rate | ~85% |
| Best-performing carrier | UPS (~91%) |
| Highest freight cost region | West Coast |
| Avg delay (when delayed) | ~5.2 days |

---

## Charts Produced

| Chart | Insight |
|-------|---------|
| `01_ontime_by_region.png` | Which regions have the worst delivery performance |
| `02_carrier_performance.png` | Carrier on-time rate ranked by volume |
| `03_monthly_trend.png` | Seasonal patterns in on-time delivery |
| `04_freight_by_region.png` | Freight cost spread and outliers by region |

---

## How to Run

```bash
pip install pandas numpy matplotlib seaborn

python supply_chain_eda.py
# Charts saved to: data/output/charts/
```

---

## Skills Demonstrated

- **Data generation** — synthetic data that mirrors real logistics schemas
- **Aggregation** — groupby with custom lambda aggregations
- **Visualization** — publication-quality charts without chart libraries
- **Statistical analysis** — outlier detection, distribution analysis, trend lines
- **Annotation** — value labels, reference lines, volume callouts on charts
