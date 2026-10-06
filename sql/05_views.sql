SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO
CREATE OR ALTER VIEW dbo.vw_OrderDetail AS
SELECT o.OrderNo, o.OrderedAt, o.Status, e.EmployeeCode, e.DisplayName AS EmployeeName,
       o.MemberCode, COALESCE(m.DisplayName, N'匿名顾客') AS MemberName,
       l.LineNumber, p.ProductCode, p.ProductName, l.Quantity, l.UnitPrice,
       CONVERT(decimal(12,2), l.Quantity * l.UnitPrice) AS LineAmount
FROM dbo.ShopOrder AS o
JOIN dbo.Employee AS e ON e.EmployeeCode = o.EmployeeCode
LEFT JOIN dbo.Member AS m ON m.MemberCode = o.MemberCode
JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
JOIN dbo.Product AS p ON p.ProductCode = l.ProductCode;
GO
CREATE OR ALTER VIEW dbo.vw_ProductSales AS
SELECT p.ProductCode, p.ProductName,
       COALESCE(SUM(CASE WHEN o.Status = 'COMPLETED' THEN l.Quantity ELSE 0 END), 0) AS UnitsSold,
       COALESCE(SUM(CASE WHEN o.Status = 'COMPLETED' THEN l.Quantity * l.UnitPrice ELSE 0 END), 0) AS SalesAmount
FROM dbo.Product AS p
LEFT JOIN dbo.OrderLine AS l ON l.ProductCode = p.ProductCode
LEFT JOIN dbo.ShopOrder AS o ON o.OrderNo = l.OrderNo
GROUP BY p.ProductCode, p.ProductName;
GO
CREATE OR ALTER VIEW dbo.vw_InventoryStatus AS
SELECT p.ProductCode, p.ProductName, p.IsActive, p.RestockThreshold,
       i.Quantity AS OnHand, i.UpdatedAt,
       CASE WHEN i.ProductCode IS NULL THEN N'未登记'
            WHEN i.Quantity = 0 THEN N'缺货'
            WHEN i.Quantity <= p.RestockThreshold THEN N'低库存'
            ELSE N'有库存' END AS StockStatus,
       CASE WHEN i.ProductCode IS NULL THEN NULL
            WHEN i.Quantity <= p.RestockThreshold
            THEN CONVERT(bigint, p.RestockThreshold) * 2 - i.Quantity
            ELSE CONVERT(bigint, 0) END AS SuggestedPreparationCups
FROM dbo.Product AS p
LEFT JOIN dbo.Inventory AS i ON i.ProductCode = p.ProductCode;
GO
CREATE OR ALTER VIEW dbo.vw_MemberConsumption AS
SELECT m.MemberCode, m.DisplayName,
       COUNT(DISTINCT o.OrderNo) AS CompletedOrders,
       COALESCE(SUM(l.Quantity), 0) AS CupsPurchased,
       CONVERT(decimal(12,2), COALESCE(SUM(l.Quantity * l.UnitPrice), 0)) AS CompletedAmount
FROM dbo.Member AS m
LEFT JOIN dbo.ShopOrder AS o ON o.MemberCode = m.MemberCode AND o.Status = 'COMPLETED'
LEFT JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
GROUP BY m.MemberCode, m.DisplayName;
GO
SELECT * FROM dbo.vw_OrderDetail ORDER BY OrderNo, LineNumber;
SELECT * FROM dbo.vw_ProductSales ORDER BY ProductCode;
SELECT ProductCode, ProductName, OnHand, RestockThreshold, StockStatus, SuggestedPreparationCups
FROM dbo.vw_InventoryStatus ORDER BY ProductCode;
SELECT * FROM dbo.vw_MemberConsumption ORDER BY MemberCode;
GO
