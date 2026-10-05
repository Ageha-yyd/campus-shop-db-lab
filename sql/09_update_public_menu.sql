USE [MilkTeaShopV01];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

-- 更新已有的阶段一样例库到公开菜单参考价。
-- 仅适用于本项目的三款 D001-D003 和固定 MT-20261005-* 虚构样例订单。
DECLARE @Menu TABLE (
    ProductCode varchar(12) NOT NULL PRIMARY KEY,
    ProductName nvarchar(80) NOT NULL,
    Category nvarchar(30) NOT NULL,
    UnitPrice decimal(10,2) NOT NULL
);
INSERT @Menu (ProductCode, ProductName, Category, UnitPrice) VALUES
('D001', N'珍珠奶茶', N'奶茶', 6.00),
('D002', N'满杯百香果', N'果茶', 7.00),
('D003', N'冰鲜柠檬水', N'柠檬饮品', 4.00);

IF (SELECT COUNT(*) FROM dbo.Product) <> 3
    THROW 51030, 'Expected the three-row course sample Product baseline; no rows were changed.', 1;
IF EXISTS (
    SELECT ProductCode FROM @Menu
    EXCEPT
    SELECT ProductCode FROM dbo.Product
)
    THROW 51031, 'Expected sample product codes D001-D003; no rows were changed.', 1;
IF (SELECT COUNT(*) FROM dbo.ShopOrder WHERE OrderNo IN
    ('MT-20261005-001','MT-20261005-002','MT-20261005-003')) <> 3
    THROW 51032, 'Expected the three fixed sample orders; no rows were changed.', 1;
IF (SELECT COUNT(*) FROM dbo.OrderLine WHERE OrderNo IN
    ('MT-20261005-001','MT-20261005-002','MT-20261005-003')) <> 4
    THROW 51033, 'Expected four fixed sample order lines; no rows were changed.', 1;

BEGIN TRANSACTION;

UPDATE p
SET p.ProductName = m.ProductName,
    p.Category = m.Category,
    p.UnitPrice = m.UnitPrice
FROM dbo.Product AS p
JOIN @Menu AS m ON m.ProductCode = p.ProductCode;
IF @@ROWCOUNT <> 3 THROW 51034, 'Expected to update three menu products.', 1;

UPDATE l
SET l.UnitPrice = m.UnitPrice
FROM dbo.OrderLine AS l
JOIN dbo.ShopOrder AS o ON o.OrderNo = l.OrderNo
JOIN @Menu AS m ON m.ProductCode = l.ProductCode
WHERE o.OrderNo IN ('MT-20261005-001','MT-20261005-002','MT-20261005-003');
IF @@ROWCOUNT <> 4 THROW 51035, 'Expected to update four sample sale-price snapshots.', 1;

COMMIT TRANSACTION;

SELECT ProductCode, ProductName, Category, UnitPrice
FROM dbo.Product
ORDER BY ProductCode;
SELECT o.OrderNo, l.LineNumber, p.ProductName, l.Quantity, l.UnitPrice,
       CONVERT(decimal(12,2), l.Quantity * l.UnitPrice) AS line_amount
FROM dbo.ShopOrder AS o
JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
JOIN dbo.Product AS p ON p.ProductCode = l.ProductCode
WHERE o.OrderNo IN ('MT-20261005-001','MT-20261005-002','MT-20261005-003')
ORDER BY o.OrderNo, l.LineNumber;
GO
