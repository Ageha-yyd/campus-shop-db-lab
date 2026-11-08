# 详细图文版截图内容说明

D01至D21是报告使用的21个真实界面状态，步骤、输入、观察值、采集时间及SHA256见[详细浏览器记录](../detailed-browser.json)，图号见[逐图索引](../detailed-figure-index.md)。

同轮保存的完整页面如下；D系列为相应界面区域的独立真实截图，没有修改金额、状态或提示文字。

| 完整页面文件 | 步骤 | 截图内容 |
| --- | --- | --- |
| 01_login.png | W01 | 尚未登录的真实表单 |
| 02_login_error.png | W02 | 错误密码提交后的401友好通知和请求编号 |
| 03_customer_menu.png | W03 | customer成功登录、六种菜单与角色入口 |
| 04_customer_draft.png | W04 | D001两杯和D003一杯草稿，16元 |
| 05_clerk_confirmed.png | W07 | 店员确认同一草稿，三杯D001加一杯D003，共22元 |
| 06_clerk_stock.png | W08 | 扣库后D001为17杯、D003为4杯；店员只读 |
| 07_admin_products.png | W10 | UI_TEST新增后改价至4元，商品维护页面 |
| 08_constraint_error.png | W11 | 再次新增相同UI_TEST编号，实际唯一约束冲突 |
| 09_admin_inventory.png | W12 | 管理员将UI_TEST盘点至8杯 |
| 10_sales.png | W15 | 确认后、取消前销售；六行求和为19杯108元 |
| 11_connection_error.png | W16 | 临时不可达连接触发503，界面只显示友好通知 |
| 12_mobile_login.png | W21 | 390×844视口完整页面；允许纵向滚动，无横向溢出 |

S01、S02、S03及T01的PNG是实际执行输出的只读核验页截图，页面已明确标注不是SSMS或原生终端截图。原文来自真实SQLCMD/pytest子进程输出，命令、时间、退出码、原始TXT/XML、SHA256和对应行号见[运行清单](../detailed-runs/manifest.json)。

报告30幅图包括2张ER设计图、21张上述界面状态和7张输出核验页。S02剩余两张核验页保留完整业务结果表，正文选用包含13项断言的第一页。
