SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

CREATE TABLE dbo.Product (
    ProductCode varchar(12) NOT NULL,
    ProductName nvarchar(80) NOT NULL,
    Category nvarchar(30) NOT NULL,
    UnitPrice decimal(10,2) NOT NULL,
    RestockThreshold int NOT NULL CONSTRAINT DF_Product_RestockThreshold DEFAULT (10),
    IsActive bit NOT NULL CONSTRAINT DF_Product_IsActive DEFAULT (1),
    CONSTRAINT PK_Product PRIMARY KEY (ProductCode),
    CONSTRAINT CK_Product_UnitPrice_Positive CHECK (UnitPrice > 0),
    CONSTRAINT CK_Product_RestockThreshold_Positive CHECK (RestockThreshold > 0)
);

CREATE TABLE dbo.Inventory (
    ProductCode varchar(12) NOT NULL,
    Quantity int NOT NULL CONSTRAINT DF_Inventory_Quantity DEFAULT (0),
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_Inventory_UpdatedAt DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT PK_Inventory PRIMARY KEY (ProductCode),
    CONSTRAINT FK_Inventory_Product FOREIGN KEY (ProductCode) REFERENCES dbo.Product(ProductCode),
    CONSTRAINT CK_Inventory_Quantity_Nonnegative CHECK (Quantity >= 0)
);

CREATE TABLE dbo.Member (
    MemberCode varchar(12) NOT NULL,
    DisplayName nvarchar(60) NOT NULL,
    Phone varchar(20) NULL,
    JoinedAt date NOT NULL CONSTRAINT DF_Member_JoinedAt DEFAULT (CONVERT(date, SYSUTCDATETIME())),
    CONSTRAINT PK_Member PRIMARY KEY (MemberCode)
);
CREATE UNIQUE INDEX UX_Member_Phone_NotNull ON dbo.Member(Phone) WHERE Phone IS NOT NULL;

CREATE TABLE dbo.Employee (
    EmployeeCode varchar(12) NOT NULL,
    DisplayName nvarchar(60) NOT NULL,
    JobTitle nvarchar(30) NOT NULL,
    IsActive bit NOT NULL CONSTRAINT DF_Employee_IsActive DEFAULT (1),
    CONSTRAINT PK_Employee PRIMARY KEY (EmployeeCode)
);

CREATE TABLE dbo.ShopOrder (
    OrderNo varchar(24) NOT NULL,
    OrderedAt datetime2(0) NOT NULL CONSTRAINT DF_ShopOrder_OrderedAt DEFAULT (SYSUTCDATETIME()),
    EmployeeCode varchar(12) NOT NULL,
    MemberCode varchar(12) NULL,
    Status varchar(12) NOT NULL CONSTRAINT DF_ShopOrder_Status DEFAULT ('COMPLETED'),
    CONSTRAINT PK_ShopOrder PRIMARY KEY (OrderNo),
    CONSTRAINT FK_ShopOrder_Employee FOREIGN KEY (EmployeeCode) REFERENCES dbo.Employee(EmployeeCode),
    CONSTRAINT FK_ShopOrder_Member FOREIGN KEY (MemberCode) REFERENCES dbo.Member(MemberCode),
    CONSTRAINT CK_ShopOrder_Status CHECK (Status IN ('COMPLETED', 'CANCELLED'))
);

CREATE TABLE dbo.OrderLine (
    OrderNo varchar(24) NOT NULL,
    LineNumber smallint NOT NULL,
    ProductCode varchar(12) NOT NULL,
    Quantity int NOT NULL,
    UnitPrice decimal(10,2) NOT NULL,
    CONSTRAINT PK_OrderLine PRIMARY KEY (OrderNo, LineNumber),
    CONSTRAINT FK_OrderLine_ShopOrder FOREIGN KEY (OrderNo) REFERENCES dbo.ShopOrder(OrderNo),
    CONSTRAINT FK_OrderLine_Product FOREIGN KEY (ProductCode) REFERENCES dbo.Product(ProductCode),
    CONSTRAINT CK_OrderLine_Quantity_Positive CHECK (Quantity > 0),
    CONSTRAINT CK_OrderLine_UnitPrice_Nonnegative CHECK (UnitPrice >= 0)
);
GO
SELECT t.name AS table_name, COUNT(c.column_id) AS column_count
FROM sys.tables AS t
JOIN sys.columns AS c ON c.object_id = t.object_id
WHERE t.schema_id = SCHEMA_ID(N'dbo')
GROUP BY t.name
ORDER BY t.name;
GO
