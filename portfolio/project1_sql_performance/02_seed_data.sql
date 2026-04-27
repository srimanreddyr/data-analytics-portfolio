-- ============================================================
-- Project 1: Seed 10,000 Sample Shipment Records
-- Author: Sriman Reddy Rondla
-- ============================================================

USE LogisticsDB;
GO

SET NOCOUNT ON;

DECLARE @i INT = 1;
DECLARE @carriers TABLE (Code VARCHAR(10));
INSERT INTO @carriers VALUES ('UPS'),('FEDEX'),('USPS'),('DHL'),('XPO');

DECLARE @statuses TABLE (Status VARCHAR(20));
INSERT INTO @statuses VALUES ('Delivered'),('Delivered'),('Delivered'),('In Transit'),('Delayed'),('Cancelled');

WHILE @i <= 10000
BEGIN
    DECLARE @shipDate  DATE = DATEADD(DAY, -ABS(CHECKSUM(NEWID()) % 365), GETDATE());
    DECLARE @promised  DATE = DATEADD(DAY, ABS(CHECKSUM(NEWID()) % 7) + 1, @shipDate);
    DECLARE @status    VARCHAR(20);
    DECLARE @actual    DATE = NULL;
    DECLARE @delay     INT = ABS(CHECKSUM(NEWID()) % 5) - 1;  -- -1 to +3 days vs promised

    SELECT TOP 1 @status = Status FROM @statuses ORDER BY NEWID();

    IF @status = 'Delivered'
        SET @actual = DATEADD(DAY, @delay, @promised);
    ELSE IF @status = 'Delayed'
        SET @actual = DATEADD(DAY, ABS(CHECKSUM(NEWID()) % 10) + 3, @promised);

    INSERT INTO dbo.Shipments (
        TrackingNumber, OriginWarehouseID, DestRegionID,
        ShipmentDate, PromisedDelivDate, ActualDelivDate,
        Status, CarrierCode, WeightLbs, FreightCostUSD, ItemCount
    )
    SELECT
        'TRK' + RIGHT('000000000' + CAST(@i AS VARCHAR), 9),
        ABS(CHECKSUM(NEWID()) % 6) + 1,
        ABS(CHECKSUM(NEWID()) % 5) + 1,
        @shipDate,
        @promised,
        @actual,
        @status,
        (SELECT TOP 1 Code FROM @carriers ORDER BY NEWID()),
        ROUND(CAST(ABS(CHECKSUM(NEWID()) % 500) + 1 AS DECIMAL(8,2)) + RAND(), 2),
        ROUND(CAST(ABS(CHECKSUM(NEWID()) % 800) + 50 AS DECIMAL(10,2)) + RAND(), 2),
        ABS(CHECKSUM(NEWID()) % 50) + 1;

    SET @i = @i + 1;
END;

-- Seed inventory
DECLARE @w INT = 1;
DECLARE @p INT;
WHILE @w <= 6
BEGIN
    SET @p = 1;
    WHILE @p <= 20
    BEGIN
        INSERT INTO dbo.Inventory (WarehouseID, PartNumber, PartDescription, QuantityOnHand, ReorderPoint)
        VALUES (
            @w,
            'PART-' + RIGHT('0000' + CAST((@w * 100 + @p) AS VARCHAR), 6),
            'Honda Part Type ' + CAST(@p AS VARCHAR),
            ABS(CHECKSUM(NEWID()) % 2000) + 50,
            ABS(CHECKSUM(NEWID()) % 200) + 50
        );
        SET @p = @p + 1;
    END;
    SET @w = @w + 1;
END;

PRINT 'Seeded ' + CAST(@@ROWCOUNT AS VARCHAR) + ' records.';
SELECT COUNT(*) AS TotalShipments FROM dbo.Shipments;
GO
