-- ============================================================
-- Project 1: Performance Comparison — Before vs After
-- Author: Sriman Reddy Rondla
-- Run this after both 03_ and 04_ scripts to compare stats
-- ============================================================

USE LogisticsDB;
GO

-- Enable detailed I/O and time statistics
SET STATISTICS IO  ON;
SET STATISTICS TIME ON;
GO

PRINT '====================================================';
PRINT 'QUERY 1 BEFORE: SELECT * with function on date col';
PRINT '====================================================';
SELECT * FROM dbo.Shipments
WHERE Status = 'Delivered'
  AND YEAR(ActualDelivDate) = YEAR(GETDATE());
GO

PRINT '====================================================';
PRINT 'QUERY 1 AFTER: Explicit cols, SARGable filter, index';
PRINT '====================================================';
DECLARE @YS DATE = DATEFROMPARTS(YEAR(GETDATE()),1,1);
DECLARE @YE DATE = DATEFROMPARTS(YEAR(GETDATE()),12,31);
SELECT ShipmentID, TrackingNumber, ShipmentDate, ActualDelivDate, Status, FreightCostUSD
FROM dbo.Shipments
WHERE Status = 'Delivered'
  AND ActualDelivDate >= @YS
  AND ActualDelivDate <= @YE;
GO

PRINT '====================================================';
PRINT 'QUERY 2 BEFORE: Correlated subquery (N+1)';
PRINT '====================================================';
SELECT r.RegionName, COUNT(s.ShipmentID) AS Total,
    (SELECT COUNT(*) FROM dbo.Shipments s2
     WHERE s2.DestRegionID = s.DestRegionID
       AND s2.Status = 'Delivered'
       AND s2.ActualDelivDate <= s2.PromisedDelivDate) AS OnTime
FROM dbo.Shipments s JOIN dbo.Regions r ON s.DestRegionID = r.RegionID
GROUP BY r.RegionName, s.DestRegionID;
GO

PRINT '====================================================';
PRINT 'QUERY 2 AFTER: CTE single-pass aggregation';
PRINT '====================================================';
WITH Stats AS (
    SELECT DestRegionID,
           COUNT(*) AS Total,
           SUM(CASE WHEN Status='Delivered' AND ActualDelivDate<=PromisedDelivDate THEN 1 ELSE 0 END) AS OnTime
    FROM dbo.Shipments WHERE Status='Delivered'
    GROUP BY DestRegionID
)
SELECT r.RegionName, s.Total, s.OnTime,
       ROUND(100.0*s.OnTime/NULLIF(s.Total,0),1) AS OnTimePct
FROM Stats s JOIN dbo.Regions r ON s.DestRegionID=r.RegionID;
GO

SET STATISTICS IO  OFF;
SET STATISTICS TIME OFF;
GO

PRINT '';
PRINT 'Compare "logical reads" and "elapsed time" in the Messages tab.';
PRINT 'Lower logical reads = fewer pages read from disk/cache = faster query.';
