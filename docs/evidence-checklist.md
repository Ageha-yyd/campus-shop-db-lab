# SSMS 截图证据清单

`result/` 同时保存 SQLCMD 文本日志和 SSMS 实际运行截图。课程第一阶段的图形界面证据已按以下清单采集；截图来自已安装的 SSMS 22.10.12217.157，连接本机 SQL Server 2025 Express。不得把日志排版成图片冒充 SSMS。

截图保存在 `result/screenshots/`。不要截入 Windows 用户名、私人路径、服务器凭据或其他无关个人信息；现有截图裁去了窗口标签和状态栏边缘，保留真实查询与结果。

| 文件名 | 运行内容与画面应能证明 |
| --- | --- |
| `01_database_and_tables.png` | 执行 `sql/10_database_overview.sql`，显示当前数据库名、表数和六张业务表清单。 |
| `02_crud.png`、`02_crud_deletes.png` | `sql/03_crud.sql` 的商品、库存、订单头和订单明细增删改查结果；分别展示写入/更新和删除后回滚至基线。 |
| `03_queries.png` | `sql/04_queries.sql` 的连接、聚合、HAVING、子查询和订单汇总查询结果。 |
| `04_views.png` | `sql/05_views.sql` 中订单明细、饮品销量、库存状态三个视图的查询结果。 |
| `05_constraints.png` | `sql/06_constraints.sql` 中合法写入成功、非法值/重复键/孤儿外键被拒绝，且最终临时数据已回滚或清理。 |
| `06_clerk_permissions.png` | `sql/07_roles.sql` 中店员成功新增订单头与订单明细，并被拒绝修改商品、读取员工表、删除商品。 |
| `07_manager_permission.png` | `sql/07_roles.sql` 中店长执行获准的菜单维护操作。 |
| `08_acceptance.png` | `sql/08_acceptance.sql` 返回 `PASS`，数据库与视图基线符合预期。 |

执行顺序、数据库实例和 SQLCMD 复现方式见根目录 `README.md`。通过 SSMS 复跑后，请保留这些真实截图，并将结果目录中 SQLCMD 日志作为可读文本证据一并保留。
