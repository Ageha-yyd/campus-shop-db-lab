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

GRANT SELECT ON dbo.vw_MemberConsumption TO shop_manager;

-- 会员/顾客不直接连接数据库；会员汇总只授权给店长。
CREATE TABLE #RoleResults (TestCase nvarchar(60), EffectiveUser sysname, Outcome varchar(12), RowsAffected int, ErrorNumber int);
DECLARE @rows int, @rows2 int, @error int, @message nvarchar(400), @effective_user sysname;

EXECUTE AS USER='course_clerk_demo';
SELECT @effective_user=USER_NAME(), @rows=COUNT(*) FROM dbo.Product;
SELECT @rows2=COUNT(*) FROM dbo.vw_ProductSales;
REVERT;
IF @rows<>6 OR @rows2<>6 THROW 51070, 'Clerk catalog/view access failed.', 1;
INSERT #RoleResults VALUES (N'clerk reads catalog and sales',@effective_user,'ALLOWED',@rows,0);

BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
INSERT dbo.ShopOrder (OrderNo,EmployeeCode,MemberCode) VALUES ('MT-ROLE-ROLLBACK','E001',NULL);
SET @rows=@@ROWCOUNT;
INSERT dbo.OrderLine VALUES ('MT-ROLE-ROLLBACK',1,'D001',1,6.00);
SET @rows2=@@ROWCOUNT;
REVERT;
ROLLBACK;
IF @rows<>1 OR @rows2<>1 THROW 51071, 'Clerk order/line insert failed.', 1;
INSERT #RoleResults VALUES (N'clerk inserts order','course_clerk_demo','ALLOWED',@rows,0);
INSERT #RoleResults VALUES (N'clerk inserts order line','course_clerk_demo','ALLOWED',@rows2,0);

SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
BEGIN TRY
    UPDATE dbo.Product SET UnitPrice=UnitPrice WHERE ProductCode='D001';
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=ERROR_MESSAGE();
END CATCH;
REVERT;
IF XACT_STATE()<>0 ROLLBACK;
IF @error<>229 THROW 51072, 'Expected permission error 229: clerk changes menu price.', 1;
INSERT #RoleResults VALUES (N'clerk changes menu price','course_clerk_demo','REJECTED',0,@error);

SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
BEGIN TRY
    DELETE dbo.Product WHERE ProductCode='D003';
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=ERROR_MESSAGE();
END CATCH;
REVERT;
IF XACT_STATE()<>0 ROLLBACK;
IF @error<>229 THROW 51072, 'Expected permission error 229: clerk deletes product.', 1;
INSERT #RoleResults VALUES (N'clerk deletes product','course_clerk_demo','REJECTED',0,@error);

SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
BEGIN TRY
    UPDATE dbo.Inventory SET Quantity=Quantity WHERE ProductCode='D001';
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=ERROR_MESSAGE();
END CATCH;
REVERT;
IF XACT_STATE()<>0 ROLLBACK;
IF @error<>229 THROW 51072, 'Expected permission error 229: clerk changes inventory.', 1;
INSERT #RoleResults VALUES (N'clerk changes inventory','course_clerk_demo','REJECTED',0,@error);

SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
BEGIN TRY
    SELECT @rows=COUNT(*) FROM dbo.Employee;
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=ERROR_MESSAGE();
END CATCH;
REVERT;
IF XACT_STATE()<>0 ROLLBACK;
IF @error<>229 THROW 51072, 'Expected permission error 229: clerk reads employee table.', 1;
INSERT #RoleResults VALUES (N'clerk reads employee table','course_clerk_demo','REJECTED',0,@error);

SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
BEGIN TRY
    SELECT @rows=COUNT(*) FROM dbo.Member;
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=ERROR_MESSAGE();
END CATCH;
REVERT;
IF XACT_STATE()<>0 ROLLBACK;
IF @error<>229 THROW 51072, 'Expected permission error 229: clerk reads member contacts.', 1;
INSERT #RoleResults VALUES (N'clerk reads member contacts','course_clerk_demo','REJECTED',0,@error);

SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
EXECUTE AS USER='course_clerk_demo';
BEGIN TRY
    SELECT @rows=COUNT(*) FROM dbo.vw_MemberConsumption;
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=ERROR_MESSAGE();
END CATCH;
REVERT;
IF XACT_STATE()<>0 ROLLBACK;
IF @error<>229 THROW 51072, 'Expected permission error 229: clerk reads manager member report.', 1;
INSERT #RoleResults VALUES (N'clerk reads manager member report','course_clerk_demo','REJECTED',0,@error);

BEGIN TRANSACTION;
EXECUTE AS USER='course_manager_demo';
UPDATE dbo.Product SET RestockThreshold=RestockThreshold WHERE ProductCode='D001';
SET @rows=@@ROWCOUNT;
UPDATE dbo.Inventory SET Quantity=Quantity WHERE ProductCode='D001';
SET @rows2=@@ROWCOUNT;
SELECT @effective_user=USER_NAME(), @error=COUNT(*) FROM dbo.vw_MemberConsumption;
REVERT;
ROLLBACK;
IF @rows<>1 OR @rows2<>1 OR @error<>4 THROW 51073, 'Manager maintenance/report access failed.', 1;
INSERT #RoleResults VALUES (N'manager maintains preparation threshold',@effective_user,'ALLOWED',@rows,0);
INSERT #RoleResults VALUES (N'manager maintains inventory snapshot',@effective_user,'ALLOWED',@rows2,0);
INSERT #RoleResults VALUES (N'manager reads member report',@effective_user,'ALLOWED',@error,0);
IF EXISTS (SELECT 1 FROM dbo.ShopOrder WHERE OrderNo='MT-ROLE-ROLLBACK')
    THROW 51074, 'Role tests left a temporary order.', 1;
SELECT * FROM #RoleResults;
SELECT N'PASS' AS role_verification, COUNT(*) AS cases_checked FROM #RoleResults;
GO
