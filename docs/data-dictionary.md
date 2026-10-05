# 关系模式与数据字典

产品名称和菜单标价参考公开菜单来源；订单、库存、员工、会员及联系方式均为虚构教学数据，不代表蜜雪冰城或其他门店的实际经营记录。SQL Server 类型是本次实现域；关系模式以列名和约束表达，物理类型后续可按引擎映射。每个字段下方均说明类型、空值/默认值/取值域及业务含义；未写默认值表示没有数据库默认值。

## Product（饮品菜单）

行粒度：一个可销售的标准饮品。

| 字段 | 定义与含义 |
| --- | --- |
| `ProductCode` | `varchar(12) NOT NULL`；饮品编码，用于稳定引用菜单项。 |
| `ProductName` | `nvarchar(80) NOT NULL`；饮品菜单显示名称。 |
| `Category` | `nvarchar(30) NOT NULL`；菜单分类文字，如“奶茶”“果茶”；本版不限制为固定枚举。 |
| `UnitPrice` | `decimal(10,2) NOT NULL CHECK (> 0)`；当前菜单单价，最多两位小数且必须为正。 |
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
| `DisplayName` | `nvarchar(60) NOT NULL`；样例展示名，不要求使用真实姓名。 |
| `Phone` | `varchar(20) NULL`；可选联系号码；非空值须唯一，本仓库样例为虚构值。 |
| `JoinedAt` | `date NOT NULL DEFAULT (CONVERT(date, SYSUTCDATETIME()))`；登记日期，默认使用当前 UTC 日期。 |

主码：`MemberCode`。候选码：`Phone` 的非空值，由过滤唯一索引 `UX_Member_Phone_NotNull` 实现；空值允许多个，匿名顾客不必登记。

## Employee（员工）

行粒度：一位门店员工。

| 字段 | 定义与含义 |
| --- | --- |
| `EmployeeCode` | `varchar(12) NOT NULL`；员工内部编号。 |
| `DisplayName` | `nvarchar(60) NOT NULL`；员工展示名，仓库中的样例均为虚构。 |
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

## 样例关系（摘要）

- Product：`D001` 珍珠奶茶 6.00；`D002` 满杯百香果 7.00；`D003` 冰鲜柠檬水 4.00（菜单参考数据，来源和访问日期见 `data-sources.md`）。
- Inventory：D001 17、D002 9、D003 12（可售杯数快照，不追踪原料）。
- Member：M001 林同学（虚构）；M002 周同学（虚构）。
- Employee：E001 陈店员、E002 王店长（均虚构）。
- ShopOrder：一笔关联 M001 的完成单、一笔匿名完成单、一笔取消单。
- OrderLine：虚构完成单售出珍珠奶茶和满杯百香果；冰鲜柠檬水只出现在取消单，因此完成销售汇总为零。

菜单名称与单价采用公开菜单参考；交易与库存样例仍是虚构的，不应解读为蜜雪冰城真实订单、销量或库存。课程第二周任务说明提到真实业务样例；如该项要求真实交易数据，需由学习者补充经授权和去标识化的数据，不能用公开菜单价冒充真实销售记录。

## 联系与基数

- Product 1—0/1 Inventory（本版样例要求每个商品有一行库存快照）。
- Employee 1—N ShopOrder；Member 0/1—N ShopOrder（订单可匿名）。
- ShopOrder 1—N OrderLine；Product 1—N OrderLine。
