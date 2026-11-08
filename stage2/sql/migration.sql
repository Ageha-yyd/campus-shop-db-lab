-- v0.1 -> v1.0. Execute ONLY in an independent restored copy. Never drop/reseed v0.1.
-- Single transaction: a failed migration rolls back all schema/data changes.
SET XACT_ABORT ON;
SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_WARNINGS ON;
SET ANSI_PADDING ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
BEGIN TRANSACTION;
IF OBJECT_ID('dbo.SchemaVersion') IS NOT NULL THROW 51000, 'Already migrated; use a fresh v0.1 copy.', 1;
IF (SELECT COUNT(*) FROM dbo.Product) <> 6 OR (SELECT COUNT(*) FROM dbo.ShopOrder) <> 7
 THROW 51001, 'Unexpected baseline; review source data before migration.', 1;
IF EXISTS (SELECT OrderNo,LineNumber FROM dbo.OrderLine GROUP BY OrderNo,LineNumber HAVING COUNT(*)>1)
 THROW 51002, 'Duplicate order line identity.', 1;
IF EXISTS (SELECT 1 FROM dbo.ShopOrder o WHERE NOT EXISTS(SELECT 1 FROM dbo.OrderLine l WHERE l.OrderNo=o.OrderNo))
 THROW 51003, 'Baseline contains an empty order.', 1;
-- Persist exact before results inside the migration copy for EXCEPT comparisons.
SELECT * INTO dbo.Baseline_OrderDetail FROM dbo.vw_OrderDetail;
SELECT * INTO dbo.Baseline_ProductSales FROM dbo.vw_ProductSales;
SELECT * INTO dbo.Baseline_Inventory FROM dbo.Inventory;
SELECT * INTO dbo.Baseline_Product FROM dbo.Product;
SELECT * INTO dbo.Baseline_Member FROM dbo.Member;
SELECT * INTO dbo.Baseline_Employee FROM dbo.Employee;
SELECT * INTO dbo.Baseline_ShopOrder FROM dbo.ShopOrder;
SELECT * INTO dbo.Baseline_OrderLine FROM dbo.OrderLine;
-- Category is an atomic classification value, with no additional category attributes.
-- Six existing business relations already meet BCNF under documented dependencies.
-- Preserve current prices, historical line prices and opening inventory snapshots.
CREATE TABLE dbo.AppUser(
 UserId int IDENTITY CONSTRAINT PK_AppUser PRIMARY KEY,
 Username varchar(40) NOT NULL CONSTRAINT UQ_AppUser_Username UNIQUE,
 PasswordHash varchar(255) NOT NULL,
 Role varchar(12) NOT NULL CONSTRAINT CK_AppUser_Role CHECK(Role IN('admin','clerk','customer')),
 EmployeeCode varchar(12) NULL CONSTRAINT FK_AppUser_Employee REFERENCES dbo.Employee(EmployeeCode),
 MemberCode varchar(12) NULL CONSTRAINT FK_AppUser_Member REFERENCES dbo.Member(MemberCode),
 IsActive bit NOT NULL CONSTRAINT DF_AppUser_Active DEFAULT(1),
 CONSTRAINT CK_AppUser_Profile CHECK(
  (Role IN('admin','clerk') AND EmployeeCode IS NOT NULL AND MemberCode IS NULL) OR
  (Role='customer' AND EmployeeCode IS NULL))
);
CREATE UNIQUE INDEX UX_AppUser_Employee ON dbo.AppUser(EmployeeCode) WHERE EmployeeCode IS NOT NULL;
CREATE UNIQUE INDEX UX_AppUser_Member ON dbo.AppUser(MemberCode) WHERE MemberCode IS NOT NULL;
ALTER TABLE dbo.ShopOrder ADD CreatedByUserId int NULL CONSTRAINT FK_ShopOrder_AppUser REFERENCES dbo.AppUser(UserId),
 StockApplied bit NOT NULL CONSTRAINT DF_ShopOrder_StockApplied DEFAULT(0);
ALTER TABLE dbo.ShopOrder ALTER COLUMN EmployeeCode varchar(12) NULL;
ALTER TABLE dbo.ShopOrder DROP CONSTRAINT CK_ShopOrder_Status;
ALTER TABLE dbo.ShopOrder ADD CONSTRAINT CK_ShopOrder_Status CHECK(Status IN('DRAFT','COMPLETED','CANCELLED'));
ALTER TABLE dbo.ShopOrder DROP CONSTRAINT DF_ShopOrder_Status;
ALTER TABLE dbo.ShopOrder ADD CONSTRAINT DF_ShopOrder_Status DEFAULT('DRAFT') FOR Status;
-- Imported orders predate the opening inventory snapshot: never deduct them again.
CREATE TABLE dbo.SchemaVersion(Version varchar(12) NOT NULL PRIMARY KEY, AppliedAt datetime2 NOT NULL DEFAULT SYSUTCDATETIME());
INSERT dbo.SchemaVersion(Version) VALUES('1.0');
COMMIT;
PRINT 'PASS migration: 6 business tables preserved; AppUser and SchemaVersion added';
