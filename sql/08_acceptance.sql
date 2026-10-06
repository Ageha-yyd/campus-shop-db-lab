SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

IF (SELECT COUNT(*) FROM sys.tables WHERE schema_id=SCHEMA_ID(N'dbo')) <> 6
    THROW 51010, 'Expected exactly six dbo business tables.', 1;
IF (SELECT COUNT(*) FROM dbo.Product) <> 6 THROW 51011, 'Unexpected Product baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Inventory) <> 6 THROW 51011, 'Unexpected Inventory baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Member) <> 4 THROW 51011, 'Unexpected Member baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Employee) <> 3 THROW 51011, 'Unexpected Employee baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.ShopOrder) <> 7 THROW 51011, 'Unexpected ShopOrder baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.OrderLine) <> 11 THROW 51011, 'Unexpected OrderLine baseline.', 1;
IF (SELECT COUNT(*) FROM sys.views WHERE schema_id=SCHEMA_ID(N'dbo')) <> 4
    THROW 51012, 'Expected four business views.', 1;
IF (SELECT COUNT(*) FROM dbo.vw_OrderDetail) <> 11
    THROW 51013, 'Order detail view lost/duplicated rows.', 1;
DECLARE @sales TABLE (ProductCode varchar(12), UnitsSold int, SalesAmount decimal(12,2));
INSERT @sales VALUES ('D001',4,24.00),('D002',3,21.00),('D003',5,20.00),('D004',3,21.00),('D005',0,0.00),('D006',0,0.00);
IF EXISTS (SELECT * FROM @sales EXCEPT SELECT ProductCode,UnitsSold,SalesAmount FROM dbo.vw_ProductSales)
   OR EXISTS (SELECT ProductCode,UnitsSold,SalesAmount FROM dbo.vw_ProductSales EXCEPT SELECT * FROM @sales)
    THROW 51014, 'Completed sales/zero-sales/cancelled-sale result is incorrect.', 1;
DECLARE @members TABLE (MemberCode varchar(12), CompletedOrders int, CupsPurchased int, CompletedAmount decimal(12,2));
INSERT @members VALUES ('M001',2,6,40.00),('M002',1,1,4.00),('M003',1,2,10.00),('M004',0,0,0.00);
IF EXISTS (SELECT * FROM @members EXCEPT SELECT MemberCode,CompletedOrders,CupsPurchased,CompletedAmount FROM dbo.vw_MemberConsumption)
   OR EXISTS (SELECT MemberCode,CompletedOrders,CupsPurchased,CompletedAmount FROM dbo.vw_MemberConsumption EXCEPT SELECT * FROM @members)
    THROW 51015, 'Member totals or zero-consumption member result is incorrect.', 1;
DECLARE @inventory TABLE (ProductCode varchar(12), OnHand int, RestockThreshold int, StockStatus nvarchar(10), SuggestedPreparationCups bigint);
INSERT @inventory VALUES ('D001',20,10,N'有库存',0),('D002',12,12,N'低库存',12),('D003',5,8,N'低库存',11),('D004',0,6,N'缺货',12),('D005',18,4,N'有库存',0),('D006',9,5,N'有库存',0);
IF EXISTS (SELECT * FROM @inventory EXCEPT SELECT ProductCode,OnHand,RestockThreshold,StockStatus,SuggestedPreparationCups FROM dbo.vw_InventoryStatus)
   OR EXISTS (SELECT ProductCode,OnHand,RestockThreshold,StockStatus,SuggestedPreparationCups FROM dbo.vw_InventoryStatus EXCEPT SELECT * FROM @inventory)
    THROW 51016, 'Preparation threshold/boundary/zero-stock result is incorrect.', 1;
IF (SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales) <> 86.00
    THROW 51017, 'Completed revenue differs from expected 86.00.', 1;
DECLARE @having TABLE (MemberCode varchar(12));
INSERT @having
SELECT m.MemberCode FROM dbo.Member m
JOIN dbo.ShopOrder o ON o.MemberCode=m.MemberCode AND o.Status='COMPLETED'
JOIN dbo.OrderLine l ON l.OrderNo=o.OrderNo
GROUP BY m.MemberCode HAVING SUM(l.Quantity*l.UnitPrice)>=10.00;
IF (SELECT COUNT(*) FROM @having)<>2
   OR NOT EXISTS (SELECT 1 FROM @having WHERE MemberCode='M001')
   OR NOT EXISTS (SELECT 1 FROM @having WHERE MemberCode='M003')
    THROW 51022, 'HAVING boundary did not return M001 and M003.', 1;
DECLARE @above_average TABLE (ProductCode varchar(12));
INSERT @above_average SELECT ProductCode FROM dbo.Product
WHERE IsActive=1 AND UnitPrice>(SELECT AVG(UnitPrice) FROM dbo.Product WHERE IsActive=1);
IF (SELECT COUNT(*) FROM @above_average)<>3
   OR EXISTS (SELECT 1 FROM @above_average WHERE ProductCode NOT IN ('D001','D002','D004'))
    THROW 51023, 'Business subquery returned incorrect products.', 1;
IF (SELECT COUNT(*) FROM dbo.ShopOrder WHERE Status='COMPLETED' AND MemberCode IS NULL) <> 2
    THROW 51018, 'Expected two anonymous completed orders.', 1;
IF EXISTS (SELECT 1 FROM dbo.Product WHERE ProductCode LIKE 'D99%')
   OR EXISTS (SELECT 1 FROM dbo.ShopOrder WHERE OrderNo IN ('MT-CRUD-ROLLBACK','MT-ROLE-ROLLBACK','MT-CONSTRAINT','NO-SUCH-ORDER'))
   OR EXISTS (SELECT 1 FROM dbo.Member WHERE MemberCode IN ('M998','M999'))
    THROW 51019, 'A demonstration left temporary business data.', 1;
IF DATABASE_PRINCIPAL_ID(N'shop_clerk') IS NULL OR DATABASE_PRINCIPAL_ID(N'shop_manager') IS NULL
    THROW 51020, 'Expected roles are missing.', 1;
IF EXISTS (SELECT 1 FROM dbo.Member WHERE Phone IS NOT NULL)
    THROW 51021, 'Seed data should not include personal phone numbers.', 1;
SELECT N'PASS' AS acceptance,
       (SELECT COUNT(*) FROM sys.tables WHERE schema_id=SCHEMA_ID(N'dbo')) AS business_tables,
       (SELECT COUNT(*) FROM sys.views WHERE schema_id=SCHEMA_ID(N'dbo')) AS business_views,
       (SELECT COUNT(*) FROM dbo.Product) AS products,
       (SELECT COUNT(*) FROM dbo.ShopOrder) AS orders,
       (SELECT COUNT(*) FROM dbo.OrderLine) AS order_lines,
       (SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales) AS completed_revenue;
SELECT N'PASS' AS boundary_verification,
       N'zero sales / cancelled orders / anonymous orders / member HAVING / stock threshold / cleanup' AS checked;
SELECT DB_NAME() AS database_name, CAST(SERVERPROPERTY('ProductVersion') AS varchar(30)) AS engine_version;
GO
