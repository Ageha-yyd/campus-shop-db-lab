# v1.0 数据字典

业务规则、候选码、关系和范式依据见 design.md。类型、长度、精度、空值、默认值来自本次实际SQL Server目录；键、检查与索引列表也直接导出。

## Product

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| ProductCode | varchar(12) | 否 | 无 | 标准饮品编号 |
| ProductName | nvarchar(80) | 否 | 无 | 当前饮品名称 |
| Category | nvarchar(30) | 否 | 无 | 原子类别名称 |
| UnitPrice | decimal(10,2) | 否 | 无 | Product为当前菜单价；OrderLine为保存当次成交价 |
| RestockThreshold | int | 否 | ((10)) | 库存预警阈值 杯 |
| IsActive | bit | 否 | ((1)) | 是否启用 |

码与索引：PK_Product(ProductCode) PK

无外码。

检查约束：CK_Product_UnitPrice_Positive ([UnitPrice]>(0))；CK_Product_RestockThreshold_Positive ([RestockThreshold]>(0))

样例：
```json
[
  {
    "ProductCode": "D001",
    "ProductName": "珍珠奶茶",
    "Category": "奶茶",
    "UnitPrice": "6.00",
    "RestockThreshold": 10,
    "IsActive": true
  },
  {
    "ProductCode": "D002",
    "ProductName": "满杯百香果",
    "Category": "果茶",
    "UnitPrice": "7.00",
    "RestockThreshold": 12,
    "IsActive": true
  },
  {
    "ProductCode": "D003",
    "ProductName": "冰鲜柠檬水",
    "Category": "柠檬饮品",
    "UnitPrice": "4.00",
    "RestockThreshold": 8,
    "IsActive": true
  }
]
```

## Inventory

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| ProductCode | varchar(12) | 否 | 无 | 标准饮品编号 |
| Quantity | int | 否 | ((0)) | Inventory为可售杯数；OrderLine为购买杯数 |
| UpdatedAt | datetime2(0) | 否 | (sysutcdatetime()) | 库存最后维护时间 UTC |

码与索引：PK_Inventory(ProductCode) PK

外码：ProductCode→Product.ProductCode

检查约束：CK_Inventory_Quantity_Nonnegative ([Quantity]>=(0))

样例：
```json
[
  {
    "ProductCode": "D001",
    "Quantity": 20,
    "UpdatedAt": "2026-10-06 08:00:00"
  },
  {
    "ProductCode": "D002",
    "Quantity": 12,
    "UpdatedAt": "2026-10-06 08:00:00"
  },
  {
    "ProductCode": "D003",
    "Quantity": 5,
    "UpdatedAt": "2026-10-06 08:00:00"
  }
]
```

## Member

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| MemberCode | varchar(12) | 否 | 无 | 可选会员编号 |
| DisplayName | nvarchar(60) | 否 | 无 | 显示名称 |
| Phone | varchar(20) | 是 | 无 | 可选联系电话 非空时唯一 |
| JoinedAt | date | 否 | (CONVERT([date],sysutcdatetime())) | 会员加入日期 |

码与索引：PK_Member(MemberCode) PK；UX_Member_Phone_NotNull(Phone) UNIQUE WHERE ([Phone] IS NOT NULL)

无外码。

其他域由类型、外码或服务层规则控制。

样例：
```json
[
  {
    "MemberCode": "M001",
    "DisplayName": "林同学",
    "Phone": null,
    "JoinedAt": "2026-09-01"
  },
  {
    "MemberCode": "M002",
    "DisplayName": "周同学",
    "Phone": null,
    "JoinedAt": "2026-09-03"
  },
  {
    "MemberCode": "M003",
    "DisplayName": "李同学",
    "Phone": null,
    "JoinedAt": "2026-09-04"
  }
]
```

## Employee

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| EmployeeCode | varchar(12) | 否 | 无 | 员工编号 草稿可以暂未指派 |
| DisplayName | nvarchar(60) | 否 | 无 | 显示名称 |
| JobTitle | nvarchar(30) | 否 | 无 | 员工职称 |
| IsActive | bit | 否 | ((1)) | 是否启用 |

码与索引：PK_Employee(EmployeeCode) PK

无外码。

其他域由类型、外码或服务层规则控制。

样例：
```json
[
  {
    "EmployeeCode": "E001",
    "DisplayName": "陈店员",
    "JobTitle": "店员",
    "IsActive": true
  },
  {
    "EmployeeCode": "E002",
    "DisplayName": "刘店员",
    "JobTitle": "店员",
    "IsActive": true
  },
  {
    "EmployeeCode": "E003",
    "DisplayName": "王店长",
    "JobTitle": "店长",
    "IsActive": true
  }
]
```

## ShopOrder

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| OrderNo | varchar(24) | 否 | 无 | 订单编号 |
| OrderedAt | datetime2(0) | 否 | (sysutcdatetime()) | 订单创建时间 UTC |
| EmployeeCode | varchar(12) | 是 | 无 | 员工编号 草稿可以暂未指派 |
| MemberCode | varchar(12) | 是 | 无 | 可选会员编号 |
| Status | varchar(12) | 否 | ('COMPLETED') | DRAFT COMPLETED CANCELLED |
| CreatedByUserId | int | 是 | 无 | 应用创建账号 历史订单为空 |
| StockApplied | bit | 否 | ((0)) | 是否有本系统新增扣库待回补 历史单为0 |

码与索引：PK_ShopOrder(OrderNo) PK

外码：EmployeeCode→Employee.EmployeeCode；MemberCode→Member.MemberCode；CreatedByUserId→AppUser.UserId

检查约束：CK_ShopOrder_Status ([Status]='CANCELLED' OR [Status]='COMPLETED' OR [Status]='DRAFT')

样例：
```json
[
  {
    "OrderNo": "MT-20261001-001",
    "OrderedAt": "2026-10-01 09:42:00",
    "EmployeeCode": "E001",
    "MemberCode": "M001",
    "Status": "COMPLETED",
    "CreatedByUserId": null,
    "StockApplied": false
  },
  {
    "OrderNo": "MT-20261001-002",
    "OrderedAt": "2026-10-01 12:35:00",
    "EmployeeCode": "E002",
    "MemberCode": null,
    "Status": "COMPLETED",
    "CreatedByUserId": null,
    "StockApplied": false
  },
  {
    "OrderNo": "MT-20261002-001",
    "OrderedAt": "2026-10-02 10:18:00",
    "EmployeeCode": "E001",
    "MemberCode": "M002",
    "Status": "COMPLETED",
    "CreatedByUserId": null,
    "StockApplied": false
  }
]
```

## OrderLine

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| OrderNo | varchar(24) | 否 | 无 | 订单编号 |
| LineNumber | smallint | 否 | 无 | 同订单内行号 从1开始 |
| ProductCode | varchar(12) | 否 | 无 | 标准饮品编号 |
| Quantity | int | 否 | 无 | Inventory为可售杯数；OrderLine为购买杯数 |
| UnitPrice | decimal(10,2) | 否 | 无 | Product为当前菜单价；OrderLine为保存当次成交价 |

码与索引：PK_OrderLine(OrderNo,LineNumber) PK

外码：OrderNo→ShopOrder.OrderNo；ProductCode→Product.ProductCode

检查约束：CK_OrderLine_Quantity_Positive ([Quantity]>(0))；CK_OrderLine_UnitPrice_Nonnegative ([UnitPrice]>=(0))

样例：
```json
[
  {
    "OrderNo": "MT-20261001-001",
    "LineNumber": 1,
    "ProductCode": "D001",
    "Quantity": 2,
    "UnitPrice": "6.00"
  },
  {
    "OrderNo": "MT-20261001-001",
    "LineNumber": 2,
    "ProductCode": "D002",
    "Quantity": 1,
    "UnitPrice": "7.00"
  },
  {
    "OrderNo": "MT-20261001-002",
    "LineNumber": 1,
    "ProductCode": "D003",
    "Quantity": 3,
    "UnitPrice": "4.00"
  }
]
```

## AppUser

| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |
| --- | --- | --- | --- | --- |
| UserId | int | 否 | 无 | 应用账号主标识 |
| Username | varchar(40) | 否 | 无 | 登录名 唯一候选码 |
| PasswordHash | varchar(255) | 否 | 无 | scrypt密码哈希 禁止前端及结果导出 |
| Role | varchar(12) | 否 | 无 | admin clerk customer |
| EmployeeCode | varchar(12) | 是 | 无 | 员工编号 草稿可以暂未指派 |
| MemberCode | varchar(12) | 是 | 无 | 可选会员编号 |
| IsActive | bit | 否 | ((1)) | 是否启用 |

码与索引：PK_AppUser(UserId) PK；UQ_AppUser_Username(Username) UNIQUE；UX_AppUser_Employee(EmployeeCode) UNIQUE WHERE ([EmployeeCode] IS NOT NULL)；UX_AppUser_Member(MemberCode) UNIQUE WHERE ([MemberCode] IS NOT NULL)

外码：EmployeeCode→Employee.EmployeeCode；MemberCode→Member.MemberCode

检查约束：CK_AppUser_Role ([Role]='customer' OR [Role]='clerk' OR [Role]='admin')；CK_AppUser_Profile (([Role]='clerk' OR [Role]='admin') AND [EmployeeCode] IS NOT NULL AND [MemberCode] IS NULL OR [Role]='customer' AND [EmployeeCode] IS NULL)

账号样例仅导出非敏感字段：
```json
[
  {
    "UserId": 1,
    "Username": "admin",
    "Role": "admin",
    "EmployeeCode": "E003",
    "MemberCode": null,
    "IsActive": true
  },
  {
    "UserId": 2,
    "Username": "clerk",
    "Role": "clerk",
    "EmployeeCode": "E001",
    "MemberCode": null,
    "IsActive": true
  },
  {
    "UserId": 3,
    "Username": "customer",
    "Role": "customer",
    "EmployeeCode": null,
    "MemberCode": "M001",
    "IsActive": true
  },
  {
    "UserId": 4,
    "Username": "guest",
    "Role": "customer",
    "EmployeeCode": null,
    "MemberCode": null,
    "IsActive": true
  }
]
```
