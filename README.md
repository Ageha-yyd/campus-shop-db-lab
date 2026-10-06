# 校园奶茶店数据库 v0.1

小组成员：袁远冬、陆乐天、罗金浩。仓库维护人：袁远冬。

**先阅读 [阶段报告.pdf](阶段报告.pdf) 或 [阶段报告.docx](阶段报告.docx)。** 报告按“一、设计思路；二、实验过程；三、实验总结”组织。

## 项目范围、角色与流程

校园单店出售固定标准饮品。六表记录菜单、可售杯数快照、会员、员工、订单头及明细；保留历史成交价，销售统计仅计算完成订单。每款饮品有独立预警阈值，杯数达到或低于阈值时建议补足到两倍阈值。

本阶段不展开糖冰加料、原料配方、采购、支付退款和积分。库存是盘点快照，不随下单自动扣减；具体信息边界、表与键的设计理由见阶段报告第一部分。

| 角色 | 业务职责与权限 |
| --- | --- |
| 店员 | 查看菜单、库存、订单/销量/库存报表，新增订单头和明细；不能改价、改库存或读取会员资料/汇总。 |
| 店长 | 维护六张业务表，读取四个视图，包括会员消费汇总；不授予db_owner。 |
| 会员或匿名顾客 | 选择饮品、杯数和可选会员编号，由店员代录，不直接连接数据库。 |

业务流程：**选择饮品与杯数 → 选择会员或匿名 → 保存订单头和成交价明细 → 查看完成销售 → 盘点并查看预警建议**。取消单保留记录但不计销售。

## 文件与验收清单

| 验收项 | 文件与结果 |
| --- | --- |
| 设计思路、实验过程、实验总结 | 根目录阶段报告.docx / 阶段报告.pdf |
| 全部字段的类型、长度、精度、空值、默认值、域、含义及码；每表样例 | [数据字典](docs/data-dictionary.md)，SQL01/02；六表每表至少3行 |
| 建库、建表、样例装载 | sql/00、01、02、09；result内建库/结构/装载截图与文本输出 |
| 分表CRUD与修改前后、删除结果 | sql/03；02_crud.png、02_crud_deletes.png及03_crud.txt |
| 连接、聚合、GROUP BY/HAVING、业务子查询 | sql/04、11；03_queries.png、10_reporting_queries.png及对应输出 |
| 四种视图 | sql/05；04_views.png、09_reporting.png；订单、销量、库存、会员汇总 |
| 完整性正反例 | sql/06；05_constraints.png、05_constraints_details.png；PASS13 |
| 不同角色授权与越权拒绝 | sql/07；06_clerk_permissions.png及07_roles.txt；PASS12 |
| 最终验收与复现 | sql/08、10，复现.ps1；08_acceptance.png及08_acceptance.txt |
| AI建议、修改与验证结论 | [ai_log](docs/ai_log.md) |
| 三人职责与成果对应 | [组内分工](docs/contribution.md) |

第1周的场景、流程与边界，第2周的关系/字典/码与样例，第3周的建库和分表CRUD，第4周的查询/视图/约束/权限均已纳入。截图及完整输出的阅读顺序见 [结果说明](result/README.md)，截图统一在result/screenshots目录。

## 脚本执行顺序

| 顺序 | SQL文件 | 作用 |
| --- | --- | --- |
| 1 | 00_create_database.sql | 建库，连接master |
| 2 | 01_schema.sql | 六表、键、字段完整性约束 |
| 3 | 02_seed.sql | 每表至少三行关联样例 |
| 4 | 09_update_public_menu.sql | 当前菜单参考价，不改历史成交价 |
| 5 | 03_crud.sql | 饮品、库存、订单及明细增读改删 |
| 6 | 04_queries.sql | 连接、统计、HAVING和子查询 |
| 7 | 05_views.sql | 四个业务视图 |
| 8 | 06_constraints.sql | 合法/非法数据对照 |
| 9 | 07_roles.sql | 角色及允许/拒绝操作 |
| 10 | 08_acceptance.sql | 基线和边界结果断言 |
| 11 | 10_database_overview.sql | 数据库与结构概览 |

即00→01→02→09→03→04→05→06→07→08→10。SQL11是补充报表，主流程完成后可单独执行；四周要求中的query/view/constraint/role分别对应04/05/06/07。

## 从空库复现

1. 安装SQL Server、ODBC版SQLCMD和ODBC Driver；当前Windows账户须有建库权限。本机已验证SQL Server 2025 Express 17.0.1000.7、SQLCMD/ODBC18及SSMS22，其他版本尚未实测。
2. 解压后进入README所在目录，确认没有MilkTeaShopV01同名库。已有库需先备份并保留/改名；脚本不会自动删除数据库，也不会覆盖已有库时的日志。
3. 在PowerShell 7运行：

```powershell
.\复现.ps1 -ServerInstance '.\SQLEXPRESS'
```

SQLCMD不在PATH时，追加 `-SqlcmdPath '实际的SQLCMD.EXE路径'`。连接使用Windows集成认证和UTF-8，`-C`用于信任本机实验实例证书。脚本读取SQL实例默认数据目录，无固定本机数据路径。

4. 核对11步成功、约束PASS13、权限PASS12及最终PASS。六表计数为6/6/4/3/7/11，四个视图，完成销售6单、15杯、86.00元。CRUD与约束/权限试验写入均回滚。
5. 结果文本写入result目录，运行摘要为复现记录.txt；原始15张SSMS截图保留。单独执行SQL时，00连接master，其余连接MilkTeaShopV01。

**样例全部位于sql/02_seed.sql，复现无需data目录、CSV、JSON、网页或父目录文件。**

## 仓库补充资料

仓库保留需求分析、整合过程、技术校验JSON和维护脚本，供开发时使用；提交包只包含上述课堂材料。运行 `.\scripts\package-submission.ps1` 生成精简提交ZIP。完整校验入口仍是scripts/check-evidence.ps1。
