-- ============================================================
-- Project 1: Production-Ready Stored Procedures
-- Author: Sriman Reddy Rondla
-- Used as the backend for Tableau / Power BI dashboard queries
-- ============================================================

USE LogisticsDB;
GO

-- ─── SP 1: Regional On-Time Delivery KPI ─────────────────────
CREATE OR ALTER PROCEDURE dbo.usp_GetOnTimeDeliveryKPI
    @StartDate  DATE = NULL,
    @EndDate    DATE = NULL,
    @RegionID   INT  = NULL   -- NULL = all regions
AS
BEGIN
    SET NOCOUNT ON;

    -- Default to current year if no range passed
    SET @StartDate = ISNULL(@StartDate, DATEFROMPARTS(YEAR(GETDATE()), 1, 1));
    SET @EndDate   = ISNULL(@EndDate,   GETDATE());

    WITH KPI AS (
        SELECT
            s.DestRegionID,
            COUNT(*)                                                         AS TotalShipments,
            SUM(CASE WHEN s.Status = 'Delivered' THEN 1 ELSE 0 END)         AS Delivered,
            SUM(CASE WHEN s.Status = 'Delayed'   THEN 1 ELSE 0 END)         AS Delayed,
            SUM(CASE WHEN s.Status = 'Cancelled' THEN 1 ELSE 0 END)         AS Cancelled,
            SUM(CASE WHEN s.Status = 'Delivered'
                      AND s.ActualDelivDate <= s.PromisedDelivDate
                     THEN 1 ELSE 0 END)                                      AS OnTime,
            SUM(s.FreightCostUSD)                                            AS TotalFreightCost,
            AVG(s.FreightCostUSD)                                            AS AvgFreightCost
        FROM dbo.Shipments s
        WHERE s.ShipmentDate >= @StartDate
          AND s.ShipmentDate <= @EndDate
          AND (@RegionID IS NULL OR s.DestRegionID = @RegionID)
        GROUP BY s.DestRegionID
    )
    SELECT
        r.RegionName,
        k.TotalShipments,
        k.Delivered,
        k.Delayed,
        k.Cancelled,
        k.OnTime,
        ROUND(100.0 * k.OnTime    / NULLIF(k.Delivered,       0), 1) AS OnTimePct,
        ROUND(100.0 * k.Delayed   / NULLIF(k.TotalShipments,  0), 1) AS DelayedPct,
        ROUND(k.TotalFreightCost,  2)                                 AS TotalFreightCost,
        ROUND(k.AvgFreightCost,    2)                                 AS AvgFreightCost
    FROM KPI k
    JOIN dbo.Regions r ON k.DestRegionID = r.RegionID
    ORDER BY OnTimePct DESC;
END;
GO

-- ─── SP 2: Warehouse Inventory Status ────────────────────────
CREATE OR ALTER PROCEDURE dbo.usp_GetInventoryStatus
    @WarehouseID    INT = NULL,   -- NULL = all warehouses
    @BelowReorder   BIT = 0       -- 1 = only items below reorder point
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        w.WarehouseName,
        r.RegionName,
        i.PartNumber,
        i.PartDescription,
        i.QuantityOnHand,
        i.ReorderPoint,
        i.QuantityOnHand - i.ReorderPoint     AS StockBuffer,
        CASE
            WHEN i.QuantityOnHand = 0               THEN 'Out of Stock'
            WHEN i.QuantityOnHand < i.ReorderPoint  THEN 'Below Reorder'
            WHEN i.QuantityOnHand < i.ReorderPoint * 1.25 THEN 'Near Reorder'
            ELSE 'Healthy'
        END                                   AS StockStatus,
        i.LastUpdated,
        DATEDIFF(DAY, i.LastUpdated, GETDATE()) AS DaysSinceUpdate
    FROM dbo.Inventory i
    JOIN dbo.Warehouses w ON i.WarehouseID = w.WarehouseID
    JOIN dbo.Regions    r ON w.RegionID    = r.RegionID
    WHERE (@WarehouseID IS NULL OR i.WarehouseID = @WarehouseID)
      AND (@BelowReorder = 0 OR i.QuantityOnHand < i.ReorderPoint)
    ORDER BY StockBuffer ASC;
END;
GO

-- ─── USAGE EXAMPLES ──────────────────────────────────────────
-- EXEC dbo.usp_GetOnTimeDeliveryKPI;                           -- current year, all regions
-- EXEC dbo.usp_GetOnTimeDeliveryKPI @RegionID = 1;            -- Midwest only
-- EXEC dbo.usp_GetOnTimeDeliveryKPI @StartDate = '2024-01-01', @EndDate = '2024-12-31';
-- EXEC dbo.usp_GetInventoryStatus;
-- EXEC dbo.usp_GetInventoryStatus @BelowReorder = 1;          -- reorder alerts only
-- EXEC dbo.usp_GetInventoryStatus @WarehouseID = 1;           -- Columbus DC only
