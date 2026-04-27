-- ============================================================
-- Project 1: AFTER — Optimized Queries + Index Strategy
-- Author: Sriman Reddy Rondla
-- ============================================================

USE LogisticsDB;
GO

-- ─── STEP 1: Create Indexes ──────────────────────────────────
-- Composite index supporting Status + date range queries
CREATE NONCLUSTERED INDEX IX_Shipments_Status_DelivDate
    ON dbo.Shipments (Status, ActualDelivDate)
    INCLUDE (ShipmentID, DestRegionID, ShipmentDate, FreightCostUSD, ItemCount);

-- Index for region-based aggregations
CREATE NONCLUSTERED INDEX IX_Shipments_DestRegion_Status
    ON dbo.Shipments (DestRegionID, Status)
    INCLUDE (ActualDelivDate, PromisedDelivDate, ShipmentID);

-- Index for inventory aging (SARGable date filter)
CREATE NONCLUSTERED INDEX IX_Inventory_LastUpdated
    ON dbo.Inventory (LastUpdated, WarehouseID)
    INCLUDE (PartNumber, QuantityOnHand, ReorderPoint);

GO

-- ─── QUERY 1 (OPTIMIZED): Regional Shipment Summary ─────────
-- Fix 1: Explicit column list instead of SELECT *
-- Fix 2: SARGable date filter (no function wrapping indexed col)
-- Fix 3: Index now supports an index seek instead of full scan

DECLARE @YearStart DATE = DATEFROMPARTS(YEAR(GETDATE()), 1, 1);
DECLARE @YearEnd   DATE = DATEFROMPARTS(YEAR(GETDATE()), 12, 31);

SELECT
    s.ShipmentID,
    s.TrackingNumber,
    s.ShipmentDate,
    s.ActualDelivDate,
    s.Status,
    s.FreightCostUSD,
    s.ItemCount,
    r.RegionName
FROM dbo.Shipments s
JOIN dbo.Regions r ON s.DestRegionID = r.RegionID
WHERE s.Status = 'Delivered'
  AND s.ActualDelivDate >= @YearStart
  AND s.ActualDelivDate <= @YearEnd
ORDER BY s.ShipmentDate DESC;
GO

-- ─── QUERY 2 (OPTIMIZED): On-Time Delivery Rate ─────────────
-- Fix: Replaced correlated subquery with a single-pass CTE + JOIN
-- One aggregation pass replaces N+1 subquery executions

WITH DeliveryStats AS (
    SELECT
        DestRegionID,
        COUNT(*)                                        AS TotalDelivered,
        SUM(CASE WHEN ActualDelivDate <= PromisedDelivDate THEN 1 ELSE 0 END) AS OnTime
    FROM dbo.Shipments
    WHERE Status = 'Delivered'
    GROUP BY DestRegionID
),
AllShipments AS (
    SELECT DestRegionID, COUNT(*) AS TotalShipments
    FROM dbo.Shipments
    GROUP BY DestRegionID
)
SELECT
    r.RegionName,
    a.TotalShipments,
    d.TotalDelivered,
    d.OnTime                                        AS OnTimeDeliveries,
    ROUND(100.0 * d.OnTime / NULLIF(d.TotalDelivered, 0), 1) AS OnTimePct
FROM dbo.Regions r
LEFT JOIN AllShipments  a ON r.RegionID = a.DestRegionID
LEFT JOIN DeliveryStats d ON r.RegionID = d.DestRegionID
ORDER BY OnTimePct DESC;
GO

-- ─── QUERY 3 (OPTIMIZED): Inventory Aging Report ─────────────
-- Fix: Replaced DATEDIFF() on indexed column with a SARGable
--      computed cutoff date — allows index seek

DECLARE @CutoffDate DATETIME = DATEADD(DAY, -30, GETDATE());

SELECT
    w.WarehouseName,
    r.RegionName,
    i.PartNumber,
    i.PartDescription,
    i.QuantityOnHand,
    i.ReorderPoint,
    i.QuantityOnHand - i.ReorderPoint AS StockGap,
    i.LastUpdated,
    DATEDIFF(DAY, i.LastUpdated, GETDATE()) AS DaysSinceUpdate
FROM dbo.Inventory i
JOIN dbo.Warehouses w ON i.WarehouseID = w.WarehouseID
JOIN dbo.Regions    r ON w.RegionID    = r.RegionID
WHERE i.LastUpdated < @CutoffDate          -- SARGable: uses IX_Inventory_LastUpdated
  AND i.QuantityOnHand < i.ReorderPoint
ORDER BY StockGap ASC;
GO
