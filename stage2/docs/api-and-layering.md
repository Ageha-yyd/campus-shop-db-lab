# 接口与分层说明

页面使用Flask模板及浏览器fetch，输入通过JSON提交。响应统一为ok、code、message、data、request_id。下表的角色检查发生在服务端，所有运行时SQL只位于DAO；页面与业务层不拼接用户SQL。

| 功能与接口 | 输入 | 处理 | 输出 |
| --- | --- | --- | --- |
| 登录 POST /api/login | username、password及CSRF请求头 | Service验证长度；DAO绑定用户名查账号；scrypt校验；更新会话与CSRF | 用户名、角色及新的CSRF；错误统一401 |
| 菜单 GET /api/products | 可选q搜索文字 | Service验证长度；DAO将两个LIKE值绑定；前端筛选展示不覆盖订单编辑的完整商品目录 | 商品编号、名称、类别、菜单价、阈值、启用状态 |
| 商品 POST/PUT/DELETE /api/products | 编号、名称、类别、价格、阈值、状态 | 仅admin；类型与范围检查；新商品同事务建零库存；有订单引用时FK拒绝硬删除 | 成功编号或统一400/403/404/409 |
| 库存 GET、PUT、DELETE /api/inventory | 商品编号、盘点杯数 | 所有角色可查询；仅admin维护；零库存才可删；缺行时可重新登记 | 商品及当前杯数、预警阈值；操作成功或友好错误 |
| 订单 POST /api/orders、PUT /api/orders/编号 | items数组及可选会员号 | 校验1至50行和每行1至100杯；顾客会员归属后端确定；保存头与明细；草稿不扣库 | 新编号；GET返回金额及明细 |
| 订单 GET /api/orders、GET /api/orders/编号 | 会话与可选编号 | 顾客仅可见自己的订单；员工可查全部；总额decimal(18,2)支持输入合法上限 | 状态、员工、会员、金额、行号、饮品及成交单价 |
| 确认 POST /api/orders/编号/submit | 草稿编号 | 仅店员/管理员；锁定状态与库存、按饮品汇总扣减、填写员工、更新完成状态；统一提交或回滚 | 成功或409；不会部分扣库或重复扣库 |
| 取消 POST /api/orders/编号/cancel | 订单编号 | 顾客可取消自己的草稿；员工可取消新系统完成单；有扣库时原子回补，缺失零库存行则重建；重复取消拒绝 | 成功或403/409；原扣库只恢复一次 |
| 草稿 DELETE /api/orders/编号 | 草稿编号 | 所有权与状态检查；同事务删除明细与头；完成单保留历史 | 成功或404/409 |
| 销售 GET /api/sales | 会话 | 仅店员/管理员；只统计COMPLETED；零销量仍保留 | 每种饮品杯数和销售额 |

查询路径：static/app.js → app.py products路由 → Service.products → DAO.products → SQL Server Product → 统一JSON → textContent展示。搜索结果与编辑目录独立维护，避免搜索D001后无法编辑含D003的草稿。

修改路径：页面确认 → app.py路由 → Service.order_action复核角色、所有权和动作 → DAO.order_action事务上下文 → usp_OrderAction在数据库锁保护下最终核对状态/库存并修改 → DAO提交/回滚、finally关闭 → 统一响应。服务负责可执行的业务流程；数据库过程中的最终状态和库存检查保证并发时校验与修改不可分割。

DAO先用Windows认证建连接，随即激活独立密码应用角色，再执行业务SQL；不申请恢复cookie、禁用连接池。运行时有效权限经实际SQL验证不是sysadmin或db_owner。SQL过程通过ownership chain完成受限写入，店员/顾客不拥有原表写权限。应用角色密码只保存在后端配置；顾客身份和订单所有权始终由可信后端会话确定。

异常仅在app.py集中归类。具体原因留在本机logs/app.jsonl，按request_id定位；重新验证账号时若连接失败，保留最后经认证的角色作为诊断字段，该字段不参与授权。输入中的非ASCII无效CSRF同样返回403，不触发500。
