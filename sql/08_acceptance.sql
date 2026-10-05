SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

DECLARE @table_count int = (SELECT COUNT(*) FROM sys.tables WHERE schema_id = SCHEMA_ID(N'dbo'));
IF @table_count <> 6 THROW 51010, 'Expected exactly six dbo tables.', 1;
IF (SELECT COUNT(*) FROM dbo.Product) <> 3 THROW 51011, 'Unexpected Product baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Inventory) <> 3 THROW 51012, 'Unexpected Inventory baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Member) <> 2 THROW 51013, 'Unexpected Member baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Employee) <> 2 THROW 51014, 'Unexpected Employee baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.ShopOrder) <> 3 THROW 51015, 'Unexpected ShopOrder baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.OrderLine) <> 4 THROW 51016, 'Unexpected OrderLine baseline.', 1;
IF (SELECT COUNT(*) FROM dbo.Product WHERE ProductCode = 'D999') <> 0 THROW 51017, 'CRUD rollback left a temporary product.', 1;
IF (SELECT COUNT(*) FROM dbo.vw_ProductSales) <> 3 THROW 51018, 'Product sales view did not retain all products.', 1;
IF (SELECT UnitsSold FROM dbo.vw_ProductSales WHERE ProductCode = 'D003') <> 0 THROW 51019, 'Zero-sales product result is incorrect.', 1;
IF (SELECT SalesAmount FROM dbo.vw_ProductSales WHERE ProductCode = 'D001') <> 18.00 THROW 51020, 'D001 completed sales amount is incorrect.', 1;
IF DATABASE_PRINCIPAL_ID(N'shop_clerk') IS NULL OR DATABASE_PRINCIPAL_ID(N'shop_manager') IS NULL
    THROW 51021, 'Expected demo roles are missing.', 1;

SELECT N'PASS' AS acceptance, @table_count AS dbo_tables,
       (SELECT COUNT(*) FROM dbo.vw_OrderDetail) AS order_detail_view_rows,
       (SELECT COUNT(*) FROM dbo.vw_ProductSales) AS product_sales_view_rows,
       (SELECT COUNT(*) FROM dbo.vw_InventoryStatus) AS inventory_view_rows,
       (SELECT COUNT(*) FROM dbo.Product WHERE ProductCode = 'D999') AS temporary_products;

SELECT d.name, d.state_desc, d.compatibility_level,
       CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(30)) AS engine_version
FROM sys.databases AS d WHERE d.name = DB_NAME();
GO
