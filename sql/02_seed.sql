SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
BEGIN TRANSACTION;

INSERT dbo.Product (ProductCode, ProductName, Category, UnitPrice, IsActive) VALUES
('P001', N'纯牛奶 250ml', N'乳品', 3.50, 1),
('P002', N'全麦面包', N'烘焙', 5.00, 1),
('P003', N'乌龙茶 500ml', N'饮料', 4.25, 1);

INSERT dbo.Inventory (ProductCode, Quantity) VALUES
('P001', 17), ('P002', 9), ('P003', 12);

INSERT dbo.Member (MemberCode, DisplayName, Phone, JoinedAt) VALUES
('M001', N'林同学（虚构）', '13800000001', '2026-09-01'),
('M002', N'周同学（虚构）', NULL, '2026-09-03');

INSERT dbo.Employee (EmployeeCode, DisplayName, JobTitle, IsActive) VALUES
('E001', N'陈店员（虚构）', N'店员', 1),
('E002', N'王店长（虚构）', N'店长', 1);

INSERT dbo.ShopOrder (OrderNo, OrderedAt, EmployeeCode, MemberCode, Status) VALUES
('CS-20261001-001', '2026-10-01T10:00:00', 'E001', 'M001', 'COMPLETED'),
('CS-20261001-002', '2026-10-01T11:00:00', 'E001', NULL, 'COMPLETED'),
('CS-20261001-003', '2026-10-01T12:00:00', 'E002', 'M001', 'CANCELLED');

INSERT dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice) VALUES
('CS-20261001-001', 1, 'P001', 2, 3.50),
('CS-20261001-001', 2, 'P002', 1, 5.00),
('CS-20261001-002', 1, 'P001', 1, 3.50),
('CS-20261001-003', 1, 'P003', 1, 4.25);

COMMIT TRANSACTION;

SELECT N'Product' AS table_name, COUNT(*) AS row_count FROM dbo.Product
UNION ALL SELECT N'Inventory', COUNT(*) FROM dbo.Inventory
UNION ALL SELECT N'Member', COUNT(*) FROM dbo.Member
UNION ALL SELECT N'Employee', COUNT(*) FROM dbo.Employee
UNION ALL SELECT N'ShopOrder', COUNT(*) FROM dbo.ShopOrder
UNION ALL SELECT N'OrderLine', COUNT(*) FROM dbo.OrderLine
ORDER BY table_name;
GO
