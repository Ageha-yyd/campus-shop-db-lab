# 执行记录与修正

最终复现于 2026-10-03。先在 `master` 删除本轮专用的 `CampusShopV01`，随后从头执行 `00_create_database.sql` 至 `08_acceptance.sql`。九个 SQLCMD 命令均返回 0；最终断言 `PASS`。标准执行使用 SQLCMD `-f 65001` 读取 UTF-8，并在涉及过滤唯一索引的脚本中显式设定 SQL Server 所需 ANSI 选项。

迭代时发现并修正了以下问题；最终 `result/` 只保留最终复现输出及一份建表失败记录：

1. `LineNo` 在目标 T-SQL 解析中触发语法错误，改为 `LineNumber`。
2. SQLCMD 的默认 `QUOTED_IDENTIFIER` 设置不满足过滤唯一索引建表和写入要求；在 schema、seed、CRUD、约束脚本中显式设置 ANSI 选项，并以 `-f 65001` 运行。
3. 最初的负库存测试用已有商品键，数据库先以重复主键拒绝；改用合法对照事务内新增的临时商品，最终观察到 `CK_Inventory_Quantity_Nonnegative` 拒绝。

这些修正都针对运行证据完成。最终完整复现包括修正后的六类验证（CHECK、主键/候选唯一、FK、CRUD 回滚、权限允许/拒绝）与基线断言。
