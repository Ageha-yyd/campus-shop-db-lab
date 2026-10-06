SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

-- 1. 明细级查询：每行是一张订单中的一个商品行，只统计完成订单。
SELECT o.OrderNo, o.OrderedAt, e.DisplayName AS clerk,
       COALESCE(m.DisplayName, N'匿名顾客') AS customer,
       p.ProductName, l.Quantity, l.UnitPrice,
       CONVERT(decimal(12,2), l.Quantity * l.UnitPrice) AS line_amount
FROM dbo.ShopOrder AS o
JOIN dbo.Employee AS e ON e.EmployeeCode = o.EmployeeCode
LEFT JOIN dbo.Member AS m ON m.MemberCode = o.MemberCode
JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
JOIN dbo.Product AS p ON p.ProductCode = l.ProductCode
WHERE o.Status = 'COMPLETED'
ORDER BY o.OrderedAt, o.OrderNo, l.LineNumber;

-- 2. 每个商品一行；LEFT JOIN 保留完成订单中零销量的商品。
SELECT p.ProductCode, p.ProductName,
       COALESCE(SUM(CASE WHEN o.Status = 'COMPLETED' THEN l.Quantity ELSE 0 END), 0) AS units_sold,
       COALESCE(SUM(CASE WHEN o.Status = 'COMPLETED' THEN l.Quantity * l.UnitPrice ELSE 0 END), 0) AS sales_amount
FROM dbo.Product AS p
LEFT JOIN dbo.OrderLine AS l ON l.ProductCode = p.ProductCode
LEFT JOIN dbo.ShopOrder AS o ON o.OrderNo = l.OrderNo
GROUP BY p.ProductCode, p.ProductName
ORDER BY p.ProductCode;

-- 3. 只显示完成订单累计金额不少于 10 元的会员（HAVING）。
SELECT m.MemberCode, m.DisplayName,
       SUM(l.Quantity * l.UnitPrice) AS completed_amount
FROM dbo.Member AS m
JOIN dbo.ShopOrder AS o ON o.MemberCode = m.MemberCode AND o.Status = 'COMPLETED'
JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
GROUP BY m.MemberCode, m.DisplayName
HAVING SUM(l.Quantity * l.UnitPrice) >= 10.00;

-- 4. 子查询：查询高于当前商品平均标价的启用商品。
SELECT ProductCode, ProductName, UnitPrice
FROM dbo.Product
WHERE IsActive = 1
  AND UnitPrice > (SELECT AVG(UnitPrice) FROM dbo.Product WHERE IsActive = 1)
ORDER BY UnitPrice DESC;

-- 5. 订单头统计；金额从明细计算，避免把订单总额重复到每个明细行。
SELECT o.OrderNo, COUNT(l.LineNumber) AS line_count,
       COALESCE(SUM(l.Quantity), 0) AS item_count,
       COALESCE(SUM(l.Quantity * l.UnitPrice), 0) AS order_amount
FROM dbo.ShopOrder AS o
LEFT JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
WHERE o.Status = 'COMPLETED'
GROUP BY o.OrderNo
ORDER BY o.OrderNo;

-- 6. 按每款饮品阈值计算建议补足杯数；这不是采购或自动制作操作。
;WITH InventoryStatus AS (
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
LEFT JOIN dbo.Inventory AS i ON i.ProductCode = p.ProductCode
)
SELECT ProductCode, ProductName, OnHand, RestockThreshold, StockStatus, SuggestedPreparationCups
FROM InventoryStatus
WHERE OnHand <= RestockThreshold AND IsActive = 1
ORDER BY ProductCode;

-- 7. 保留无消费会员，并仅统计完成订单；不公开联系方式。
SELECT m.MemberCode, m.DisplayName,
       COUNT(DISTINCT o.OrderNo) AS CompletedOrders,
       COALESCE(SUM(l.Quantity), 0) AS CupsPurchased,
       CONVERT(decimal(12,2), COALESCE(SUM(l.Quantity * l.UnitPrice), 0)) AS CompletedAmount
FROM dbo.Member AS m
LEFT JOIN dbo.ShopOrder AS o ON o.MemberCode = m.MemberCode AND o.Status = 'COMPLETED'
LEFT JOIN dbo.OrderLine AS l ON l.OrderNo = o.OrderNo
GROUP BY m.MemberCode, m.DisplayName
ORDER BY m.MemberCode;
GO
