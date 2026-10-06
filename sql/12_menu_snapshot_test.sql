-- Run from repository root with SQLCMD. :r includes the actual menu updater.
SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
BEGIN TRANSACTION;
UPDATE dbo.Product SET UnitPrice=9.90 WHERE ProductCode='D001';
UPDATE dbo.OrderLine SET UnitPrice=5.00 WHERE OrderNo='MT-20261001-001' AND LineNumber=1;
SELECT N'BEFORE_MENU_REFRESH' AS stage,
       (SELECT UnitPrice FROM dbo.Product WHERE ProductCode='D001') AS current_menu_price,
       (SELECT UnitPrice FROM dbo.OrderLine WHERE OrderNo='MT-20261001-001' AND LineNumber=1) AS historical_price;
GO
:r sql/09_update_public_menu.sql
GO
IF NOT EXISTS (SELECT 1 FROM dbo.Product WHERE ProductCode='D001' AND UnitPrice=6.00)
   OR NOT EXISTS (SELECT 1 FROM dbo.OrderLine WHERE OrderNo='MT-20261001-001' AND LineNumber=1 AND UnitPrice=5.00)
BEGIN
    IF XACT_STATE()<>0 ROLLBACK;
    THROW 51090, 'Actual menu updater changed a historical sale-price snapshot.', 1;
END;
SELECT N'PASS' AS historical_price_preservation,
       (SELECT UnitPrice FROM dbo.Product WHERE ProductCode='D001') AS current_menu_price,
       (SELECT UnitPrice FROM dbo.OrderLine WHERE OrderNo='MT-20261001-001' AND LineNumber=1) AS historical_price;
ROLLBACK;
IF NOT EXISTS (SELECT 1 FROM dbo.Product WHERE ProductCode='D001' AND UnitPrice=6.00)
   OR NOT EXISTS (SELECT 1 FROM dbo.OrderLine WHERE OrderNo='MT-20261001-001' AND LineNumber=1 AND UnitPrice=6.00)
   OR (SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales)<>86.00
    THROW 51091, 'Price snapshot test did not restore the baseline.', 1;
SELECT N'PASS' AS snapshot_test_cleanup,
       (SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales) AS baseline_completed_revenue;
GO
