SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

-- 可重复的 CRUD 演示：所有改动都在最后回滚，保持样例基线不变。
BEGIN TRANSACTION;

-- CREATE + READ: 新增商品及其库存快照。
INSERT INTO dbo.Product (ProductCode, ProductName, Category, UnitPrice)
VALUES ('P999', N'实验用苏打水', N'实验', 2.00);
INSERT INTO dbo.Inventory (ProductCode, Quantity) VALUES ('P999', 0);
SELECT ProductCode, ProductName, UnitPrice FROM dbo.Product WHERE ProductCode = 'P999';

-- UPDATE + READ: 更新库存快照并检查受影响行。
UPDATE dbo.Inventory SET Quantity = 7, UpdatedAt = SYSUTCDATETIME() WHERE ProductCode = 'P999';
SELECT ProductCode, Quantity FROM dbo.Inventory WHERE ProductCode = 'P999';

-- 新增订单与明细后用连接确认业务记录。
INSERT INTO dbo.ShopOrder (OrderNo, EmployeeCode, MemberCode, Status)
VALUES ('CS-CRUD-ROLLBACK', 'E001', NULL, 'COMPLETED');
INSERT INTO dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice)
VALUES ('CS-CRUD-ROLLBACK', 1, 'P999', 2, 2.00);
SELECT o.OrderNo, p.ProductName, l.Quantity, l.UnitPrice,
       CONVERT(decimal(12,2), l.Quantity * l.UnitPrice) AS line_amount
FROM dbo.ShopOrder AS o
JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
JOIN dbo.Product AS p ON p.ProductCode = l.ProductCode
WHERE o.OrderNo = 'CS-CRUD-ROLLBACK';

-- DELETE: 先用相同条件核对目标，再按外键依赖的反方向删除。
SELECT OrderNo, LineNumber FROM dbo.OrderLine WHERE OrderNo = 'CS-CRUD-ROLLBACK';
DELETE dbo.OrderLine WHERE OrderNo = 'CS-CRUD-ROLLBACK';
SELECT @@ROWCOUNT AS deleted_order_lines;
SELECT OrderNo FROM dbo.ShopOrder WHERE OrderNo = 'CS-CRUD-ROLLBACK';
DELETE dbo.ShopOrder WHERE OrderNo = 'CS-CRUD-ROLLBACK';
SELECT @@ROWCOUNT AS deleted_orders;
DELETE dbo.Inventory WHERE ProductCode = 'P999';
DELETE dbo.Product WHERE ProductCode = 'P999';
SELECT COUNT(*) AS temporary_product_rows_after_delete
FROM dbo.Product WHERE ProductCode = 'P999';

ROLLBACK TRANSACTION;
SELECT COUNT(*) AS temporary_product_rows_after_rollback
FROM dbo.Product WHERE ProductCode = 'P999';
SELECT COUNT(*) AS baseline_product_rows FROM dbo.Product;
GO
