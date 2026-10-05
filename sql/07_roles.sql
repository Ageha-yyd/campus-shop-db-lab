SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

IF DATABASE_PRINCIPAL_ID(N'shop_clerk') IS NULL CREATE ROLE shop_clerk AUTHORIZATION dbo;
IF DATABASE_PRINCIPAL_ID(N'shop_manager') IS NULL CREATE ROLE shop_manager AUTHORIZATION dbo;
IF DATABASE_PRINCIPAL_ID(N'course_clerk_demo') IS NULL CREATE USER course_clerk_demo WITHOUT LOGIN;
IF DATABASE_PRINCIPAL_ID(N'course_manager_demo') IS NULL CREATE USER course_manager_demo WITHOUT LOGIN;
IF NOT EXISTS (SELECT 1 FROM sys.database_role_members WHERE role_principal_id = DATABASE_PRINCIPAL_ID(N'shop_clerk') AND member_principal_id = DATABASE_PRINCIPAL_ID(N'course_clerk_demo'))
    ALTER ROLE shop_clerk ADD MEMBER course_clerk_demo;
IF NOT EXISTS (SELECT 1 FROM sys.database_role_members WHERE role_principal_id = DATABASE_PRINCIPAL_ID(N'shop_manager') AND member_principal_id = DATABASE_PRINCIPAL_ID(N'course_manager_demo'))
    ALTER ROLE shop_manager ADD MEMBER course_manager_demo;

GRANT SELECT ON dbo.Product TO shop_clerk;
GRANT SELECT ON dbo.Inventory TO shop_clerk;
GRANT SELECT ON dbo.vw_OrderDetail TO shop_clerk;
GRANT SELECT ON dbo.vw_ProductSales TO shop_clerk;
GRANT SELECT ON dbo.vw_InventoryStatus TO shop_clerk;
GRANT INSERT ON dbo.ShopOrder TO shop_clerk;
GRANT INSERT ON dbo.OrderLine TO shop_clerk;

GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Product TO shop_manager;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Inventory TO shop_manager;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Member TO shop_manager;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Employee TO shop_manager;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.ShopOrder TO shop_manager;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.OrderLine TO shop_manager;
GRANT SELECT ON dbo.vw_OrderDetail TO shop_manager;
GRANT SELECT ON dbo.vw_ProductSales TO shop_manager;
GRANT SELECT ON dbo.vw_InventoryStatus TO shop_manager;

PRINT 'shop_clerk: read catalog/inventory/views and insert orders; no direct price/inventory/employee maintenance.';
PRINT 'shop_manager: maintenance on the six named business tables and read access to views.';

-- 店员：允许查询商品与视图。
EXECUTE AS USER = 'course_clerk_demo';
SELECT USER_NAME() AS effective_user, COUNT(*) AS visible_products FROM dbo.Product;
SELECT USER_NAME() AS effective_user, COUNT(*) AS visible_sales_rows FROM dbo.vw_ProductSales;

-- 店员：可以创建订单头；用回滚避免改变固定样例。
BEGIN TRANSACTION;
INSERT INTO dbo.ShopOrder (OrderNo, EmployeeCode, MemberCode, Status)
VALUES ('MT-ROLE-ROLLBACK', 'E001', NULL, 'COMPLETED');
SELECT N'ALLOWED: clerk order insert' AS test_case, @@ROWCOUNT AS inserted_rows;
ROLLBACK TRANSACTION;

-- 店员：不能改商品定价。
BEGIN TRY
    UPDATE dbo.Product SET UnitPrice = UnitPrice WHERE ProductCode = 'D001';
    PRINT 'UNEXPECTED SUCCESS: clerk changed product';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: clerk product update' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- 店员：不能读取员工表。
BEGIN TRY
    SELECT COUNT(*) AS employee_count FROM dbo.Employee;
    PRINT 'UNEXPECTED SUCCESS: clerk read employee table';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: clerk employee read' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- 店员：不能删除商品目录数据。
BEGIN TRY
    DELETE dbo.Product WHERE ProductCode = 'D003';
    PRINT 'UNEXPECTED SUCCESS: clerk deleted product';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: clerk product delete' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;
REVERT;

-- 店长：同一商品维护操作允许执行，但写入相同值，不改变数据。
EXECUTE AS USER = 'course_manager_demo';
UPDATE dbo.Product SET UnitPrice = UnitPrice WHERE ProductCode = 'D001';
SELECT USER_NAME() AS effective_user, @@ROWCOUNT AS manager_update_rows;
REVERT;
GO
