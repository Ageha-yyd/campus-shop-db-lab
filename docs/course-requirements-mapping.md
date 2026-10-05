# 第一阶段课程要求对应表

本页按课程第一至第四周任务说明整理验收点与本仓库材料，供只克隆本仓库的读者理解项目范围。原始周任务讲解文件未复制进仓库；本阶段奶茶店数据库使用 `sql/02_seed.sql` 内的自包含样例，不读取本机的 `School.zip` 或父目录文件。

| 周次/要求 | 本项目对应内容 | 当前状态 |
| --- | --- | --- |
| 第 1 周：选择经营场景，确定角色、流程和数据边界 | `docs/requirements.md`；范围说明见根目录 `README.md` | 奶茶店标准饮品场景、店长/店员/会员与匿名顾客、业务流程和不纳入的数据已记录。小组成员与贡献按学习者要求暂缓填写，见 `docs/contribution.md`。 |
| 第 2 周：列出实体、属性/域、类型/长度/精度、空值、默认值、字段含义、PK/候选码/FK，并提供样例元组 | `docs/data-dictionary.md`、`sql/01_schema.sql`、`sql/02_seed.sql` | 六个关系、逐字段解释及约束已列明；样例数据为虚构教学数据。任务说明提及真实业务数据，提交前需确认是否接受虚构样例；不要公开未经授权的真实身份或联系方式。 |
| 第 3 周：从空库建表、装载数据，完成商品/库存/订单相关数据 CRUD 并能复现 | `sql/00_create_database.sql`–`sql/03_crud.sql`、`README.md`、`result/00_create_database.txt`–`result/03_crud.txt` | 建库、六表和样例数据已实现；CRUD 演示分别覆盖 Product、Inventory、ShopOrder、OrderLine 的新增、读取、修改和删除，操作在事务中回滚。00–08曾从空库完整运行；本轮修改后又重跑03、07和08，详见 `docs/execution-notes.md`。 |
| 第 4 周：连接查询、聚合/HAVING/子查询、统计视图、完整性约束、最小角色权限和正反例 | `sql/04_queries.sql`–`sql/08_acceptance.sql`、`result/04_queries.txt`–`result/08_acceptance.txt` | 查询、三个视图、合法/非法约束验证和店员/店长角色均已实现；店员新增订单头和明细的成功结果及越权拒绝结果有文本记录，验收脚本返回 `PASS`。 |
| v0.1 交付：README、SQL、结果证据、阶段报告、AI 使用记录、组内分工 | 根目录 `README.md`、`sql/`、`result/`、`docs/stage-report.md`、`docs/ai_log.md`、`docs/contribution.md` | README、脚本、文本执行证据、报告和 AI 使用摘要已在仓库。课程要求的 SSMS 图形界面截图尚未采集，清单见 `docs/evidence-checklist.md`。组内分工留待最后填写。 |

## 复现证据的边界

成功执行以 SQL Server 2025 Express、SQLCMD 18 和 ODBC Driver 18 为当前已验证环境。仓库包含 SQL 和种子数据，不包含 SQL Server/SSMS 安装程序，也不包含 SSMS 截图。课程展示要求学习者能解释设计、人工复核 SQL 并现场演示；代码和日志本身不能证明个人掌握情况。
