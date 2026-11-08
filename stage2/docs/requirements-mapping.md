# 第五至第九周验收对应

详细图文版将正文结论与步骤W01至W21、SQL执行S01至S03、集成执行T01对应；原图、命令、输出和逐图索引见result/detailed-figure-index.md及detailed-runs/manifest.json。

| 周次 | 要求 | 交付与实证 |
| --- | --- | --- |
| 5 | 实体 属性 主码 候选码 外码 | design.md、data-dictionary.md，er-v01.svg、er-v10.svg 与 PNG |
| 5 | 1:1 1:N M:N 与参与约束 | design.md 业务规则表，图标 min..max；明细关联实体和最低一行由过程实现 |
| 5 | v0.1 问题 保留理由 多商品 会员 散客 库存映射 | design.md 问题清单、浏览器完整流程与基线回归 |
| 6 | 全部候选码 FD 1NF 2NF 3NF 异常 | design.md 逐表分析，normalization_demo.sql 和实际输出 |
| 6 | 目标关系 无损 依赖保持 冗余取舍 | design.md 分解证明及历史成交价解释 |
| 6 | 先副本再迁移 数据保留 恢复 | setup.py、migration.sql、migration-guide.md、setup.json |
| 6 | 明细 销量 库存 金额 权限回归 | regression.sql 的13项断言、result/regression.txt，before-after.json |
| 7-9 | Web 框架 页面→服务→DAO→SQL Server | Flask web/app.py、service.py、dao.py、templates/、static/、sql/ |
| 7-9 | 登录 商品库存订单及明细 CRUD | 三角色 UI；products/inventory/orders API；草稿明细整单更新/删行，草稿删除；完成单保留历史 |
| 7-9 | 店员 顾客 管理员权限一致 | 后端角色和所有权、应用角色 SQL 拒绝；pytest 真实数据库权限用例 |
| 7-9 | 参数化 SQL 事务与资源释放 | dao.py 的 ? 参数、contextmanager commit/rollback/finally close；库存锁与并发用例 |
| 7-9 | 统一错误 前端友好 后端可追踪 | app.py 一处异常处理；request_id/time/operation/role/code/result；connection_error 和 constraint_error 截图 |
| 7-9 | 正常和错误集成测试 从空环境复现 | tests/、browser_acceptance.py；pytest.xml/txt、browser-acceptance.json、package-replay.json |
| 阶段 | 操作手册 报告 ai_log 分工 | README.md、user-manual.md、阶段报告.docx/pdf、ai_log.md、contribution.md |

运行日志用 UTC；课程交付日期按用户本地日期 2026年11月8日。所有证据需区分真实数据库错误、浏览器操作、显式故障注入与人工复核；人工尚未确认的组内执行不写成已发生。
