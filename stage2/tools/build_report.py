"""Generate the submission report from checked SQL/HTTP evidence; no invented results.
Use the Codex bundled Python (python-docx/Pillow) for document authoring.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image
from docx import Document
from docx.enum.section import WD_ORIENT,WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm,Pt,RGBColor

ROOT=Path(__file__).resolve().parents[1]
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
QA=ROOT/'private'/'report-qa';QA.mkdir(parents=True,exist_ok=True)
doc=Document()


def font(style,size,bold=False):
    s=doc.styles[style];s.font.name='Calibri';s.font.size=Pt(size);s.font.bold=bold;s.font.color.rgb=RGBColor(0,0,0)
    s.element.rPr.rFonts.set(qn('w:eastAsia'),'宋体' if style=='Normal' else '黑体')
    s.paragraph_format.space_after=Pt(7)


font('Normal',11);font('Title',24,True);font('Subtitle',12);font('Heading 1',17,True);font('Heading 2',13,True);font('Heading 3',11.5,True)
doc.styles['Subtitle'].font.italic=False
for border in list(doc.styles.element.iter(qn('w:pBdr'))):
    border.getparent().remove(border)
doc.styles['Normal'].paragraph_format.line_spacing=1.3
for s in ['Heading 1','Heading 2','Heading 3']:
    doc.styles[s].paragraph_format.keep_with_next=True
    doc.styles[s].paragraph_format.space_before=Pt(9)
    doc.styles[s].paragraph_format.space_after=Pt(9)


def layout(section,landscape=False):
    section.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width=Cm(29.7 if landscape else 21)
    section.page_height=Cm(21 if landscape else 29.7)
    section.top_margin=Cm(1.6);section.bottom_margin=Cm(1.6)
    section.left_margin=Cm(1.8);section.right_margin=Cm(1.8)
    section.footer_distance=Cm(.65)


layout(doc.sections[0])
footer=doc.sections[0].footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=footer.add_run();r.font.size=Pt(9);fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)


def p(text='',style=None):
    return doc.add_paragraph(text,style)


def h(text,level=1):
    return doc.add_heading(text,level)


def page(title):
    doc.add_page_break();h(title)


def table(headers,rows,widths=None):
    t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
    for cell,txt in zip(t.rows[0].cells,headers):
        cell.text=txt
        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E9EEE6');cell._tc.get_or_add_tcPr().append(shade)
    header=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(header)
    for row in rows:
        cells=t.add_row().cells
        for cell,txt in zip(cells,row):cell.text=str(txt)
    for row in t.rows:
        trpr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
        for i,cell in enumerate(row.cells):
            if widths:cell.width=Cm(widths[i])
            for para in cell.paragraphs:
                para.paragraph_format.space_after=Pt(5);para.paragraph_format.space_before=Pt(4);para.paragraph_format.line_spacing=1.15
                for run in para.runs:run.font.size=Pt(9.5)
    p()
    return t


def picture(path,width,caption):
    para=p();para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.line_spacing=1
    para.paragraph_format.space_before=Pt(0)
    para.paragraph_format.space_after=Pt(5)
    para.add_run().add_picture(str(path),width=Cm(width))
    cap=p(caption);cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after=Pt(7)
    for r in cap.runs:r.font.size=Pt(9)


data=json.loads((ROOT/'result/before-after.json').read_text(encoding='utf-8'))
browser=json.loads((ROOT/'result/browser-acceptance.json').read_text(encoding='utf-8'))
suite=ET.parse(ROOT/'result/pytest.xml').getroot().find('testsuite')
integration_tests=int(suite.attrib['tests'])
assert integration_tests>=43 and suite.attrib['failures']=='0' and suite.attrib['errors']=='0'
assert len(browser['checks'])==18 and all(x['result']=='PASS' for x in browser['checks'])
assert all(x['equal'] for x in data['source_preservation'])
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()

# 1: a substantive opening, not an empty cover.
doc.add_heading('校园奶茶店数据库应用第二阶段实验报告',0)
p('第五周至第九周成果  v1 0', 'Subtitle')
p('小组成员  袁远冬  陆乐天  罗金浩')
p('课程  数据库系统实验    提交日期  2026年11月8日')
h('一 设计思路')
p('本阶段从第一阶段奶茶店数据库出发，完成ER模型、函数依赖与范式分析，在保留业务数据的副本上迁移，并构建连接SQL Server的分角色Web应用。六张原业务表保留，增加账号及订单来源状态；顾客维护自己的草稿，店员确认时以事务扣减库存，管理员维护商品与库存。')
p(f'本次验收中，迁移前后六表原数据、订单明细、商品销量与库存完全一致，完成销售仍为6单、15杯、86.00元；13项SQL回归、{integration_tests}例API与数据库及交叉场景集成测试、18项真实浏览器流程均通过。测试证据和源文件随提交包提供。')
table(['周次','任务与交付','主要位置'],[
['5','实体、标识、联系基数、参与约束与问题清单','docs/er-v01.svg、er-v10.svg、design.md'],
['6','FD与范式、异常与分解、数据迁移和对照','sql/migration.sql、regression.sql；result/before-after.json'],
['7至9','分层Web、登录CRUD、角色、事务及异常','web/、tests/；result/浏览器截图及测试记录'],
['阶段','操作手册、分工、AI记录、可复现提交','README.md、docs/user-manual.md、contribution.md、ai_log.md']],[1.5,8.0,7.7])
p('业务范围沿用校园单店、标准饮品和可售杯数，不扩展配方、糖冰加料、采购及支付退款。库存原本是开库盘点快照，迁移不得按历史销量再扣减。正文的设计结论来自实际表结构与业务规则，样例回归用于检查实现，不代替范式证明。')
p('仓库  https://github.com/Ageha-yyd/campus-shop-db-lab')
p('代码验收基线  '+sha[:12]+'    第二阶段目录  stage2')

# 2-3: source diagrams.
page('第五周 原有设计的ER模型')
p('v0.1包含商品、库存、会员、员工、订单、订单明细六个实体。商品与订单的多对多联系通过明细关联实体实现。明细以订单号和行号联合标识，同一饮品可以在一张订单重复出现。')
picture(ROOT/'docs/er-v01.png',17.2,'图1  v0.1 ER模型  可编辑源文件 docs/er-v01.svg')
p('图中端点标注表示另一端单条记录所对应的此端记录数。0表示可选参与，1表示必须参与；PK为主码、AK为候选码、FK为外码、问号表示可空。Inventory共享商品主码，业务允许商品暂未登记库存，因此商品到库存为0..1。')
p('订单至少一条明细是业务规则；仅有FK不能保证这一最低基数。历史单的员工必填，会员可空；样例中的散客订单和多商品订单都与该规则一致。')

page('第五周 目标设计的ER模型')
p('v1.0增加AppUser；订单新增创建账号与扣库来源标志，允许草稿暂无员工。店员确认后必须写入员工；历史订单创建账号保留NULL，不虚构来源。')
picture(ROOT/'docs/er-v10.png',17.2,'图2  v1.0 ER模型  可编辑源文件 docs/er-v10.svg')
p('AppUser.UserId为主码，Username是另一个候选码；员工号与会员号只在非空子集唯一，不是全关系候选码。admin和clerk必须绑定员工，customer可以绑定会员或为散客，不能把两个可选联系误画成账号必须同时关联员工与会员。')
p('SchemaVersion用于迁移版本记录；Baseline_*保存迁移前查询和数据快照，不作为业务实体。字段类型、空值、默认值和全部索引约束由实际SQL Server目录导出到data-dictionary.md。')

page('第五周 业务规则与原设计改进')
table(['联系','两端业务基数','映射与执行方式'],[
['商品与库存','商品0..1库存；库存恰好1商品','Inventory.ProductCode共享PK/FK；新建商品自动建零库存，允许删零库存'],
['商品与明细','商品0..N明细；明细恰好1商品','OrderLine.ProductCode FK；历史引用限制删除，可下架'],
['订单与明细','订单1..N明细；明细恰好1订单','复合PK、FK；最低一行由事务保存过程与确认过程检查'],
['员工与订单','员工0..N订单；草稿0..1员工，完成单1员工','可空FK；确认过程使用店员账号对应员工'],
['会员与订单','会员0..N订单；订单0..1会员','可空MemberCode；顾客会员归属在后端确定'],
['账号与订单','账号0..N订单；订单0..1创建账号','CreatedByUserId FK；历史为空，新增必填；顾客按创建人过滤'],
['账号与员工或会员','两端各0..1，依角色选择','可空FK和过滤唯一索引；CHECK限制员工/顾客配置']],[2.6,5.1,9.5])
h('问题清单及保留理由',2)
p('保留：六表避免重复存储会员名、员工名和商品信息；OrderLine的历史成交价不依赖当前菜单价；订单金额由明细聚合而不重复存储。Category只有原子类别名称，无类别编号或其他类别属性，不为展示拆表而破坏现有关系。')
p('改进：原库没有登录账号，库存不自动扣减，订单没有草稿状态；外码也不能保证头与明细同时写入。增加AppUser和DRAFT状态，以受限过程保存非空草稿，确认时统一扣库存。StockApplied区分新系统实际扣库与历史开库订单，避免错误回补。')
p('验证映射：会员customer绑定M001；guest的MemberCode为空；浏览器创建D001与D003的多商品草稿，店员确认后D001库存20→17、D003库存5→4。该流程将图中的可选会员、订单关联明细与商品库存实际连通。')

page('第六周 逐表函数依赖与范式判断')
p('以下依赖来自本项目业务规则。“其余字段”指同一关系内字段。全部字段为原子值，满足1NF；判断2NF时考虑所有候选码，判断3NF时检查非码决定因素。')
table(['表与候选码','关键函数依赖','范式及理由'],[
['Product\nProductCode','ProductCode → 名称 类别 当前价 阈值 启用状态','BCNF；无已知非码决定因素；名称和类别不唯一'],
['Inventory\nProductCode','ProductCode → Quantity UpdatedAt','BCNF；可售杯数与维护时间依赖商品主码'],
['Member\nMemberCode','MemberCode → 名称 电话 加入日期','BCNF；可空电话不是全关系候选码，仅非空子集唯一'],
['Employee\nEmployeeCode','EmployeeCode → 名称 职称 启用状态','BCNF；同职称或姓名不能决定员工号'],
['ShopOrder\nOrderNo','OrderNo → 时间 员工 会员 状态 创建账号 扣库来源','BCNF；Status不能单独决定StockApplied，历史与新增完成单不同'],
['OrderLine\n(OrderNo,LineNumber)','(OrderNo,LineNumber) → ProductCode Quantity UnitPrice','BCNF；非主属性依赖完整复合码；订单号或商品号单独不决定成交价'],
['AppUser\nUserId 与 Username','UserId → 其余字段；Username → 其余字段','在声明全域FD下BCNF；两个候选码均为决定因素，Role不决定员工或会员编号']],[4.1,6.5,6.6])
p('对单属性候选码，非主属性不存在对码的部分依赖；OrderLine中订单号并不决定商品、杯数和价格，行号在不同订单中也不能单独决定明细，因而满足2NF。没有将商品名、会员名、员工名从其他实体复制到订单中，避免非码的传递依赖。')
p('条件唯一、可空、角色互斥与最小参与约束仍需单独实现；不能仅凭加入UserId自增主键，就宣称用户名等其他候选码的依赖已经消失。')

page('第六周 更新异常与分解依据')
h('实际关系的插入修改删除分析',2)
table(['对象','如何避免异常'],[
['商品与库存','商品可独立存在；盘点只更新一条库存；删除零库存不删除商品。被历史明细引用的商品不能误删'],
['会员与员工','各自可以独立登记；名称只维护一处；历史订单通过外码引用，限制破坏性删除'],
['订单与明细','订单属性只存订单头；明细保存商品与成交价。头和非空明细在同一事务保存，完成单保留历史'],
['账号','唯一登录名和独立密码哈希；员工与会员名称不复制到账号。禁用账号后已有会话也被拒绝']],[3,14.2])
h('独立异常关系及无损证明',2)
p('演示关系R(ProductCode,ProductName,CategoryCode,CategoryName)，F={ProductCode→ProductName,CategoryCode；CategoryCode→CategoryName}。P01与P02同属C01奶茶，只把P01类别名改为鲜奶茶就产生同编号不同名称的修改异常；无商品时无法登记新类别是插入异常；删除某类最后商品会丢失类别信息是删除异常。')
p('分解为P(ProductCode,ProductName,CategoryCode)与C(CategoryCode,CategoryName)。交集{CategoryCode}是C的码，(P∩C)→C成立，因此二元分解无损；原两条关键依赖分别保留在P和C中，保持依赖。normalization_demo.sql真实复现修改异常、连接还原与独立类别登记；有限样例通过只作辅助检查。')
p('实际v0.1没有CategoryCode，也没有类别的其他属性，不能凭假设关系指认原表存在该传递依赖，因此六张核心关系不做拆分。OrderLine.UnitPrice是当次成交事实，Product.UnitPrice是当前价格，两者含义不同；历史价保留不属于不当冗余。订单总额由明细聚合；StockApplied由确认和取消事务维护。')

# 7-9 process.
page('二 实验过程')
h('副本迁移与失败恢复',2)
p('首先核对GitHub主分支与本地基线7b77969一致。默认初始化对原MilkTeaShopV01做COPY_ONLY、CHECKSUM备份，用独立文件名还原到新的目标库。目标已存在或.env已存在时直接拒绝覆盖。原库不删、不重建、不重命名；失败调试副本也保留。')
table(['顺序','执行内容与实际结论'],[
['1 保存基线','检查商品6行、订单7行、重复明细及空订单；保存六表及订单详情/销量/库存快照'],
['2 迁移结构','同一事务增加AppUser、SchemaVersion与唯一索引；订单增加创建账号与StockApplied，扩展DRAFT并调整员工可空及默认状态'],
['3 配置应用','更新详情视图为可显示无员工草稿；创建受限订单过程与权限；配置四个密码应用角色及四个哈希登录账号'],
['4 回归对照','原有六表仍为6/6/4/3/7/11行；双向EXCEPT比较详情、销量、库存；校验金额、键、约束及权限'],
['5 空环境验证','--from-scripts从仓库自带v0.1结构与样例建立独立基线，随后执行同一迁移，不以删库重建代替已有数据迁移']],[3,14.2])
p('migration.sql使用XACT_ABORT及单事务。结构或数据冲突抛错后回滚；不自动合并重复编号，也不凭空补造订单明细。SchemaVersion存在即拒绝再次迁移。配置后半段出错时保留失败副本，修复后换新目标名。')
p('迁移后需退回时，停止应用并指回保留的v0.1库或还原备份；先单独保存v1.0新增订单，不宣称降级能够无损接纳新结构的数据。新增AppUser四行、版本记录一行和Baseline_*快照是辅助数据增加，不是业务数据重复或丢失。')
p('证据位置：result/setup.json、before-after.json、regression.txt。原库、迁移快照及目标六表原字段的SHA256与逐行比较均一致。')

page('迁移前后关键结果与SQL回归')
table(['项目','迁移前预期','迁移后实际','结论'],[
['六业务表行数','6 / 6 / 4 / 3 / 7 / 11','6 / 6 / 4 / 3 / 7 / 11','一致'],
['订单详情','11条明细及全部字段','双向EXCEPT均无差集','一致'],
['完成订单','6张','6张','一致'],
['完成销量与金额','15杯 / 86.00元','15杯 / 86.00元','一致'],
['D001至D006销量','4 / 3 / 5 / 3 / 0 / 0','4 / 3 / 5 / 3 / 0 / 0','一致'],
['D001至D006库存','20 / 12 / 5 / 0 / 18 / 9','20 / 12 / 5 / 0 / 18 / 9','一致'],
['历史扣库标记','全部0；不重复扣盘点库存','全部0','一致']],[4.2,5.2,5.5,2.3])
table(['回归项','实际结果'],[
['01至06 语义与标识','明细、销量、库存双向相等；金额/数量正确；商品会员员工原属性保留；历史单无重复扣库'],
['07至10 完整性与价格','不存在订单的外码、负库存被547拒绝；合法商品与库存写入成功后回滚；修改当前价格不改历史成交价'],
['11至13 权限','店员可读菜单；改价与读取账号哈希均以229拒绝；临时测试用户与写入全部回滚']],[4.8,12.4])
p('result/before-after.json逐项保存expected和actual，不只保留成功截图。取消订单不计销售，零销量D005/D006仍返回0。商品当前菜单价与历史成交价分开验证，避免误把两种价格强制同步。')
p('独立规范化演示也已实际运行，记录在normalization-demo.txt。它只使用临时表，不更改业务结构。')

page('分层实现与事务安全')
table(['层级','文件与职责'],[
['页面层','templates/index.html、static/app.js与app.py路由：表单交互、fetch API、接收输入与展示统一结果'],
['业务层','service.py：输入范围、角色、所有权与状态规则；组织草稿保存、确认与取消流程'],
['数据访问层','dao.py：唯一运行时SQL入口；?参数绑定；连接打开、事务提交/回滚、finally关闭'],
['数据库层','SQL Server表、CHECK/UNIQUE/FK、视图与订单过程；锁定订单并维护库存一致性']],[3,14.2])
p('查询路径：菜单搜索GET→Service.products→DAO.products→绑定搜索参数查询Product→统一JSON→DOM的textContent展示。修改路径：确认POST→业务角色/可见性检查→DAO事务→usp_OrderAction锁定订单、按商品号汇总和锁库存、校验可售杯数、扣库并完成→提交。任何中途错误都rollback，连接最终释放。')
p('同商品多行先汇总，再一次性扣减。重复确认被状态限制拒绝；v1.0完成单取消仅回补一次。真实并发用例中，两单各需D001十五杯、库存二十杯，结果一单200、一单409，剩五杯。第二商品缺货时，第一商品已经执行的扣减也回滚。')
h('权限与统一异常',2)
p('数据库连接以Windows身份建立后，立即通过顶层ODBC CALL激活密码应用角色，再执行任何业务SQL；禁用连接池，不申请角色恢复cookie，关闭后销毁。四个有效身份均实测sysadmin=0、db_owner=0；店员/顾客不能直接改价、改库存、读账号哈希或订单全表。顾客个人所有权还由服务会话检查。')
table(['角色','可执行范围','关键限制'],[
['顾客含会员和散客','菜单库存查询；维护自己的非空草稿与明细，查看确认结果','不能确认扣库、改商品/库存、查销量或其他顾客订单'],
['店员','管理全部草稿、确认扣库、取消新完成单并回补、查库存销量','不能改菜单或直接盘点库存；历史开库单不可按新流水回补'],
['管理员','商品和库存维护；同时具备店员订单操作','被引用商品不可硬删；无架构、账号管理及数据库所有者权限']],[2.8,7.2,7.2])
p('统一响应ok/code/message/data/request_id；区分参数、认证、权限、资源、业务、连接、约束和事务错误。界面不暴露SQL、连接、路径或堆栈；后端JSONL记录时间、请求编号、操作、角色、错误码与结果。CSRF、HttpOnly/SameSite会话、scrypt哈希和账号有效性检查同步启用。')

# 10-16: landscape evidence, crops only; keep original full screenshots unchanged.
screens=[
('顾客完整流程与订单明细','04_customer_draft.png',(130,690,1310,1148),
 'customer以会员M001身份保存D001两杯和D003一杯，草稿总额16.00元；随后通过界面将D001改为三杯，总额22.00元。guest账号看不到该订单；顾客不能执行确认。'),
('店员确认与完成订单','05_clerk_confirmed.png',(130,690,1310,1370),
 '店员在订单中心核对并确认同一草稿，状态变为已完成，订单明细为D001三杯及D003一杯，总额22.00元；数据库同时填写员工并扣减库存。'),
('店员库存查询与角色差异','06_clerk_stock.png',(130,115,1310,860),
 '确认后D001为17杯、D003为4杯；店员可查询库存但无盘点与删除入口。之后取消该v1.0完成订单，库存恢复原值；再次取消被拒绝。'),
('管理员商品维护','07_admin_products.png',(130,800,1310,1400),
 'admin通过表单新增UI_TEST验收测试茶，再把价格3.50改为4.00。新建商品同时创建零库存；图中展示测试饮品及商品维护表单。'),
('管理员库存维护','09_admin_inventory.png',(130,400,1310,1205),
 '管理员将UI_TEST盘点为8杯，再调整为0杯，删除库存记录并重新登记，最后删除无订单引用的测试商品。已有订单引用的商品删除会被外码拒绝，事务回滚。'),
('约束冲突的统一反馈','08_constraint_error.png',(130,1020,1310,1510),
 '通过相同商品编号再次新增，SQL唯一约束产生真实冲突；API返回409及CONSTRAINT_CONFLICT，界面只显示友好提示与请求编号。登录错误及输入错误也有独立测试。'),
('真实连接失败与日志定位','11_connection_error.png',(130,400,1310,1205),
 '验收时把测试服务连接暂时指向本机未监听端口，实际连接尝试失败；API返回503及DB_UNAVAILABLE，界面无SQL、服务器地址、路径或堆栈。测试后立即恢复配置。')]
section=doc.add_section(WD_SECTION_START.NEW_PAGE);layout(section,True)
for index,(title,name,box,description) in enumerate(screens):
    if index:doc.add_page_break()
    h(title)
    p(description)
    original=ROOT/'result/screenshots'/name
    im=Image.open(original);box=(box[0],box[1],box[2],min(box[3],im.height))
    crop=QA/('report-'+name);im.crop(box).save(crop)
    height=box[3]-box[1];width=box[2]-box[0]
    display=min(25.4,12.8*width/height)
    picture(crop,display,'图'+str(index+3)+'  实际浏览器截图节选  原图 result/screenshots/'+name)

# 17-18 portrait summary and usable manual.
section=doc.add_section(WD_SECTION_START.NEW_PAGE);layout(section)
h('应用测试与可复现验收')
table(['测试类别','输入与预期','实际结果'],[
['认证与会话','四账号登录退出；错误密码、注入登录、停用账号、未登录、CSRF','正确200；错误401或403；已停用会话也拒绝'],
['CRUD与权限','商品库存增改删；客户草稿及明细增改删；跨客户访问、店员越权','合法完成；越权403；不可见订单404'],
['完整性与安全','编号重复、被引用删除、不存在会员、负数/小数/布尔杯数、搜索注入','统一400/409；原数据保留；用户输入未拼接SQL'],
['事务','缺货回滚、重复确认、历史价、取消回补、两单争抢库存','第一商品扣减回滚；重复操作拒绝；一200一409剩5杯'],
['数据库限制','四有效身份非sysadmin/db_owner；直接DDL和敏感SQL','四身份均为0；DDL/越权语句真实拒绝'],
['故障反馈','真实连接失败；注入40001测试统一事务错误分类','分别503与DB_UNAVAILABLE/TRANSACTION_FAILED；无内部信息泄露'],
['真实Web','会员顾客、散客、店员、管理员表单操作及移动登录','18项检查；59次HTTP响应；12张截图；无JS未捕获异常']],[3.0,7.5,6.7])
p(f'API与真实SQL Server及交叉场景集成共{integration_tests}例，全部通过；SQL回归13项全部通过；浏览器检查18项全部通过。pytest.xml/txt、browser-acceptance.json、regression.txt分别保存独立证据。浏览器写入只发生在独立_Test库，测试后清理恢复基线；演示库和v0.1原库不受测试清理影响。')
p(f'提交包已解压到独立中文路径，重新创建虚拟环境并按README从自带脚本建立新库，再次通过SQL回归13项、集成{integration_tests}例和浏览器18项。复制后的BAT启动入口也分别完成四个账号登录及菜单查询；运行代码和SQL与最终源文件逐一核对，记录见package-replay.json。')
p('第二次独立复核新增五个反例，修订前全部失败，修订后全部通过：搜索后编辑其他饮品、库存行删除后的取消回补、大金额订单查询、非ASCII无效CSRF及连接故障角色日志。ER图也补齐联系名称并纠正原版本非空明细脚注，详见course-review.md与course-audit.json。')
p('证据边界：40001异常分类明确使用故障注入；缺货回滚、非法FK、唯一冲突、数据库权限、并发和连接失败均真实执行。自动化结果不等于三位同学已经人工签字验收。')
p('日志示例保存在log-evidence.jsonl，覆盖十类错误且保留request_id、time、operation、role、code、result；详细诊断只保留本机，不将连接密码或会话密钥写入报告或公共仓库。')

page('三 实验总结')
h('复现与操作摘要',2)
p('空环境先安装SQL Server、ODBC Driver18与Python，在包含sql和stage2的仓库根目录创建.venv并安装stage2/requirements-dev.txt。运行python -m stage2.tools.setup --from-scripts --database MilkTeaShopV10_Demo，再运行python -m stage2。已有v0.1原库时省略--from-scripts，由脚本备份还原后迁移。')
p('访问127.0.0.1:5000；随机账号密码位于本机stage2/private/<数据库名>_accounts.json。顾客：菜单→多行草稿→修改或删除→查看店员确认结果；店员：核对→确认→库存和销量→需要时取消；管理员：商品维护→盘点库存→零库存及无引用记录删除。完整步骤与错误排查见user-manual.md。')
h('总结与限制',2)
p('本阶段用ER解释实体和最小/最大参与，结合所有候选码分析FD和范式，保留合理关系，并以独立关系展示更新异常及无损分解。迁移通过副本、快照与双向查询证明原有语义保持；应用把权限、参数绑定、事务回滚和连接释放落实到实际流程。')
p('当前版本是校园单店的课堂应用；未实现支付退款、原料库存、配方和公网部署。数据库应用角色用于后端内部授权，顾客间身份由可信后端会话校验；数据库角色密码不分发给顾客。商品名称变化不作为历史名称快照要求，历史订单保证的是成交单价与数量。')
table(['成员','责任与演示安排'],[
['袁远冬','ER、迁移、仓库与复现整合，讲解实体关系和初始化'],
['陆乐天','FD与范式、字典、DAO及CRUD回归，讲解约束与分解'],
['罗金浩','Web角色流程、权限异常、结果与报告组织，讲解事务和错误反馈']],[2.8,14.4])
p('本次代码、文档、测试与浏览器操作由AI工具辅助完成，上表是责任与演示安排，不虚构个人开发时长或尚未发生的人工验证。提交前按分工复核、补充本人操作记录。AI建议、实际修正和验证结论详见ai_log.md。')
p('技术参考：Flask官方文档的Web安全与会话配置；Microsoft Learn的SQL Server Table Hints、应用程序角色与sp_setapprole文档。课程要求以本地第五周、第六周、第7至9周任务讲解为准。')

doc.core_properties.title='校园奶茶店数据库应用第二阶段实验报告'
doc.core_properties.author='袁远冬 陆乐天 罗金浩'
doc.core_properties.subject='第五至第九周 ER 规范化 迁移 Web应用及验收'
for border in list(doc.element.iter(qn('w:pBdr'))):
    border.getparent().remove(border)
target=ROOT/'阶段报告_课程复核版.docx';doc.save(target)
(ROOT/'result/report-source.json').write_text(json.dumps({'code_commit':sha,'sql_regression_pass':13,'integration_tests':integration_tests,'browser_checks':18,
 'screenshots':[x[1] for x in screens],'source_preservation':all(x['equal'] for x in data['source_preservation']),
 'report_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
print('Created '+str(target))
