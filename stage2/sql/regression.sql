SET NOCOUNT ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
-- Run before application demonstrations; assertions deliberately fail on semantic drift.
IF EXISTS(SELECT * FROM dbo.Baseline_OrderDetail EXCEPT SELECT * FROM dbo.vw_OrderDetail)
 OR EXISTS(SELECT * FROM dbo.vw_OrderDetail EXCEPT SELECT * FROM dbo.Baseline_OrderDetail) THROW 51200,'Order details changed.',1;
PRINT 'PASS 01 exact order detail equality both directions';
IF EXISTS(SELECT * FROM dbo.Baseline_ProductSales EXCEPT SELECT * FROM dbo.vw_ProductSales)
 OR EXISTS(SELECT * FROM dbo.vw_ProductSales EXCEPT SELECT * FROM dbo.Baseline_ProductSales) THROW 51201,'Sales changed.',1;
PRINT 'PASS 02 product sales equality including zero sales';
IF EXISTS(SELECT * FROM dbo.Baseline_Inventory EXCEPT SELECT * FROM dbo.Inventory)
 OR EXISTS(SELECT * FROM dbo.Inventory EXCEPT SELECT * FROM dbo.Baseline_Inventory) THROW 51202,'Inventory changed.',1;
PRINT 'PASS 03 opening inventory equality';
IF (SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales)<>86 OR (SELECT SUM(UnitsSold) FROM dbo.vw_ProductSales)<>15 THROW 51203,'Wrong totals.',1;
PRINT 'PASS 04 completed totals 6 orders / 15 cups / 86.00';
IF (SELECT COUNT(*) FROM dbo.ShopOrder WHERE Status='COMPLETED')<>6 THROW 51204,'Order counts changed.',1;
IF EXISTS(SELECT * FROM dbo.Baseline_Product EXCEPT SELECT * FROM dbo.Product) THROW 51205,'Product changed.',1;
IF EXISTS(SELECT * FROM dbo.Baseline_Member EXCEPT SELECT * FROM dbo.Member) THROW 51206,'Member changed.',1;
IF EXISTS(SELECT * FROM dbo.Baseline_Employee EXCEPT SELECT * FROM dbo.Employee) THROW 51207,'Employee changed.',1;
PRINT 'PASS 05 business identities and profiles preserved';
IF EXISTS(SELECT 1 FROM dbo.ShopOrder WHERE StockApplied<>0 OR CreatedByUserId IS NOT NULL) THROW 51208,'Historical stock flags changed.',1;
PRINT 'PASS 06 historical stock not deducted again';
BEGIN TRY
 BEGIN TRAN;
 INSERT dbo.OrderLine VALUES('NO_SUCH_ORDER',1,'D001',1,6);
 ROLLBACK;
 THROW 51209,'Invalid foreign key accepted.',1;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK;
 IF ERROR_NUMBER()<>547 THROW;
 PRINT 'PASS 07 invalid foreign key rejected 547';
END CATCH;
BEGIN TRY
 BEGIN TRAN;
 UPDATE dbo.Inventory SET Quantity=-1 WHERE ProductCode='D001';
 ROLLBACK;
 THROW 51210,'Invalid stock accepted.',1;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK;
 IF ERROR_NUMBER()<>547 THROW;
 PRINT 'PASS 08 negative stock rejected 547';
END CATCH;
BEGIN TRAN;
UPDATE dbo.Product SET UnitPrice=9.90 WHERE ProductCode='D001';
IF EXISTS(SELECT 1 FROM dbo.OrderLine WHERE ProductCode='D001' AND UnitPrice<>6) THROW 51211,'Historical price changed.',1;
ROLLBACK;
PRINT 'PASS 09 current menu price independent of historical price';
BEGIN TRAN;
INSERT dbo.Product VALUES('REG_OK',N'合法对照',N'测试',1,1,1);
INSERT dbo.Inventory(ProductCode,Quantity) VALUES('REG_OK',1);
ROLLBACK;
PRINT 'PASS 10 valid inserts accepted and rolled back';
SET XACT_ABORT OFF;
BEGIN TRAN;
CREATE USER stage2_reg_clerk WITHOUT LOGIN;
ALTER ROLE web_clerk ADD MEMBER stage2_reg_clerk;
EXECUTE AS USER='stage2_reg_clerk';
DECLARE @Products int=(SELECT COUNT(*) FROM dbo.Product);
REVERT;
IF @Products<>6 THROW 51212,'Clerk read denied.',1;
PRINT 'PASS 11 clerk SELECT permitted';
DECLARE @Error int=0;
EXECUTE AS USER='stage2_reg_clerk';
BEGIN TRY
 UPDATE dbo.Product SET UnitPrice=1 WHERE ProductCode='D001';
END TRY
BEGIN CATCH
 SET @Error=ERROR_NUMBER();
END CATCH;
REVERT;
IF @Error<>229 THROW 51213,'Clerk price write not denied.',1;
PRINT 'PASS 12 clerk price write denied 229';
SET @Error=0;
EXECUTE AS USER='stage2_reg_clerk';
BEGIN TRY
 SELECT PasswordHash FROM dbo.AppUser;
END TRY
BEGIN CATCH
 SET @Error=ERROR_NUMBER();
END CATCH;
REVERT;
IF @Error<>229 THROW 51214,'Clerk credential read not denied.',1;
ROLLBACK;
PRINT 'PASS 13 credential read denied 229; temporary test user rolled back';
SELECT * FROM dbo.vw_ProductSales ORDER BY ProductCode;
SELECT * FROM dbo.Inventory ORDER BY ProductCode;
SELECT OrderNo,Status,COUNT(*) OVER() AS order_count FROM dbo.ShopOrder ORDER BY OrderNo;
