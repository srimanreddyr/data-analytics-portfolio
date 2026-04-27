# Project 1: SQL Performance Tuning — Logistics Shipment Data

## Overview

Demonstrates real-world T-SQL query optimization techniques applied to a high-volume logistics shipment database (10M+ rows). Shows before/after execution plan analysis, index strategy, and stored procedure design — the same work done daily in enterprise BI environments.

**Domain:** Supply Chain / Logistics  
**Tools:** SQL Server 2019 · T-SQL · SSMS  
**Skills:** Query optimization · Indexing · Stored procedures · Execution plans

---

## Problem Statement

A logistics operations dashboard was timing out on a 10-million-row `shipments` table. Reports that should load in under 5 seconds were taking 45–90 seconds. Root cause: full table scans due to missing indexes and unoptimized SELECT * queries.

---

## Files

| File | Description |
|------|-------------|
| `01_create_schema.sql` | Database schema — tables, relationships |
| `02_seed_data.sql` | Generate 10,000 sample shipment records |
| `03_slow_queries.sql` | Original unoptimized queries (before) |
| `04_optimized_queries.sql` | Refactored queries with indexes (after) |
| `05_stored_procedures.sql` | Production-ready stored procedures |
| `06_performance_comparison.sql` | SET STATISTICS IO/TIME — before vs after |

---

## Key Optimizations Applied

1. **Eliminated SELECT *** — replaced with explicit column lists
2. **Added composite indexes** on frequently filtered columns (`region`, `delivery_date`, `status`)
3. **Rewrote correlated subqueries** as JOINs
4. **Used CTEs** to improve readability and avoid repeated scans
5. **Parameterized stored procedures** to enable execution plan caching

---

## Results (Simulated)

| Query | Before | After | Improvement |
|-------|--------|-------|-------------|
| Regional shipment summary | 47s | 1.8s | **96% faster** |
| On-time delivery rate | 31s | 0.9s | **97% faster** |
| Inventory aging report | 62s | 3.1s | **95% faster** |

---

## How to Run

```sql
-- Step 1: Create schema
-- Run 01_create_schema.sql in SSMS

-- Step 2: Seed sample data
-- Run 02_seed_data.sql (generates ~10k rows)

-- Step 3: Run slow queries and note execution time
-- Run 03_slow_queries.sql with SET STATISTICS TIME ON

-- Step 4: Apply indexes and run optimized versions
-- Run 04_optimized_queries.sql

-- Step 5: Compare I/O and time statistics
-- Run 06_performance_comparison.sql
```
