-- ============================================================
-- Project 1: Logistics Shipment Database Schema
-- Author: Sriman Reddy Rondla
-- Tools: SQL Server 2019 / T-SQL
-- ============================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'LogisticsDB')
    CREATE DATABASE LogisticsDB;
GO

USE LogisticsDB;
GO

-- ─── REGIONS ─────────────────────────────────────────────────
IF OBJECT_ID('dbo.Regions', 'U') IS NOT NULL DROP TABLE dbo.Regions;
CREATE TABLE dbo.Regions (
    RegionID    INT PRIMARY KEY IDENTITY(1,1),
    RegionName  VARCHAR(50)  NOT NULL,
    Country     VARCHAR(50)  NOT NULL DEFAULT 'USA'
);

INSERT INTO dbo.Regions (RegionName) VALUES
    ('Midwest'), ('Northeast'), ('Southeast'), ('Southwest'), ('West Coast');

-- ─── WAREHOUSES ──────────────────────────────────────────────
IF OBJECT_ID('dbo.Warehouses', 'U') IS NOT NULL DROP TABLE dbo.Warehouses;
CREATE TABLE dbo.Warehouses (
    WarehouseID     INT PRIMARY KEY IDENTITY(1,1),
    WarehouseName   VARCHAR(100) NOT NULL,
    RegionID        INT NOT NULL REFERENCES dbo.Regions(RegionID),
    Capacity        INT NOT NULL,   -- in units
    UtilizationPct  DECIMAL(5,2)
);

INSERT INTO dbo.Warehouses (WarehouseName, RegionID, Capacity, UtilizationPct) VALUES
    ('Columbus DC',       1, 50000, 78.4),
    ('Detroit Hub',       1, 35000, 82.1),
    ('New York DC',       2, 60000, 91.3),
    ('Atlanta DC',        3, 45000, 65.7),
    ('Dallas Hub',        4, 55000, 73.9),
    ('Los Angeles DC',    5, 70000, 88.2);

-- ─── SHIPMENTS ───────────────────────────────────────────────
IF OBJECT_ID('dbo.Shipments', 'U') IS NOT NULL DROP TABLE dbo.Shipments;
CREATE TABLE dbo.Shipments (
    ShipmentID          INT PRIMARY KEY IDENTITY(1,1),
    TrackingNumber      VARCHAR(20)     NOT NULL UNIQUE,
    OriginWarehouseID   INT             NOT NULL REFERENCES dbo.Warehouses(WarehouseID),
    DestRegionID        INT             NOT NULL REFERENCES dbo.Regions(RegionID),
    ShipmentDate        DATE            NOT NULL,
    PromisedDelivDate   DATE            NOT NULL,
    ActualDelivDate     DATE            NULL,
    Status              VARCHAR(20)     NOT NULL CHECK (Status IN ('In Transit','Delivered','Delayed','Cancelled')),
    CarrierCode         VARCHAR(10)     NOT NULL,
    WeightLbs           DECIMAL(8,2)    NOT NULL,
    FreightCostUSD      DECIMAL(10,2)   NOT NULL,
    ItemCount           INT             NOT NULL
);

-- ─── INVENTORY ───────────────────────────────────────────────
IF OBJECT_ID('dbo.Inventory', 'U') IS NOT NULL DROP TABLE dbo.Inventory;
CREATE TABLE dbo.Inventory (
    InventoryID     INT PRIMARY KEY IDENTITY(1,1),
    WarehouseID     INT         NOT NULL REFERENCES dbo.Warehouses(WarehouseID),
    PartNumber      VARCHAR(20) NOT NULL,
    PartDescription VARCHAR(100),
    QuantityOnHand  INT         NOT NULL DEFAULT 0,
    ReorderPoint    INT         NOT NULL DEFAULT 100,
    LastUpdated     DATETIME    NOT NULL DEFAULT GETDATE()
);

PRINT 'Schema created successfully.';
GO
