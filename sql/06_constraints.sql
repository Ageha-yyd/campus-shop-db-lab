SET NOCOUNT ON;
SET XACT_ABORT OFF;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

-- 合法对照数据：有效商品及库存能够写入；最后回滚。
BEGIN TRANSACTION;
INSERT dbo.Product (ProductCode, ProductName, Category, UnitPrice)
VALUES ('D998', N'合法约束测试商品', N'测试', 1.00);
INSERT dbo.Inventory (ProductCode, Quantity) VALUES ('D998', 0);
SELECT ProductCode, Quantity FROM dbo.Inventory WHERE ProductCode = 'D998';
ROLLBACK TRANSACTION;

-- CHECK：负库存应失败。
BEGIN TRY
    BEGIN TRANSACTION;
    INSERT dbo.Inventory (ProductCode, Quantity) VALUES ('D998', -1);
    ROLLBACK TRANSACTION;
    PRINT 'UNEXPECTED SUCCESS: negative inventory';
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    SELECT N'REJECTED: negative inventory' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- CHECK：非正商品标价应失败。
BEGIN TRY
    INSERT dbo.Product (ProductCode, ProductName, Category, UnitPrice)
    VALUES ('D997', N'非法价格测试', N'测试', 0.00);
    PRINT 'UNEXPECTED SUCCESS: zero price';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: zero product price' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- 主键：重复订单号应失败。
BEGIN TRY
    INSERT dbo.ShopOrder (OrderNo, EmployeeCode, MemberCode, Status)
    VALUES ('MT-20261005-001', 'E001', NULL, 'COMPLETED');
    PRINT 'UNEXPECTED SUCCESS: duplicate order number';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: duplicate order number' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- UNIQUE 候选码：重复非空手机号应失败。
BEGIN TRY
    INSERT dbo.Member (MemberCode, DisplayName, Phone)
    VALUES ('M999', N'重复手机号测试', '13800000001');
    PRINT 'UNEXPECTED SUCCESS: duplicate phone';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: duplicate member phone' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- FK：订单明细引用不存在订单应失败。
BEGIN TRY
    INSERT dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice)
    VALUES ('NO-SUCH-ORDER', 1, 'D001', 1, 6.00);
    PRINT 'UNEXPECTED SUCCESS: orphan order line';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: orphan order line' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

-- CHECK：非正购买数量应失败。
BEGIN TRY
    INSERT dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice)
    VALUES ('MT-20261005-001', 9, 'D001', 0, 6.00);
    PRINT 'UNEXPECTED SUCCESS: zero line quantity';
END TRY
BEGIN CATCH
    SELECT N'REJECTED: zero line quantity' AS test_case, ERROR_NUMBER() AS error_number, CAST(LEFT(ERROR_MESSAGE(), 300) AS nvarchar(300)) AS error_message;
END CATCH;

SELECT (SELECT COUNT(*) FROM dbo.Product WHERE ProductCode IN ('D997','D998')) AS test_products_remaining,
       (SELECT COUNT(*) FROM dbo.Member WHERE MemberCode = 'M999') AS test_members_remaining,
       (SELECT COUNT(*) FROM dbo.OrderLine WHERE OrderNo = 'NO-SUCH-ORDER') AS orphan_lines_remaining;
GO
