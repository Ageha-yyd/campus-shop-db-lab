# 第二阶段结果阅读入口

最新成果为[详细图文版报告](../阶段报告_详细图文版.pdf)及[逐图证据索引](detailed-figure-index.md)。21个实际界面状态覆盖W01至W21，均有操作、输入和结果解释；SQL和pytest图片明确标为实际输出核验页，原始TXT/XML与执行命令、时间、退出码、SHA256保留在[detailed-runs](detailed-runs/manifest.json)。

本轮补采：43例集成重新通过、13项SQL通过、18项真实浏览器检查通过、60次HTTP记录与公开日志请求编号对应。收尾原库/演示库/测试库原字段对照见detailed-final-validation.json；报告排版核验见detailed-report-validation.json。历史报告在仓库保留，最终提交包只放最新详细图文版；旧验收记录用于追溯，不与本轮截图混作同一订单。

| 课程要求 | 证据 |
| --- | --- |
| ER图、联系名称、基数与参与 | [v0.1源图](../docs/er-v01.svg)、[导出图](../docs/er-v01.png)；[v1.0源图](../docs/er-v10.svg)、[导出图](../docs/er-v10.png) |
| 逐表FD、范式、更新异常、保留及分解 | [规范化分析](../docs/design.md)、normalization-demo.txt；假设关系与实际项目分别说明 |
| 迁移前基准和实际差异 | before-after.json，六表原字段逐行/哈希对照；订单明细、销量、库存expected/actual |
| SQL回归 | regression.txt，13项真实SQL断言，含合法及非法写入与权限 |
| API、数据库及扩展交叉场景 | pytest.txt/xml；course-audit-tests.xml及course-audit-after.txt |
| 第二次核查的修订依据 | course-audit.json；[课程核查结论](../docs/course-review.md) |
| 不同角色的Web完整流程 | browser-acceptance.json、browser-console.txt、screenshots/原始截图 |
| 错误分类与追踪 | log-evidence.jsonl只含脱敏字段；详细错误日志仅留本机 |
| 独立解压复现 | package-replay.json、package-pytest.txt/xml、package-regression.txt、package-cleanup.txt |
| 文档排版与来源 | 最新detailed-report-validation.json、detailed-report-source.json；旧版report-validation.json、report-source.json保留追溯 |

所有结果应与对应脚本和当前提交共同阅读。40001分类测试及复核日志测试采用显式故障注入；库存、并发、约束和连接失败分别有真实SQL或实际连接证据。人工分工复核仍需同学实际操作填写，不用自动化结果代签。
