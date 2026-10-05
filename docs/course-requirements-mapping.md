# 第一阶段课程要求对应表

本页按课程第一至第四周任务说明整理验收点与本仓库材料，供只克隆本仓库的读者理解项目范围。原始周任务讲解文件未复制进仓库；本阶段奶茶店数据库使用 `sql/02_seed.sql` 内的自包含样例，不读取本机的 `School.zip` 或父目录文件。

| 周次/要求 | 本项目对应内容 | 当前状态 |
| --- | --- | --- |
| 第 1 周：选择经营场景，确定角色、流程和数据边界 | `docs/requirements.md`；范围说明见根目录 `README.md` | 奶茶店标准饮品场景、店长/店员/会员与匿名顾客、业务流程和不纳入的数据已记录。小组成员与贡献按学习者要求暂缓填写，见 `docs/contribution.md`。 |
| 第 2 周：列出实体、属性/域、类型/长度/精度、空值、默认值、字段含义、PK/候选码/FK，并提供每表 2–3 行真实业务样例 | `docs/data-dictionary.md`、`docs/data-sources.md`、`sql/01_schema.sql`、`sql/02_seed.sql` | 关系模式、逐字段定义、键与约束已实现；样例数据已装载，但仅菜单产品名称/参考价来自公开页面，其他业务行均为虚构教学数据。因此“真实业务样例”这一项尚未满足，不能标为第二周全部完成。 |
| 第 3 周：从空库建表、装载数据，完成商品/库存/订单相关数据 CRUD 并能复现 | `sql/00_create_database.sql`–`sql/03_crud.sql`、`sql/09_update_public_menu.sql`、`README.md`、`result/00_create_database.txt`–`result/03_crud.txt` | 建库、六表、装载和 CRUD 已实现。`00`–`08` 曾从空库完整运行；菜单更新脚本 `09` 后来加入，随后在现存数据库重跑 `03`–`08`。当前最终版本的 `00`–`09` 尚未再次从空库整体复跑，详见 `docs/execution-notes.md`。 |
| 第 4 周：连接查询、聚合/HAVING/子查询、统计视图、完整性约束、最小角色权限和正反例 | `sql/04_queries.sql`–`sql/08_acceptance.sql`、`result/04_queries.txt`–`result/08_acceptance.txt` | 查询、三个视图、合法/非法约束验证和店员/店长权限均已实现并有 SQLCMD 结果；`03`–`08` 也在 SSMS 中实际运行并留有截图。此为分阶段运行证据，尚非当前最终脚本组合从空库的一次性复现。 |
| v0.1 交付：README、SQL、结果证据、阶段报告、AI 使用记录、组内分工 | 根目录 `README.md`、`sql/`、`result/`、`docs/stage-report.md`、`docs/ai_log.md`、`docs/contribution.md` | README、脚本、SQLCMD 输出、SSMS 截图、报告和 AI 使用摘要已在仓库；组内分工按学习者要求留待最后填写。因此交付材料主体已齐，v0.1 最终验收尚未完成。 |

## 复现证据的边界

成功执行以 SQL Server 2025 Express、SQLCMD 18、ODBC Driver 18 和 SSMS 22.10.12217.157 为当前已验证环境。仓库包含 SQL、种子数据和本轮 SSMS 截图，不包含 SQL Server/SSMS 安装程序。课程展示要求学习者能解释设计、人工复核 SQL 并现场演示；代码和日志本身不能证明个人掌握情况。
