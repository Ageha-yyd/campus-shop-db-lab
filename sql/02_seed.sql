SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
SET XACT_ABORT ON;

-- 课堂操作样例；菜单参考来源见 data/public-menu.csv。
-- 显式 UTC 日期保证跨日期复现；会员联系方式不收集，样例全部 NULL。
BEGIN TRANSACTION;

INSERT dbo.Product (ProductCode, ProductName, Category, UnitPrice, RestockThreshold, IsActive) VALUES
('D001', N'珍珠奶茶', N'奶茶', 6.00, 10, 1),
('D002', N'满杯百香果', N'果茶', 7.00, 12, 1),
('D003', N'冰鲜柠檬水', N'柠檬饮品', 4.00, 8, 1),
('D004', N'椰果奶茶', N'奶茶', 7.00, 6, 1),
('D005', N'柠檬红茶', N'果茶', 5.00, 4, 1),
('D006', N'茉莉绿茶', N'纯茶', 4.00, 5, 1);

INSERT dbo.Inventory (ProductCode, Quantity, UpdatedAt) VALUES
('D001', 20, '2026-10-06T08:00:00'),
('D002', 12, '2026-10-06T08:00:00'),
('D003', 5, '2026-10-06T08:00:00'),
('D004', 0, '2026-10-06T08:00:00'),
('D005', 18, '2026-10-06T08:00:00'),
('D006', 9, '2026-10-06T08:00:00');

INSERT dbo.Member (MemberCode, DisplayName, Phone, JoinedAt) VALUES
('M001', N'林同学', NULL, '2026-09-01'),
('M002', N'周同学', NULL, '2026-09-03'),
('M003', N'李同学', NULL, '2026-09-04'),
('M004', N'陈同学', NULL, '2026-09-05');

INSERT dbo.Employee (EmployeeCode, DisplayName, JobTitle, IsActive) VALUES
('E001', N'陈店员', N'店员', 1),
('E002', N'刘店员', N'店员', 1),
('E003', N'王店长', N'店长', 1);

INSERT dbo.ShopOrder (OrderNo, OrderedAt, EmployeeCode, MemberCode, Status) VALUES
('MT-20261001-001', '2026-10-01T09:42:00', 'E001', 'M001', 'COMPLETED'),
('MT-20261001-002', '2026-10-01T12:35:00', 'E002', NULL, 'COMPLETED'),
('MT-20261002-001', '2026-10-02T10:18:00', 'E001', 'M002', 'COMPLETED'),
('MT-20261002-002', '2026-10-02T14:02:00', 'E001', 'M002', 'CANCELLED'),
('MT-20261003-001', '2026-10-03T11:26:00', 'E002', NULL, 'COMPLETED'),
('MT-20261004-001', '2026-10-04T15:40:00', 'E002', 'M001', 'COMPLETED'),
('MT-20261004-002', '2026-10-04T16:10:00', 'E001', 'M003', 'COMPLETED');

INSERT dbo.OrderLine (OrderNo, LineNumber, ProductCode, Quantity, UnitPrice) VALUES
('MT-20261001-001', 1, 'D001', 2, 6.00),
('MT-20261001-001', 2, 'D002', 1, 7.00),
('MT-20261001-002', 1, 'D003', 3, 4.00),
('MT-20261002-001', 1, 'D003', 1, 4.00),
('MT-20261002-002', 1, 'D005', 1, 5.00),
('MT-20261003-001', 1, 'D004', 2, 7.00),
('MT-20261003-001', 2, 'D001', 1, 6.00),
('MT-20261004-001', 1, 'D002', 2, 7.00),
('MT-20261004-001', 2, 'D004', 1, 7.00),
('MT-20261004-002', 1, 'D003', 1, 4.00),
('MT-20261004-002', 2, 'D001', 1, 6.00);

COMMIT TRANSACTION;

SELECT N'Product' AS table_name, COUNT(*) AS row_count FROM dbo.Product
UNION ALL SELECT N'Inventory', COUNT(*) FROM dbo.Inventory
UNION ALL SELECT N'Member', COUNT(*) FROM dbo.Member
UNION ALL SELECT N'Employee', COUNT(*) FROM dbo.Employee
UNION ALL SELECT N'ShopOrder', COUNT(*) FROM dbo.ShopOrder
UNION ALL SELECT N'OrderLine', COUNT(*) FROM dbo.OrderLine
ORDER BY table_name;
GO
