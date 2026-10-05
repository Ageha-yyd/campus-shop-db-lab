# 关系模式与数据字典

样例行均为虚构数据。SQL Server 类型是本次实现域；关系模式以列名/约束表达，物理类型后续可按引擎映射。

| 关系 | 行粒度 | 字段（类型；空值/域） | 键与约束理由 |
| --- | --- | --- | --- |
| `Product` | 一个可销售商品 | `ProductCode varchar(12)` 非空；`ProductName nvarchar(80)` 非空；`Category nvarchar(30)` 非空；`UnitPrice decimal(10,2)` >0；`IsActive bit` 默认 1 | PK `ProductCode`；名称不是可靠唯一键；正价格 CHECK |
| `Inventory` | 一个商品的一份当前库存快照 | `ProductCode varchar(12)`；`Quantity int` >=0；`UpdatedAt datetime2(0)` 默认当前时间 | PK 同时 FK 到 Product；每商品最多一个快照；非负 CHECK |
| `Member` | 一个自愿登记会员 | `MemberCode varchar(12)`；`DisplayName nvarchar(60)`；`Phone varchar(20)` 可空 | PK `MemberCode`；非空 Phone 通过过滤唯一索引做候选码；不要求匿名顾客登记 |
| `Employee` | 一位门店员工 | `EmployeeCode varchar(12)`；`DisplayName nvarchar(60)`；`JobTitle nvarchar(30)`；`IsActive bit` | PK `EmployeeCode` |
| `ShopOrder` | 一张订单 | `OrderNo varchar(24)`；`OrderedAt datetime2(0)`；`EmployeeCode varchar(12)`；`MemberCode varchar(12)` 可空；`Status varchar(12)` 默认 `COMPLETED` | PK `OrderNo`；店员 FK 必填；会员 FK 可空；订单号候选键；状态枚举 CHECK |
| `OrderLine` | 一张订单中的一个明细行 | `OrderNo varchar(24)`；`LineNumber smallint`；`ProductCode varchar(12)`；`Quantity int`；`UnitPrice decimal(10,2)` | 复合 PK `(OrderNo, LineNumber)`；FK 引用订单和商品；数量正数、成交价非负 CHECK；保存价格快照 |

## 样例关系（摘要）

- Product：`D001` 珍珠奶茶 12.00；`D002` 杨枝甘露 18.00；`D003` 柠檬茶 10.00。
- Inventory：D001 17、D002 9、D003 12（可售杯数快照，不追踪原料）。
- Member：M001 林同学（虚构）；M002 周同学（虚构）。
- Employee：E001 陈店员、E002 王店长（均虚构）。
- ShopOrder：一笔关联 M001 的完成单、一笔匿名完成单、一笔取消单。
- OrderLine：完成订单售出珍珠奶茶和杨枝甘露；柠檬茶只出现在取消单，因此完成销售汇总为零。

## 联系与基数

- Product 1—0/1 Inventory（本版要求每个样例商品有且仅有一行库存）。
- Employee 1—N ShopOrder；Member 0/1—N ShopOrder（订单可匿名）。
- ShopOrder 1—N OrderLine；Product 1—N OrderLine。
- ShopOrder 与 Product 是多对多关系，由 OrderLine 分解；价格与数量属于明细事实。
