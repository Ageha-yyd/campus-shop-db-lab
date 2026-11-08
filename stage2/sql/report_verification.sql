SET NOCOUNT ON;
SELECT DB_NAME() AS DatabaseName;
SELECT Status,COUNT(*) AS Orders FROM dbo.ShopOrder GROUP BY Status ORDER BY Status;
SELECT COUNT(DISTINCT o.OrderNo) AS CompletedOrders,SUM(l.Quantity) AS Cups,SUM(CAST(l.Quantity AS decimal(18,2))*l.UnitPrice) AS Amount
FROM dbo.ShopOrder o JOIN dbo.OrderLine l ON l.OrderNo=o.OrderNo WHERE o.Status='COMPLETED';
SELECT p.ProductCode,CAST(p.ProductName AS nvarchar(10)) AS ProductName,i.Quantity,s.UnitsSold,s.SalesAmount
FROM dbo.Product p LEFT JOIN dbo.Inventory i ON i.ProductCode=p.ProductCode JOIN dbo.vw_ProductSales s ON s.ProductCode=p.ProductCode ORDER BY p.ProductCode;
SELECT OrderNo,LineNumber,ProductCode,Quantity,UnitPrice FROM dbo.OrderLine ORDER BY OrderNo,LineNumber;
