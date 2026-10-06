SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
-- Read-only compact evidence for the same business queries/views in 04 and 05.
SELECT ProductCode,ProductName,OnHand,RestockThreshold,StockStatus,SuggestedPreparationCups
FROM dbo.vw_InventoryStatus ORDER BY ProductCode;
SELECT * FROM dbo.vw_MemberConsumption ORDER BY MemberCode;
SELECT * FROM dbo.vw_ProductSales ORDER BY ProductCode;
SELECT m.MemberCode, SUM(l.Quantity*l.UnitPrice) AS CompletedAmount
FROM dbo.Member m
JOIN dbo.ShopOrder o ON o.MemberCode=m.MemberCode AND o.Status='COMPLETED'
JOIN dbo.OrderLine l ON l.OrderNo=o.OrderNo
GROUP BY m.MemberCode HAVING SUM(l.Quantity*l.UnitPrice)>=10.00
ORDER BY m.MemberCode;
SELECT ProductCode,ProductName,UnitPrice FROM dbo.Product
WHERE IsActive=1 AND UnitPrice>(SELECT AVG(UnitPrice) FROM dbo.Product WHERE IsActive=1)
ORDER BY ProductCode;
GO
