# 关系模式与数据字典

本字典列出六张业务表的行粒度、属性域、类型、长度、精度、空值、默认值、键及业务含义。未写默认值表示没有数据库默认值；完整样例见SQL02。

## Product（饮品菜单）

行粒度：一个可销售的标准饮品。

| 字段 | 定义与含义 |
| --- | --- |
| `ProductCode` | `varchar(12) NOT NULL`；饮品编码，用于稳定引用菜单项。 |
| `ProductName` | `nvarchar(80) NOT NULL`；饮品菜单显示名称。 |
| `Category` | `nvarchar(30) NOT NULL`；菜单分类文字，如“奶茶”“果茶”；本版不限制为固定枚举。 |
| `UnitPrice` | `decimal(10,2) NOT NULL CHECK (> 0)`；当前菜单单价，最多两位小数且必须为正。 |
| `RestockThreshold` | `int NOT NULL DEFAULT (10) CHECK (> 0)`；每款饮品可售杯数预警阈值；等于阈值也触发预警。 |
| `IsActive` | `bit NOT NULL DEFAULT (1)`；是否仍在售，取值 0/1。 |

主码：`ProductCode`。饮品名称可能重复或更改，不作为候选码。

## Inventory（可售杯数快照）

行粒度：一个饮品的一份当前可售数量快照。

| 字段 | 定义与含义 |
| --- | --- |
| `ProductCode` | `varchar(12) NOT NULL`；所对应饮品编码。 |
| `Quantity` | `int NOT NULL DEFAULT (0) CHECK (>= 0)`；当前记录的可售杯数，不代表原料数量。 |
| `UpdatedAt` | `datetime2(0) NOT NULL DEFAULT (SYSUTCDATETIME())`；快照最后更新时间，默认写入 UTC 时间。 |

主码：`ProductCode`；同时是引用 `Product(ProductCode)` 的外码。每个饮品最多一份快照。

## Member（可选会员）

行粒度：一个自愿登记的会员。

| 字段 | 定义与含义 |
| --- | --- |
| `MemberCode` | `varchar(12) NOT NULL`；会员内部编号。 |
| `DisplayName` | `nvarchar(60) NOT NULL`；会员显示名称。 |
| `Phone` | `varchar(20) NULL`；可选联系号码；非空值须唯一，本仓库种子样例均为 NULL，反例只用回滚的占位值。 |
| `JoinedAt` | `date NOT NULL DEFAULT (CONVERT(date, SYSUTCDATETIME()))`；登记日期，默认使用当前 UTC 日期。 |

主码：`MemberCode`。唯一候选码为 `MemberCode`。`Phone` 是非空时唯一的可选属性，由过滤唯一索引 `UX_Member_Phone_NotNull` 实现；允许多个 NULL，因此不作为整个关系的候选码。匿名顾客不必登记。

## Employee（员工）

行粒度：一位门店员工。

| 字段 | 定义与含义 |
| --- | --- |
| `EmployeeCode` | `varchar(12) NOT NULL`；员工内部编号。 |
| `DisplayName` | `nvarchar(60) NOT NULL`；员工显示名称。 |
| `JobTitle` | `nvarchar(30) NOT NULL`；岗位名称，如“店员”“店长”。 |
| `IsActive` | `bit NOT NULL DEFAULT (1)`；是否在职/启用，取值 0/1。 |

主码：`EmployeeCode`。

## ShopOrder（订单头）

行粒度：一张订单。

| 字段 | 定义与含义 |
| --- | --- |
| `OrderNo` | `varchar(24) NOT NULL`；订单编号，用于识别一张订单。 |
| `OrderedAt` | `datetime2(0) NOT NULL DEFAULT (SYSUTCDATETIME())`；下单时间，默认使用 UTC 当前时间。 |
| `EmployeeCode` | `varchar(12) NOT NULL`；经办员工编号，引用 `Employee(EmployeeCode)`。 |
| `MemberCode` | `varchar(12) NULL`；可选会员编号，引用 `Member(MemberCode)`；空值表示匿名购买。 |
| `Status` | `varchar(12) NOT NULL DEFAULT ('COMPLETED') CHECK (IN ('COMPLETED','CANCELLED'))`；订单状态，本版只区分完成和取消。 |

主码/候选码：`OrderNo`。外码：`EmployeeCode`、`MemberCode` 分别引用员工、会员。

## OrderLine（订单明细）

行粒度：一张订单中的一个饮品明细行。

| 字段 | 定义与含义 |
| --- | --- |
| `OrderNo` | `varchar(24) NOT NULL`；所属订单编号，引用 `ShopOrder(OrderNo)`。 |
| `LineNumber` | `smallint NOT NULL`；同一订单内的行号。 |
| `ProductCode` | `varchar(12) NOT NULL`；本行所售饮品，引用 `Product(ProductCode)`。 |
| `Quantity` | `int NOT NULL CHECK (> 0)`；本行购买杯数，必须为正整数。 |
| `UnitPrice` | `decimal(10,2) NOT NULL CHECK (>= 0)`；成交时单价快照，保留历史成交价格。 |

复合主码：`(OrderNo, LineNumber)`。外码：`OrderNo`、`ProductCode`。订单与饮品之间的多对多关系由明细分解，成交单价和数量属于明细事实。

## 关系模式、码与理由

六个关系为 Product(ProductCode, ProductName, Category, UnitPrice, RestockThreshold, IsActive)、Inventory(ProductCode, Quantity, UpdatedAt)、Member(MemberCode, DisplayName, Phone, JoinedAt)、Employee(EmployeeCode, DisplayName, JobTitle, IsActive)、ShopOrder(OrderNo, OrderedAt, EmployeeCode, MemberCode, Status)、OrderLine(OrderNo, LineNumber, ProductCode, Quantity, UnitPrice)。

| 关系 | 候选码（同时选为主码） | 外码 | 选择理由 |
| --- | --- | --- | --- |
| Product | ProductCode | 无 | 名称/价格可变，编码稳定 |
| Inventory | ProductCode | → Product | 每饮品至多一份当前快照 |
| Member | MemberCode | 无 | 姓名可重复；Phone 可空，不能作为全关系候选码 |
| Employee | EmployeeCode | 无 | 展示名和岗位可变 |
| ShopOrder | OrderNo | EmployeeCode → Employee；MemberCode → Member（可空） | 一张订单唯一标识；会员可选 |
| OrderLine | (OrderNo, LineNumber) | OrderNo → ShopOrder；ProductCode → Product | 区分同单多行，允许同饮品出现多次 |

订单金额由数量×成交价计算，不冗余存储可任意改写的行小计/总金额。明细单价是历史事实，与当前菜单价含义不同。无级联删除，删除演示先明细、后订单，先库存、后饮品。

## 每表至少三行样例

以下为摘要投影；每行完整属性以 [seed](../sql/02_seed.sql) 为准。

| ProductCode | 名称 | 单价 | 阈值 | Inventory.Quantity |
| --- | --- | ---: | ---: | ---: |
| D001 | 珍珠奶茶 | 6.00 | 10 | 20 |
| D002 | 满杯百香果 | 7.00 | 12 | 12 |
| D003 | 冰鲜柠檬水 | 4.00 | 8 | 5 |
| D004 | 椰果奶茶 | 7.00 | 6 | 0 |
| D005 | 柠檬红茶 | 5.00 | 4 | 18 |
| D006 | 茉莉绿茶 | 4.00 | 5 | 9 |

| MemberCode | 展示名 | Phone | JoinedAt |
| --- | --- | --- | --- |
| M001 | 林同学 | NULL | 2026-09-01 |
| M002 | 周同学 | NULL | 2026-09-03 |
| M003 | 李同学 | NULL | 2026-09-04 |
| M004 | 陈同学 | NULL | 2026-09-05 |

| EmployeeCode | 展示名 | 岗位 |
| --- | --- | --- |
| E001 | 陈店员 | 店员 |
| E002 | 刘店员 | 店员 |
| E003 | 王店长 | 店长 |

| ShopOrder.OrderNo | EmployeeCode | MemberCode | Status |
| --- | --- | --- | --- |
| MT-20261001-001 | E001 | M001 | COMPLETED |
| MT-20261001-002 | E002 | NULL | COMPLETED |
| MT-20261002-001 | E001 | M002 | COMPLETED |

另有一张取消单、三张完成单，共七张。

| OrderLine.OrderNo | LineNumber | ProductCode | Quantity | UnitPrice |
| --- | ---: | --- | ---: | ---: |
| MT-20261001-001 | 1 | D001 | 2 | 6.00 |
| MT-20261001-001 | 2 | D002 | 1 | 7.00 |
| MT-20261001-002 | 1 | D003 | 3 | 4.00 |

明细共十一行，会员Phone为空；菜单参考和样例安排见 [数据说明](data-sources.md)。

## 联系与基数

- Product 1—0/1 Inventory；当前种子每个饮品均有快照。
- Employee 1—0..N ShopOrder；Member 1—0..N ShopOrder；每张订单关联 0/1 位会员。
- ShopOrder 1—0..N OrderLine；Product 1—0..N OrderLine。

业务上完成订单应至少有一行明细，但外键只能保证每个明细有订单，不能强制每个订单有明细。本版样例满足该规则；未实现结单事务来强制非空订单。店员的 INSERT 权限也不等于实现完整结单业务流程。

## 预警与会员统计口径

当前杯数=0 时显示“缺货”，0<杯数≤阈值为“低库存”，高于阈值为“有库存”，没有快照时为“未登记”。预警时建议杯数=2×阈值−当前杯数，否则为 0；没有快照返回 NULL。计算使用 bigint 避免阈值倍增的 int 溢出。

会员汇总用 LEFT JOIN 保留 M004；仅关联完成订单，COUNT(DISTINCT OrderNo) 避免多明细重复计单；金额来自成交价。会员报表仅授权店长读取。
