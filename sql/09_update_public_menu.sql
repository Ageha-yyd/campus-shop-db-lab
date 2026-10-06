SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
SET XACT_ABORT ON;
-- 仅适用于本项目六款固定饮品。只对齐菜单目录，不修改任何历史成交价快照。
DECLARE @Menu TABLE (ProductCode varchar(12) PRIMARY KEY, ProductName nvarchar(80), Category nvarchar(30), UnitPrice decimal(10,2));
INSERT @Menu VALUES
('D001',N'珍珠奶茶',N'奶茶',6.00),
('D002',N'满杯百香果',N'果茶',7.00),
('D003',N'冰鲜柠檬水',N'柠檬饮品',4.00),
('D004',N'椰果奶茶',N'奶茶',7.00),
('D005',N'柠檬红茶',N'果茶',5.00),
('D006',N'茉莉绿茶',N'纯茶',4.00);
IF (SELECT COUNT(*) FROM dbo.Product) <> 6
   OR EXISTS (SELECT ProductCode FROM @Menu EXCEPT SELECT ProductCode FROM dbo.Product)
    THROW 51030, 'Expected six fixed sample products; no menu rows were changed.', 1;
BEGIN TRANSACTION;
UPDATE p SET ProductName=m.ProductName,Category=m.Category,UnitPrice=m.UnitPrice
FROM dbo.Product p JOIN @Menu m ON m.ProductCode=p.ProductCode;
IF @@ROWCOUNT <> 6
BEGIN
    ROLLBACK;
    THROW 51031, 'Expected to align six menu rows.', 1;
END;
COMMIT;
SELECT ProductCode,ProductName,UnitPrice,RestockThreshold FROM dbo.Product ORDER BY ProductCode;
SELECT N'historical sale-price snapshots preserved' AS note;
GO
