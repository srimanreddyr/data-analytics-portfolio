-- ============================================================
-- Project 1: BEFORE — Slow, Unoptimized Queries
-- Author: Sriman Reddy Rondla
-- Run these first and note execution time / logical reads
-- ============================================================

USE LogisticsDB;
GO

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

-- ─── QUERY 1 (SLOW): Regional Shipment Summary ──────────────
-- Problem: SELECT *, no index on Status/Region, full table scan
-- Reported dashboard load time: ~47 seconds on 10M rows

SELECT *
FROM dbo.Shipments s
WHERE s.Status = 'Delivered'
  AND YEAR(s.ActualDelivDate) = YEAR(GETDATE())
ORDER BY s.ShipmentDate DESC;
GO

-- ─── QUERY 2 (SLOW): On-Time Delivery Rate ──────────────────
-- Problem: Correlated subquery runs once per row (N+1 problem)
-- Reported dashboard load time: ~31 seconds on 10M rows

SELECT
    r.RegionName,
    COUNT(s.ShipmentID) AS TotalShipments,
    (
        SELECT COUNT(*)
        FROM dbo.Shipments s2
        WHERE s2.DestRegionID = s.DestRegionID
          AND s2.Status = 'Delivered'
          AND s2.ActualDelivDate <= s2.PromisedDelivDate
    ) AS OnTimeCount
FROM dbo.Shipments s
JOIN dbo.Regions r ON s.DestRegionID = r.RegionID
GROUP BY r.RegionName, s.DestRegionID;
GO

-- ─── QUERY 3 (SLOW): Inventory Aging Report ─────────────────
-- Problem: Function on indexed column prevents index seek
-- Reported dashboard load time: ~62 seconds on 10M rows

SELECT *
FROM dbo.Inventory i
JOIN dbo.Warehouses w ON i.WarehouseID = w.WarehouseID
WHERE DATEDIFF(DAY, i.LastUpdated, GETDATE()) > 30
  AND i.QuantityOnHand < i.ReorderPoint;
GO

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO
