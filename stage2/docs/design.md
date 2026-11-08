# 第二阶段设计说明

## 设计边界与第五周问题清单

沿用校园单店、标准饮品、按可售杯数盘点的范围。不扩展糖冰加料、原料配方、支付退款和采购。

| v0.1 证据 | 影响 | v1.0 处理 |
| --- | --- | --- |
| Product、Inventory、Member、Employee、ShopOrder、OrderLine 分表，明细以订单号和行号联合标识 | 已避免把商品名、会员名、员工名重复写入订单 | 保留六表和全部业务样例 |
| Category 仅为一个原子类别名称，无类别编号或其他类别属性 | 不存在 CategoryCode→CategoryName 的传递依赖 | 不为了增加表数而拆表；用独立关系演示规范化 |
| 无应用账号，顾客由店员代录 | 无法登录及限制顾客可见订单 | 增加 AppUser，用户名唯一，密码哈希；关联员工或可选会员 |
| ShopOrder 的 EmployeeCode 必填，状态只有完成或取消 | 顾客提交前无法保存待确认订单 | 新增 DRAFT；顾客草稿可暂无员工，确认时填入员工 |
| 外码只保证明细引用订单，不能保证订单有明细 | 裸写订单头可能形成空单 | 通过受限过程一次保存头和非空明细；确认前再次检查 |
| Inventory 是盘点快照，不自动扣减 | 应用确认后库存会与销售脱节 | 仅 v1.0 新订单确认时事务扣减；StockApplied 区分开库库存与新增扣减 |
| 原角色是课堂 EXECUTE AS 演示用户 | 隐藏按钮不能限制真实 SQL | 后端复核角色；DAO 激活密码应用角色，再运行业务 SQL；禁止连接池和角色恢复 cookie |

## 关系与标识

Product 一行是一种标准饮品；Inventory 一行是该饮品当前可售杯数；Member 一行是会员；Employee 一行是工作人员；ShopOrder 一行是订单头；OrderLine 一行是某订单中第 LineNumber 行；AppUser 一行是可登录账号。SchemaVersion 为迁移元数据，Baseline_* 为只读回归快照，不作为业务实体。

| 关系 | 主码及候选码 | 外码及可选标识 |
| --- | --- | --- |
| Product | ProductCode | 无。商品名不保证唯一，不是候选码 |
| Inventory | ProductCode，兼外码 | →Product.ProductCode |
| Member | MemberCode | 非空 Phone 由过滤唯一索引约束；Phone 可空，不能当作全关系候选码 |
| Employee | EmployeeCode | 姓名与职称均不能唯一标识员工 |
| ShopOrder | OrderNo | EmployeeCode 可空→Employee；MemberCode 可空→Member；CreatedByUserId 可空→AppUser |
| OrderLine | (OrderNo, LineNumber) | OrderNo→ShopOrder；ProductCode→Product；(OrderNo,ProductCode) 不唯一，同饮品允许多行 |
| AppUser | UserId；Username 也是候选码 | EmployeeCode 可空→Employee；MemberCode 可空→Member；两个非空过滤唯一索引限制一个员工或会员最多绑定一个账号 |

## 业务规则与映射

这里“某实体对应另一实体 0..N”表示一条该实体记录可关联到的另一端记录数。图采用带 min..max 标签的关系连线，一端标识处的数字表示另一端单条记录对应此端的最小和最大数。PK 主码，AK 候选码，FK 外码，? 可空。

| 联系及适用条件 | 两端最小与最大基数 | 映射与实现 |
| --- | --- | --- |
| Product 与 Inventory | 一商品 0..1 库存；一库存恰好 1 商品 | Inventory 的共享主码/外码。新商品自动建零库存；管理员可删零库存，因此明确可选 |
| Product 与 OrderLine | 一商品 0..N 明细；一明细恰好 1 商品 | OrderLine.ProductCode FK。被引用商品硬删除由 FK 拒绝，可下架 |
| ShopOrder 与 OrderLine | 一订单业务上 1..N 明细；一明细恰好 1 订单 | 复合主码+FK；非空订单由服务/过程保证，FK 单独不能保证最低 1 |
| Employee 与 ShopOrder | 一员工 0..N 订单；v0.1 一订单恰好 1 员工；v1.0 草稿 0..1，完成时 1 | ShopOrder.EmployeeCode FK；确认过程填写账号对应员工 |
| Member 与 ShopOrder | 一会员 0..N 订单；一订单 0..1 会员 | 可空 MemberCode FK。散客为 NULL，顾客不能指定别人的会员号 |
| AppUser 与 ShopOrder | 一账号 0..N 订单；一订单 0..1 创建账号 | CreatedByUserId FK；历史订单 NULL，新应用订单必填并用于顾客所有权过滤 |
| Employee 与 AppUser | 一员工 0..1 账号；一账号 0..1 员工 | 非空唯一 EmployeeCode FK；admin/clerk 必须绑定员工 |
| Member 与 AppUser | 一会员 0..1 账号；一账号 0..1 会员 | 非空唯一 MemberCode FK；customer 可绑定会员或为散客，员工角色不绑定会员 |

Product 与 ShopOrder 的 M:N 通过 OrderLine 关联实体实现，并保留 Quantity 与历史 UnitPrice。AppUser 的员工与会员关联是角色条件下的可选联系，不能误画成每个账号都必须关联两者。

## 第六周函数依赖与范式

函数依赖来自业务规则，而非有限样例的偶然唯一。下表的“其余属性”均指同一关系内其余字段，详细字段类型见数据字典。

| 表 | 主要非平凡函数依赖 | 插入 修改 删除异常与结论 |
| --- | --- | --- |
| Product | ProductCode→ProductName,Category,UnitPrice,RestockThreshold,IsActive | 可独立新增；改当前价不改成交价；订单引用时不能误删。单属性码，无部分依赖，无已知非码决定因素，BCNF |
| Inventory | ProductCode→Quantity,UpdatedAt | 产品与库存分离；盘点只改一行；删零库存不删商品。BCNF |
| Member | MemberCode→DisplayName,Phone,JoinedAt | 会员可独立存在；改名只改会员表；被引用时限制删除。非空电话唯一是条件域约束，非全域候选码。BCNF |
| Employee | EmployeeCode→DisplayName,JobTitle,IsActive | 员工独立存在、改名一处维护、历史订单保留员工引用。BCNF |
| ShopOrder | OrderNo→OrderedAt,EmployeeCode,MemberCode,Status,CreatedByUserId,StockApplied | 非空明细由事务流程维护；不存重复总额，金额由明细求和。StockApplied 不由 Status 单独决定，历史与新增完成单可能取不同值。BCNF |
| OrderLine | (OrderNo,LineNumber)→ProductCode,Quantity,UnitPrice | 非主属性依赖完整联合码；OrderNo 不决定饮品和单价，ProductCode 不决定历史成交价，同一商品可重复行。BCNF |
| AppUser | UserId→其余属性；Username→其余属性 | 两个完整候选码均检查。Role 不决定 EmployeeCode/MemberCode；不复制员工和会员名称。条件唯一与角色约束另行实现。在声明的全域依赖下 BCNF |

所有字段均为原子值，满足 1NF。OrderLine 的非主属性对联合码不存在部分依赖，满足 2NF；各表没有非码决定非主属性的已知传递依赖，满足 3NF，且全域非平凡依赖决定因素均为超码，达到 BCNF。这里只针对本项目明确的业务依赖，不把“有自增主键”当作规范化证明。

## 独立异常演示与分解证明

假设演示关系 R(ProductCode, ProductName, CategoryCode, CategoryName)，F={ProductCode→ProductName CategoryCode, CategoryCode→CategoryName}。P01 和 P02 都属 C01 奶茶。将 C01 改名需更新多个商品（修改异常）；暂无商品时不能独立登记 C02（插入异常）；删除 C01 最后一个商品会丢掉类别名称（删除异常）。这些是假设关系的反例，不声称 v0.1 有不存在的 CategoryCode 字段。

分解为 ProductDemo(ProductCode,ProductName,CategoryCode) 和 CategoryDemo(CategoryCode,CategoryName)。交集 {CategoryCode} 是 CategoryDemo 的码，满足二元无损分解条件 (R1∩R2)→R2，按 CategoryCode 自然连接可以无损还原；原两条依赖分别在子关系内表达，保持依赖。此证明基于 F，样例还原只是辅助验证。实际 Product 只存原子类别名称，无类别编号或其他类别属性，保留已有结构。

OrderLine.UnitPrice 与 Product.UnitPrice 的名称相同但含义不同，分别为当次成交价和当前菜单价。历史价是必要事实，并非由当前商品价产生的规范化冗余。订单总额不落库，不需要维护重复金额；StockApplied 是开库快照与新增流水的来源状态，只有确认和取消过程按事务维护。

## 分层与安全

浏览器 static/app.js → web/app.py 路由 → web/service.py 业务 → web/dao.py 参数化访问 → SQL Server 表/约束/视图/受限过程。查询示例：菜单 GET→Service.products→DAO.products→绑定两个搜索参数。修改示例：确认 POST→Service.order_action 校验角色及可见性→DAO 事务→usp_OrderAction 锁订单、按商品号锁库存并检查余额、扣减和更新状态→提交；任一步异常全部回滚。

运行连接使用 Windows 认证建立连接，立即用 ODBC 顶层 CALL 激活密码应用角色。激活后才执行任何业务 SQL；不申请恢复 cookie，关闭连接时丢弃，pyodbc pooling=False。四个有效数据库身份 mt_auth/mt_admin/mt_clerk/mt_customer 经过 sysadmin=0、db_owner=0 和真实拒绝操作测试。mt_auth 仅读账号哈希；mt_admin 维护商品库存；店员/顾客只能读菜单库存、执行订单过程，不能直接改库存商品、直接读订单全表或读取账号哈希。角色账号是应用后端内部凭据；顾客之间的账户身份仍由服务会话校验，不向用户提供数据库连接或应用角色密码。本机认证模式不需调整，不需服务重启。

应用管理员不拥有架构管理或账号管理权限。样例账号由配置阶段随机生成，密码经 scrypt 保存；.env 和 private/ 不提交。JSON API 有 CSRF、HttpOnly/SameSite Cookie、会话过期与每次请求账号有效性检查。输入必须进行服务端校验；DOM 使用 textContent，数据库用户输入均使用参数绑定，SQL 只在 DAO/数据库脚本内。
