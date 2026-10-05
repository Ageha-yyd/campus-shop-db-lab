# 阶段一 v0.1：校园奶茶店数据库原型

本仓库是一个独立的数据库课程实验小项目，覆盖第一阶段第 1–4 周的主体实现。SQL、说明和阶段证据已整理；课程验收尚未全部闭环：第二周要求的真实业务样例数据尚未提供，当前最终脚本组合尚未再次从空库完整复跑，组内分工留待本人填写。下文区分已实现、已验证和待完成事项。

## 场景与范围

场景固定为校园奶茶店。首版只经营菜单里的标准饮品，记录饮品、可售杯数快照、订单、订单明细、可选会员和员工；顾客可匿名购买。糖度、冰量、加料、配方和原料库存暂不纳入，避免把点单定制和后厨库存带入首版。支付卡号、登录凭据、采购和补货也不纳入。饮品名称与菜单价参考公开网页，来源及边界见 `docs/data-sources.md`；库存、订单、成交、人员和会员信息均为**虚构教学数据**。

`docs/requirements.md` 记业务流程、角色、数据边界和未决问题；`docs/data-dictionary.md` 记行粒度、属性/域、码与样例。

## 环境

- 已验证引擎：Microsoft SQL Server 2025 Express (`SQLEXPRESS`)，Windows 集成身份验证，本机共享内存连接。
- 执行工具：SQLCMD 18 + Microsoft ODBC Driver 18；该本机实例使用自签名证书，因此复现命令带 `-C` 信任本机证书。仅供本机实验，不作为远程/生产连接建议。
- SSMS 22.10.12217.157 已安装，并已用 Windows 集成身份验证连接本机实例。`03`–`08` 脚本已在 SSMS 实际执行，真实界面结果截图见 `result/screenshots/`；SQL Server 2022 / SSMS 19.3 的课程安装路径未在此机验证。
- `result/` 保存 SQLCMD 输出文本、服务器版本摘要和 SSMS 实际运行截图。截图裁去了窗口标签/状态栏边缘中的本机账户标识，没有改写查询内容或结果。

## 从空库复现

在 PowerShell 当前目录设为 `sql`，用已获本机 SQL Server 权限的 Windows 用户打开终端：

```powershell
$sqlcmd = 'C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\180\Tools\Binn\SQLCMD.EXE'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -i '00_create_database.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '01_schema.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '02_seed.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -i '09_update_public_menu.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '03_crud.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '04_queries.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '05_views.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '06_constraints.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '07_roles.sql'
& $sqlcmd -S '.\SQLEXPRESS' -E -C -f 65001 -b -d MilkTeaShopV01 -i '08_acceptance.sql'
```

`00_create_database.sql` 只创建名为 `MilkTeaShopV01` 的新库；如果同名库已存在会停止，不会覆盖。要重新从空库演练，先在 SSMS 明确确认目标确为本实验库，再由有权限的操作者单独删除它，然后按上述顺序执行。schema 与 seed 是首次初始化脚本；不要对含有其他数据的库运行。

## 目录

- `sql/00_create_database.sql`：创建独立数据库。
- `sql/01_schema.sql`：六张表、主键、候选键、外键、域与默认约束。
- `sql/02_seed.sql`：公开菜单参考饮品与虚构业务样例数据。
- `sql/03_crud.sql`：可重跑的事务内增删改查演示，最后回滚到基线。
- `sql/04_queries.sql`：连接、聚合、HAVING、子查询和业务口径查询。
- `sql/05_views.sql`：订单明细、商品销量和库存状态三个视图。
- `sql/06_constraints.sql`：合法写入与重复键、孤儿外键、负库存、非法价格等拒绝反例。
- `sql/07_roles.sql`：最小权限角色与成功/拒绝操作验证。
- `sql/08_acceptance.sql`：核对最终样例基线、视图结果和临时数据清理。
- `sql/09_update_public_menu.sql`：把既有阶段一样例菜单更新到有来源记录的公开参考价；仅匹配本项目三款饮品和固定虚构订单，发现基线不符会停止。
- `sql/10_database_overview.sql`：只读查看当前数据库和六张业务表。
- `result/`：实际 SQLCMD 运行记录。
- `docs/`：需求、数据字典、阶段报告、AI 使用记录、组内分工和执行修正记录。
- `docs/data-sources.md`：公开菜单数据引用与虚构交易数据边界。
- `docs/course-requirements-mapping.md`：第一至第四周课程要求与本项目文件的对应表。
- `docs/evidence-checklist.md`：课程要求的 SSMS 截图清单及对应 SQL 脚本。

## 当前状态与验收边界

主体功能已实现：建库、六表、样例装载、CRUD、查询、视图、约束和角色权限均有 SQL 脚本与运行证据。验证范围是：`00`–`08` 曾在 SQL Server 2025 Express 上从新库完整执行；之后菜单切换为有来源的公开参考价，在原有样例库运行带基线保护的 `09`，再重新执行 `03`–`08`；SQLCMD 与之后的 SSMS 执行均有成功记录，验收脚本返回 `PASS`。这组记录是初次空库执行加后续增量验证，不代表当前仓库最终版本已经从空库完整复跑过 `00`–`09`。`result/screenshots/` 保存了 SSMS 阶段结果画面。

按原始课程要求，当前验收状态仍有三项待完成：第二周要求每表提供真实业务样例，当前除公开菜单商品名/参考价外，订单、库存、会员和员工等均为虚构教学数据；当前最终脚本组合尚未再次从空库完整复跑；组内分工待本人填写。公开菜单来源不是官方报价，不能替代真实交易记录。SQL Server 2022、个性化点单、原料库存、支付、采购补货、库存流水、并发与事务工作流不在本版验收范围内。CRUD 演示在显式事务中回滚，因此反复运行不会改变固定样例基线。

## 后续待本人确认

课程要求列出小组分工，但尚未提供组员姓名和实际分工；见 `docs/contribution.md`，不能由 AI 虚构。菜单商品名和标价取自公开网页，其他业务数据为虚构教学样例；来源与真实性边界见 `docs/data-sources.md`。AI 使用和人工复核边界见 `docs/ai_log.md`。

## 项目独立性

本仓库仅保存该实验项目的代码、说明和复现证据。第一至第四周的要求摘要与对应文件见 `docs/course-requirements-mapping.md`；原始课件与 School 数据未纳入仓库，当前奶茶店样例不依赖它们。菜单数据来源与虚构数据边界见 `docs/data-sources.md`。结果记录已去除本机名称和账户标识。

