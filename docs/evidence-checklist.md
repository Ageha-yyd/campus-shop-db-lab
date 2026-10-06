# 阶段一证据清单

2026-10-06当前版本的本机验证已完成。SQLCMD11步空库复跑记录见 `../result/verification.json`；完整输出为 `../result/00_create_database.txt` 至 `10_database_overview.txt`，执行顺序以清单为准。三个额外验证的文件哈希见 `../result/additional-verification.json`。

## 真实SSMS截图

| 截图 | 执行SQL | 可核对内容 |
| --- | --- | --- |
| [00_database_creation.png](../result/screenshots/00_database_creation.png) | 00 / master | 新库ONLINE与兼容级别；真实建库成功 |
| [01_schema.png](../result/screenshots/01_schema.png) | 01 | 六表结构与列数 |
| [01_seed.png](../result/screenshots/01_seed.png) | 02 | 每表至少三行，最终基线计数 |
| [01_public_menu.png](../result/screenshots/01_public_menu.png) | 09 | 六饮品参考价，不重写历史明细 |
| [01_database_and_tables.png](../result/screenshots/01_database_and_tables.png) | 10 | 当前数据库与六表概览 |
| [02_crud.png](../result/screenshots/02_crud.png) | 03 | 饮品与库存新增/修改等可见结果 |
| [02_crud_deletes.png](../result/screenshots/02_crud_deletes.png) | 03（滚动） | 删除行数、临时数据归零和回滚基线 |
| [03_queries.png](../result/screenshots/03_queries.png) | 04 | 多表完成单明细与销售汇总 |
| [04_views.png](../result/screenshots/04_views.png) | 05 | 订单明细/销售视图可见部分 |
| [05_constraints.png](../result/screenshots/05_constraints.png) | 06 | 合法/默认/NULL对照与前部反例，PASS13 |
| [05_constraints_details.png](../result/screenshots/05_constraints_details.png) | 06（滚动） | 后部反例及PASS13 |
| [06_clerk_permissions.png](../result/screenshots/06_clerk_permissions.png) | 07 | 店员和店长12项允许/拒绝，PASS12 |
| [08_acceptance.png](../result/screenshots/08_acceptance.png) | 08 | PASS；6表4视图6饮品7订单11明细86元 |
| [09_reporting.png](../result/screenshots/09_reporting.png) | 11 | 库存阈值与建议、零消费会员、零销量饮品 |
| [10_reporting_queries.png](../result/screenshots/10_reporting_queries.png) | 11（滚动） | HAVING边界与平均价业务子查询 |

截图manifest逐张保存来源SQL、源/图片SHA256、UTC采集时间、SSMS版本、数据库和真实成功状态。只裁掉账户窗口边缘，未改写查询/结果；可见区域未覆盖的结果应查SQLCMD完整输出。

## 复核命令

在仓库根目录PowerShell7运行：

```powershell
.\scripts\check-evidence.ps1
```

脚本核对当前11步源文件与输出、全部15张截图和额外验证记录，不重新创建数据库。需要重新截图时，安装中文界面的SSMS，按源文件运行；也可用 `scripts/capture-ssms.ps1`，通过-SsmsPath指定实际可执行文件，-SqlFile和-ImageName指定源文件和图片。该工具会真实打开SSMS、执行查询并只在成功时记录图片；建库/建表/seed需准备新库，其余回滚或只读脚本可重跑。

课堂演示时，按源SQL说明操作目的、返回行数和约束/权限的作用。
