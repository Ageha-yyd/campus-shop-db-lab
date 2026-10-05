SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

-- 饮品名称与菜单参考价来源见 docs/data-sources.md；关联订单和其余数据为虚构样例。
BEGIN TRANSACTION;

INSERT dbo.Product (ProductCode, ProductName, Category, UnitPrice, IsActive) VALUES
('D001', N'珍珠奶茶', N'奶茶', 6.00, 1),
('D002', N'满杯百香果', N'果茶', 7.00, 1),
('D003', N'冰鲜柠檬水', N'柠檬饮品', 4.00, 1);

INSERT dbo.Inventory (ProductCode, Quantity) VALUES
('D001', 17), ('D002', 9), ('D003', 12);

INSERT dbo.Member (MemberCode, DisplayName, Phone, JoinedAt) VALUES
('M001', N'林同学（虚构）', '13800000001', '2026-09-01'),
('M002', N'周同学（虚构）', NULL, '2026-09-03');

INSERT dbo.Employee (EmployeeCode, DisplayName, JobTitle, IsActive) VALUES
('E001', N'陈店员（虚构）', N'店员', 1),
('E002', N'王店长（虚构）', N'店长', 1);

INSERT dbo.ShopOrder (OrderNo, OrderedAt, EmployeeCode, MemberCode, Status) VALUES
('MT-20261005-001', '2026-10-05T10:00:00', 'E001', 'M001', 'COMPLETED'),
('MT-20261005-002', '2026-10-05T11:00:00', 'E001', NULL, 'COMPLETED'),
('MT-20261005-003', '2026-10-05T12:00:00', 'E002', 'M001', 'CANCELLED');

INSERT dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice) VALUES
('MT-20261005-001', 1, 'D001', 2, 6.00),
('MT-20261005-001', 2, 'D002', 1, 7.00),
('MT-20261005-002', 1, 'D001', 1, 6.00),
('MT-20261005-003', 1, 'D003', 1, 4.00);

COMMIT TRANSACTION;

SELECT N'Product' AS table_name, COUNT(*) AS row_count FROM dbo.Product
UNION ALL SELECT N'Inventory', COUNT(*) FROM dbo.Inventory
UNION ALL SELECT N'Member', COUNT(*) FROM dbo.Member
UNION ALL SELECT N'Employee', COUNT(*) FROM dbo.Employee
UNION ALL SELECT N'ShopOrder', COUNT(*) FROM dbo.ShopOrder
UNION ALL SELECT N'OrderLine', COUNT(*) FROM dbo.OrderLine
ORDER BY table_name;
GO
