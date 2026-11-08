# 详细图文版逐图证据索引

图1和图2为ER设计图；以下为实际运行截图及真实输出核验页。

| 图号 | 步骤 | 截图内容 | 原始证据 |
| --- | --- | --- | --- |
| 3 | S03_normalization | 规范化异常和分解演示 输出第1至13行 | [S03_normalization-1.png](detailed-screenshots/S03_normalization-1.png) |
| 4 | S01_baseline | SQL基线和业务数值核验 输出第1至18行 | [S01_baseline-1.png](detailed-screenshots/S01_baseline-1.png) |
| 5 | S01_baseline | SQL基线和业务数值核验 输出第19至31行 | [S01_baseline-2.png](detailed-screenshots/S01_baseline-2.png) |
| 6 | S02_regression | 迁移与权限SQL回归 输出第1至18行 | [S02_regression-1.png](detailed-screenshots/S02_regression-1.png) |
| 7 | W01 | 登录界面 | [D01_login.png](detailed-screenshots/D01_login.png) |
| 8 | W02 | 错误密码反馈 | [D02_wrong_login.png](detailed-screenshots/D02_wrong_login.png) |
| 9 | W03 | 顾客菜单与角色入口 | [D03_customer_menu.png](detailed-screenshots/D03_customer_menu.png) |
| 10 | W04 | 保存多商品会员草稿 | [D04_draft.png](detailed-screenshots/D04_draft.png) |
| 11 | W05 | 修改草稿并重新计算 | [D05_edited_draft.png](detailed-screenshots/D05_edited_draft.png) |
| 12 | W07 | 店员确认后的同一订单 | [D07_confirmed.png](detailed-screenshots/D07_confirmed.png) |
| 13 | W08 | 实际扣库与库存预警 | [D08_deducted_stock.png](detailed-screenshots/D08_deducted_stock.png) |
| 14 | W06 | 不同顾客订单隔离 | [D06_guest_isolation.png](detailed-screenshots/D06_guest_isolation.png) |
| 15 | W09 | 顾客看到店员确认结果 | [D09_customer_completed.png](detailed-screenshots/D09_customer_completed.png) |
| 16 | W19 | 散客也能建立草稿 | [D19_guest_draft.png](detailed-screenshots/D19_guest_draft.png) |
| 17 | W20 | 删除草稿及其明细 | [D20_deleted_draft.png](detailed-screenshots/D20_deleted_draft.png) |
| 18 | W10 | 新增商品与修改价格 | [D10_product.png](detailed-screenshots/D10_product.png) |
| 19 | W12 | 管理员盘点库存 | [D12_inventory_eight.png](detailed-screenshots/D12_inventory_eight.png) |
| 20 | W13 | 删除零库存记录 | [D13_deleted_inventory.png](detailed-screenshots/D13_deleted_inventory.png) |
| 21 | W14 | 删除没有订单引用的商品 | [D14_deleted_product.png](detailed-screenshots/D14_deleted_product.png) |
| 22 | W15 | 完成订单计入销售统计 | [D15_sales.png](detailed-screenshots/D15_sales.png) |
| 23 | W17 | 取消后保留订单历史 | [D17_cancelled.png](detailed-screenshots/D17_cancelled.png) |
| 24 | W18 | 取消后的实际库存恢复 | [D18_restored_stock.png](detailed-screenshots/D18_restored_stock.png) |
| 25 | W11 | 真实唯一约束冲突 | [D11_constraint.png](detailed-screenshots/D11_constraint.png) |
| 26 | W16 | 真实连接失败的友好反馈 | [D16_connection.png](detailed-screenshots/D16_connection.png) |
| 27 | W21 | 390像素宽移动布局的登录页 | [D21_mobile.png](detailed-screenshots/D21_mobile.png) |
| 28 | T01_pytest | 真实SQL Server集成测试 输出第1至18行 | [T01_pytest-1.png](detailed-screenshots/T01_pytest-1.png) |
| 29 | T01_pytest | 真实SQL Server集成测试 输出第19至36行 | [T01_pytest-2.png](detailed-screenshots/T01_pytest-2.png) |
| 30 | T01_pytest | 真实SQL Server集成测试 输出第37至52行 | [T01_pytest-3.png](detailed-screenshots/T01_pytest-3.png) |

每图的操作和结果解释位于报告相邻正文。图号与detailed-report-source.json一致；21个界面状态另附detailed-browser.json的动作、时间、SHA256及相邻实际HTTP记录。

SQL和pytest图片为实际输出核验页。命令与逐字输出见detailed-runs/manifest.json及同目录TXT/XML；图片只裁去空白边缘，不改写结果。
