"""
supply_chain_eda.py — Warehouse KPI Analysis: Exploratory Data Analysis
Author: Sriman Reddy Rondla

Analyzes cleaned shipment data to surface operational insights:
- On-time delivery trends by region and carrier
- Freight cost distribution and outlier analysis
- Warehouse utilization patterns
- Delay root-cause breakdown
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ─── STYLE ───────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "font.family":      "sans-serif",
    "axes.titlesize":   13,
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
})
COLORS = ["#0A66C2", "#00A0DC", "#5CB8B2", "#F5A623", "#D0021B"]
OUTPUT_DIR = Path("data/output/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── GENERATE SAMPLE DATA ────────────────────────────────────
# (In production this reads from the pipeline output parquet)
np.random.seed(42)
N = 5000
REGIONS  = ["Midwest", "Northeast", "Southeast", "Southwest", "West Coast"]
CARRIERS = ["UPS", "FEDEX", "USPS", "DHL", "XPO"]

dates = pd.date_range("2023-01-01", "2024-12-31", periods=N)
carrier_arr = np.random.choice(CARRIERS, N, p=[0.3, 0.25, 0.2, 0.15, 0.1])
region_arr  = np.random.choice(REGIONS,  N, p=[0.3, 0.2, 0.2, 0.15, 0.15])

on_time_base = {"UPS": 0.91, "FEDEX": 0.88, "USPS": 0.76, "DHL": 0.83, "XPO": 0.85}
on_time = np.array([np.random.rand() < on_time_base[c] for c in carrier_arr])

freight_base = {"Midwest": 220, "Northeast": 290, "Southeast": 240, "Southwest": 270, "West Coast": 310}
freight = np.array([np.random.normal(freight_base[r], 60) for r in region_arr]).clip(50, 900)
delay_days = np.where(~on_time, np.random.randint(1, 12, N), 0)

df = pd.DataFrame({
    "shipment_date":   dates,
    "carrier_code":    carrier_arr,
    "dest_region":     region_arr,
    "freight_cost_usd":np.round(freight, 2),
    "on_time":         on_time,
    "delay_days":      delay_days,
    "item_count":      np.random.randint(1, 50, N),
    "weight_lbs":      np.round(np.random.uniform(5, 600, N), 1),
    "status":          np.where(on_time, "Delivered",
                        np.where(np.random.rand(N) < 0.3, "Delayed", "In Transit")),
    "month":           pd.to_datetime(dates).to_period("M"),
})


# ═══════════════════════════════════════════════════════════════
# CHART 1: On-Time Delivery Rate by Region (bar)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4.5))
ot_region = (
    df.groupby("dest_region")["on_time"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
    .reset_index()
)
bars = ax.barh(ot_region["dest_region"], ot_region["on_time"],
               color=COLORS, height=0.55, edgecolor="none")
for bar, val in zip(bars, ot_region["on_time"]):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", fontsize=10, fontweight="bold", color="#333")
ax.axvline(ot_region["on_time"].mean(), color="#ccc", linestyle="--", linewidth=1)
ax.set_xlim(0, 100)
ax.set_xlabel("On-Time Delivery Rate (%)")
ax.set_title("On-Time Delivery Rate by Region", fontweight="bold", pad=12)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "01_ontime_by_region.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Chart 1 saved: On-Time Delivery by Region")


# ═══════════════════════════════════════════════════════════════
# CHART 2: On-Time Rate by Carrier (with volume annotation)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4.5))
carrier_stats = df.groupby("carrier_code").agg(
    on_time_pct=("on_time", lambda x: x.mean() * 100),
    volume=("on_time", "count")
).sort_values("on_time_pct", ascending=False).reset_index()

bars = ax.bar(carrier_stats["carrier_code"], carrier_stats["on_time_pct"],
              color=COLORS[:len(carrier_stats)], width=0.5, edgecolor="none")
for bar, row in zip(bars, carrier_stats.itertuples()):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{row.on_time_pct:.1f}%\n(n={row.volume:,})",
            ha="center", fontsize=9, color="#333")
ax.set_ylim(0, 105)
ax.set_ylabel("On-Time Delivery Rate (%)")
ax.set_title("Carrier Performance: On-Time Rate & Volume", fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "02_carrier_performance.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Chart 2 saved: Carrier Performance")


# ═══════════════════════════════════════════════════════════════
# CHART 3: Monthly On-Time Trend (line)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 4.5))
monthly = (
    df.groupby(df["shipment_date"].dt.to_period("M"))["on_time"]
    .mean()
    .mul(100)
    .reset_index()
)
monthly["shipment_date"] = monthly["shipment_date"].astype(str)
ax.plot(monthly["shipment_date"], monthly["on_time"],
        color=COLORS[0], linewidth=2.5, marker="o", markersize=4)
ax.fill_between(monthly["shipment_date"], monthly["on_time"],
                alpha=0.08, color=COLORS[0])
ax.axhline(monthly["on_time"].mean(), color="#ccc", linestyle="--", linewidth=1,
           label=f"Avg: {monthly['on_time'].mean():.1f}%")
ax.set_ylabel("On-Time Delivery Rate (%)")
ax.set_title("Monthly On-Time Delivery Trend (2023–2024)", fontweight="bold", pad=12)
tick_spacing = max(1, len(monthly) // 12)
ax.set_xticks(range(0, len(monthly), tick_spacing))
ax.set_xticklabels(monthly["shipment_date"].iloc[::tick_spacing], rotation=45, ha="right")
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "03_monthly_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Chart 3 saved: Monthly Trend")


# ═══════════════════════════════════════════════════════════════
# CHART 4: Freight Cost Distribution by Region (box)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 5))
regions_ordered = (df.groupby("dest_region")["freight_cost_usd"]
                   .median().sort_values(ascending=False).index.tolist())
data_by_region = [df[df["dest_region"] == r]["freight_cost_usd"].values for r in regions_ordered]
bp = ax.boxplot(data_by_region, patch_artist=True, vert=True,
                medianprops=dict(color="white", linewidth=2))
for patch, color in zip(bp["boxes"], COLORS):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
ax.set_xticklabels(regions_ordered)
ax.set_ylabel("Freight Cost (USD)")
ax.set_title("Freight Cost Distribution by Region", fontweight="bold", pad=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "04_freight_by_region.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Chart 4 saved: Freight Distribution")


# ═══════════════════════════════════════════════════════════════
# SUMMARY STATS TABLE
# ═══════════════════════════════════════════════════════════════
print("\n─── SUMMARY KPIs ──────────────────────────────────")
print(f"Total shipments:        {len(df):,}")
print(f"Overall on-time rate:   {df['on_time'].mean()*100:.1f}%")
print(f"Avg freight cost:       ${df['freight_cost_usd'].mean():,.2f}")
print(f"Avg delay (delayed):    {df[df['delay_days']>0]['delay_days'].mean():.1f} days")
print(f"Carrier count:          {df['carrier_code'].nunique()}")
print(f"Regions covered:        {df['dest_region'].nunique()}")
print("\n─── ON-TIME RATE BY REGION ─────────────────────────")
print(df.groupby("dest_region")["on_time"].mean().mul(100).round(1).to_string())
print("\n─── AVG FREIGHT COST BY REGION ─────────────────────")
print(df.groupby("dest_region")["freight_cost_usd"].mean().round(2).to_string())
print(f"\n✓ All charts saved to: {OUTPUT_DIR}")
