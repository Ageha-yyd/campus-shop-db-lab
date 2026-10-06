# 实验结果入口

本目录保存完整SQLCMD输出、验证记录及15张真实SSMS截图。截图导航见 [截图清单](../docs/evidence-checklist.md)，完整设计说明见 [阶段报告](../docs/stage-report.md)。

| 验收内容 | 截图 | 完整输出 |
| --- | --- | --- |
| 成功建库、结构与数据 | screenshots/00_database_creation.png、01_schema.png、01_seed.png、01_database_and_tables.png | 00_create_database.txt、01_schema.txt、02_seed.txt、10_database_overview.txt |
| 当前菜单更新 | screenshots/01_public_menu.png | 09_update_public_menu.txt |
| CRUD正常用例、前后变化、删除与回滚 | screenshots/02_crud.png、02_crud_deletes.png | 03_crud.txt |
| 关键业务查询 | screenshots/03_queries.png、10_reporting_queries.png | 04_queries.txt、12_reporting_evidence.txt |
| 不同统计视图 | screenshots/04_views.png、09_reporting.png | 05_views.txt、12_reporting_evidence.txt |
| 合法数据与非法数据 | screenshots/05_constraints.png、05_constraints_details.png | 06_constraints.txt：PASS13 |
| 店员、店长、正常授权与越权访问 | screenshots/06_clerk_permissions.png | 07_roles.txt：PASS12 |
| 最终原型验收 | screenshots/08_acceptance.png | 08_acceptance.txt：PASS |

上表截图文件均在screenshots目录。源SQL和图片哈希见screenshots/manifest.json；主流程记录见verification.json。额外验证包括同名库保护、补充报表、历史价保留。result/reproducibility.json记录独立目录重建方式；submission-verification.json记录本次提交包演练。

从空库运行会更新主流程文本输出和verification.json。截图是此前当前SQL的SSMS实跑证据，可通过scripts/check-evidence.ps1核对，不会在SQLCMD运行中重新生成。
