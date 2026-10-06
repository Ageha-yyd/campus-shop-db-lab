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
DECLARE @before_products int = (SELECT COUNT(*) FROM dbo.Product);
DECLARE @before_inventory int = (SELECT COUNT(*) FROM dbo.Inventory);
DECLARE @before_orders int = (SELECT COUNT(*) FROM dbo.ShopOrder);
DECLARE @before_lines int = (SELECT COUNT(*) FROM dbo.OrderLine);
BEGIN TRANSACTION;

-- Product CREATE + READ: 新增实验商品并查看初始值。
INSERT INTO dbo.Product (ProductCode, ProductName, Category, UnitPrice)
VALUES ('D999', N'实验用试饮奶茶', N'实验', 2.00);
SELECT ProductCode, ProductName, UnitPrice, RestockThreshold FROM dbo.Product WHERE ProductCode = 'D999';

-- Product UPDATE + READ: 调整菜单名称与标价，再查询确认。
UPDATE dbo.Product
SET ProductName = N'实验用经典奶茶', UnitPrice = 2.50, RestockThreshold = 6
WHERE ProductCode = 'D999';
SELECT ProductCode, ProductName, UnitPrice, RestockThreshold FROM dbo.Product WHERE ProductCode = 'D999';

-- Inventory CREATE + READ: 为商品创建可售杯数快照并查看。
INSERT INTO dbo.Inventory (ProductCode, Quantity) VALUES ('D999', 0);
SELECT ProductCode, Quantity FROM dbo.Inventory WHERE ProductCode = 'D999';

-- Inventory UPDATE + READ: 更新库存快照并检查受影响行。
UPDATE dbo.Inventory SET Quantity = 7, UpdatedAt = SYSUTCDATETIME() WHERE ProductCode = 'D999';
SELECT ProductCode, Quantity FROM dbo.Inventory WHERE ProductCode = 'D999';

-- ShopOrder CREATE + READ: 新增订单并读取其状态。
INSERT INTO dbo.ShopOrder (OrderNo, EmployeeCode, MemberCode, Status)
VALUES ('MT-CRUD-ROLLBACK', 'E001', NULL, 'COMPLETED');
SELECT OrderNo, Status, EmployeeCode, MemberCode
FROM dbo.ShopOrder WHERE OrderNo = 'MT-CRUD-ROLLBACK';

-- ShopOrder UPDATE + READ: 演示取消状态变更，然后恢复为完成单以继续明细演示。
UPDATE dbo.ShopOrder SET Status = 'CANCELLED' WHERE OrderNo = 'MT-CRUD-ROLLBACK';
SELECT OrderNo, Status FROM dbo.ShopOrder WHERE OrderNo = 'MT-CRUD-ROLLBACK';
UPDATE dbo.ShopOrder SET Status = 'COMPLETED' WHERE OrderNo = 'MT-CRUD-ROLLBACK';
SELECT OrderNo, Status FROM dbo.ShopOrder WHERE OrderNo = 'MT-CRUD-ROLLBACK';

-- OrderLine CREATE + READ: 新增明细并用连接确认订单、商品与金额。
INSERT INTO dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice)
VALUES ('MT-CRUD-ROLLBACK', 1, 'D999', 2, 2.50);
SELECT o.OrderNo, p.ProductName, l.Quantity, l.UnitPrice,
       CONVERT(decimal(12,2), l.Quantity * l.UnitPrice) AS line_amount
FROM dbo.ShopOrder AS o
JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
JOIN dbo.Product AS p ON p.ProductCode = l.ProductCode
WHERE o.OrderNo = 'MT-CRUD-ROLLBACK';

-- OrderLine UPDATE + READ: 调整本实验订单的杯数，再确认金额随之变化。
UPDATE dbo.OrderLine
SET Quantity = 3
WHERE OrderNo = 'MT-CRUD-ROLLBACK' AND LineNumber = 1;
SELECT OrderNo, LineNumber, Quantity, UnitPrice,
       CONVERT(decimal(12,2), Quantity * UnitPrice) AS line_amount
FROM dbo.OrderLine WHERE OrderNo = 'MT-CRUD-ROLLBACK' AND LineNumber = 1;

-- DELETE: 先核对目标，再按外键依赖的反方向删除。
SELECT OrderNo, LineNumber FROM dbo.OrderLine WHERE OrderNo = 'MT-CRUD-ROLLBACK';
DELETE dbo.OrderLine WHERE OrderNo = 'MT-CRUD-ROLLBACK';
SELECT @@ROWCOUNT AS deleted_order_lines;
SELECT OrderNo FROM dbo.ShopOrder WHERE OrderNo = 'MT-CRUD-ROLLBACK';
DELETE dbo.ShopOrder WHERE OrderNo = 'MT-CRUD-ROLLBACK';
SELECT @@ROWCOUNT AS deleted_orders;
SELECT ProductCode, Quantity FROM dbo.Inventory WHERE ProductCode = 'D999';
DELETE dbo.Inventory WHERE ProductCode = 'D999';
SELECT @@ROWCOUNT AS deleted_inventory_rows;
SELECT ProductCode, ProductName FROM dbo.Product WHERE ProductCode = 'D999';
DELETE dbo.Product WHERE ProductCode = 'D999';
SELECT @@ROWCOUNT AS deleted_product_rows;
SELECT COUNT(*) AS temporary_product_rows_after_delete
FROM dbo.Product WHERE ProductCode = 'D999';

ROLLBACK TRANSACTION;
IF (SELECT COUNT(*) FROM dbo.Product) <> @before_products
   OR (SELECT COUNT(*) FROM dbo.Inventory) <> @before_inventory
   OR (SELECT COUNT(*) FROM dbo.ShopOrder) <> @before_orders
   OR (SELECT COUNT(*) FROM dbo.OrderLine) <> @before_lines
   OR EXISTS (SELECT 1 FROM dbo.Product WHERE ProductCode = 'D999')
   OR EXISTS (SELECT 1 FROM dbo.ShopOrder WHERE OrderNo = 'MT-CRUD-ROLLBACK')
    THROW 51003, 'CRUD did not restore the baseline.', 1;
SELECT COUNT(*) AS temporary_product_rows_after_rollback
FROM dbo.Product WHERE ProductCode = 'D999';
SELECT COUNT(*) AS baseline_product_rows FROM dbo.Product;
GO
