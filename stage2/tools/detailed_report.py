"""Append an execution-bound, illustrated record to the reviewed design report."""
import hashlib
import json
from xml.etree import ElementTree as ET

from PIL import Image, ImageChops
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def finish(c):
    root,doc=c['ROOT'],c['doc']
    base_p,base_h,table,base_picture,layout=[c[x] for x in ['p','h','table','picture','layout']]
    qa=root/'private/detailed-report-qa';qa.mkdir(parents=True,exist_ok=True)
    browser=json.loads((root/'result/detailed-browser.json').read_text(encoding='utf-8'))
    runs=json.loads((root/'result/detailed-runs/manifest.json').read_text(encoding='utf-8'))
    figs={x['step']:x for x in browser['figures']}
    cases=ET.parse(root/'result/detailed-runs/pytest.xml').getroot().find('testsuite')
    assert int(cases.attrib['tests'])==43 and cases.attrib['failures']==cases.attrib['errors']=='0'
    assert len(figs)==21 and len(browser['checks'])==18 and not browser['javascript_errors']
    for run in runs:
        assert run['exit_code']==0
        assert hashlib.sha256((root/run['stdout_file']).read_bytes()).hexdigest()==run['stdout_sha256']
    figure_index=[]
    code_sources=[]
    number=2
    landscape=False

    def p(text='',style=None):
        para=base_p(text,style)
        if landscape:
            para.paragraph_format.line_spacing=1.12
            para.paragraph_format.space_after=Pt(4)
            for run in para.runs:run.font.size=Pt(10.5)
        return para

    def h(text,level=1):
        para=base_h(text,level)
        if landscape:
            para.paragraph_format.space_before=Pt(0)
            para.paragraph_format.space_after=Pt(7)
            for run in para.runs:run.font.size=Pt(16)
        return para

    def picture(path,width,caption):
        base_picture(path,width,caption)
        for para in doc.paragraphs[-2:]:
            para.paragraph_format.line_spacing=1
            para.paragraph_format.space_after=Pt(3)
        doc.paragraphs[-2].paragraph_format.keep_with_next=True

    # Identify the latest edition without changing the retained review edition.
    doc.paragraphs[1].text='第五周至第九周成果  详细图文版  v1 0'
    for para in doc.paragraphs:
        if '18项真实浏览器流程均通过' in para.text:
            para.text+=' 本版进一步补充21个真实界面状态及SQL和测试输出截图，逐项说明执行动作、输入、观察位置与结论。'
    # Match table styling to the formal classroom report.
    def polish_tables():
        for t in doc.tables:
            pr=t._tbl.tblPr
            borders=pr.find(qn('w:tblBorders'))
            if borders is None:borders=OxmlElement('w:tblBorders');pr.append(borders)
            for edge in ['top','left','bottom','right','insideH','insideV']:
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            for cell in t.rows[0].cells:
                cell._tc.get_or_add_tcPr().find(qn('w:shd')).set(qn('w:fill'),'E5EDF4')

    def new(title,wide=False):
        nonlocal landscape
        if landscape!=wide:
            section=doc.add_section(WD_SECTION_START.NEW_PAGE);layout(section,wide)
            landscape=wide;h(title)
        else:
            heading=h(title);heading.paragraph_format.page_break_before=True

    def code(path,first,last):
        source=root/path;lines=source.read_text(encoding='utf-8-sig').splitlines()
        excerpt='\n'.join(lines[first-1:last])
        para=p(excerpt);para.paragraph_format.line_spacing=1.05;para.paragraph_format.space_after=Pt(8)
        for run in para.runs:run.font.name='Consolas';run.font.size=Pt(9)
        p(f'代码来源  {path}  第{first}至{last}行；正文仅节选，完整文件随包提供。')
        code_sources.append({'file':str(path),'line_start':first,'line_end':last,'file_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})

    def fig(source,step,title,description='',width=24.8,maxheight=None,box=None,trim=False):
        nonlocal number
        source=root/source
        original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        im=Image.open(source).convert('RGB')
        if box:im=im.crop(box)
        if trim:
            bounds=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
            if bounds:im=im.crop((0,0,im.width,min(im.height,bounds[3]+22)))
        target=qa/(str(number+1)+'-'+source.name);im.save(target)
        if maxheight:width=min(width,maxheight*im.width/im.height)
        number+=1
        picture(target,width,f'图{number}  {step}  {title}')
        if description:p(description)
        para=p('原始证据  '+source.relative_to(root).as_posix())
        for r in para.runs:r.font.size=Pt(8)
        para.paragraph_format.space_after=Pt(4)
        figure_index.append({'figure':number,'step':step,'title':title,'source':source.relative_to(root).as_posix(),
            'source_sha256':original_sha,'embedded_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'crop':list(box) if box else 'white margins only' if trim else None})

    def ui(step,width=24.8,maxheight=None,extra='',box=None):
        f=figs[step]
        assert hashlib.sha256((root/f['image']).read_bytes()).hexdigest()==f['sha256']
        p(f'步骤{step}  {f["action"]}。观察结果：{f["observed"]}。'+extra)
        fig(f['image'],step,f['title'],width=width,maxheight=maxheight,box=box)

    def output(step,index,intro,observation):
        run=next(x for x in runs if x['step']==step);image=run['figures'][index-1]
        p(intro)
        p(observation)
        fig(image['image'],step,run['title']+f' 输出第{image["line_start"]}至{image["line_end"]}行',
            width=24.8,maxheight=12.1,trim=True)

    new('小组实施顺序与实验环境')
    p('本报告按需求分析、模型论证、迁移实现、应用实现、运行验证和复核整改组织，展示项目实际形成的过程。代码、SQL和自动化运行由AI工具辅助完成；组员责任及后续演示安排列于末尾，不把自动化记录写成未经确认的个人操作或人工签字。')
    h('从任务到实现的过程',2)
    p('第一步，对照第五周、第六周和第7至9周任务讲解，把交付拆成模型、规范化、迁移和Web四部分。先确认校园单店及可售杯数的业务范围，读取v0.1六表及历史样例，列出保留项和缺口，避免在不存在的类别编号上杜撰传递依赖。')
    p('第二步，从订单和明细的业务事实确定键与联系：一次购买可以有多种饮品，会员可选，明细必须属于订单；再按草稿、确认、取消的状态补充账号和库存来源。每个基数都明确由主外码、可空、唯一约束或事务过程中的哪一层执行。')
    p('第三步，逐表分析函数依赖和全部候选码。六张原表已有合理分解，保留结构和历史成交价；另用临时关系演示异常、无损分解和保持依赖，而非为增加表数改坏原设计。')
    p('第四步，先建立独立副本，再迁移、保存Baseline快照、安装受限过程和应用角色。用双向EXCEPT、行数和原字段摘要对照原数据，确认6笔完成单、15杯、86.00元及库存均未改变，再接入页面。')
    p('第五步，按页面、路由、业务、DAO和SQL分层实现登录及CRUD。先验证一条查询和一次草稿写入，再串联顾客下单、店员确认、库存和销量；最后覆盖越权、缺货回滚、并发、取消和连接故障。复核暴露的五项缺陷修复后重新执行全部验收。')
    table(['项目','本次实测配置'],[
        ['运行环境','Windows；Python 3.14；SQL Server 2025 Express 17.0.1000.7；ODBC Driver 18'],
        ['应用与浏览器','Flask 3.1.2；pyodbc 5.3.0；pytest 8.4.2；Playwright驱动真实Microsoft Edge'],
        ['原库与演示库','MilkTeaShopV01保留；演示副本MilkTeaShopV10_Final'],
        ['截图与集成验收库',browser['database']+'；只清理明确以_Test结尾的隔离测试库'],
        ['运行方式','python -m stage2；复制后的启动第二阶段.bat亦已验证；默认仅监听本机']],[3.4,13.8])

    new('关键字段与数据库约束的实现')
    p('模型转换为关系后，字段类型和空值约束必须能表达业务范围。下表列出应用链条中的关键字段；完整七表、默认值、索引、CHECK和实际样例见docs/data-dictionary.md，该字典从SQL Server目录导出。')
    table(['关系及字段','类型或标识','设计作用与约束'],[
        ['Product.ProductCode','varchar(12) PK','稳定商品编号；名称不唯一，不作为码'],
        ['Product.UnitPrice','decimal(10,2)','当前菜单价；服务限制0.01至99999999.99，最多两位小数'],
        ['Inventory.ProductCode','PK兼FK','每商品最多一条库存；可无登记；不重复商品名称'],
        ['Inventory.Quantity','int','非负可售杯数；应用盘点上限1000000，零杯才可删除记录'],
        ['ShopOrder.OrderNo','varchar(24) PK','新增为WEB加随机标识；历史编号保持原样'],
        ['ShopOrder.Status','varchar(12)','DRAFT、COMPLETED、CANCELLED；动作过程控制转换'],
        ['EmployeeCode 与 MemberCode','可空FK','草稿暂无员工；会员可空；确认时填写店员对应员工'],
        ['CreatedByUserId','可空FK至AppUser','历史来源为空；新增保存实际登录账号，用于顾客订单隔离'],
        ['StockApplied','bit','新系统实际扣库后为1，取消回补后为0；历史开库订单为0'],
        ['OrderLine 联合标识','PK(OrderNo,LineNumber)','Quantity与UnitPrice依赖完整联合码；同商品允许多行'],
        ['OrderLine.UnitPrice','decimal(10,2)','保存草稿时的成交报价；确认不按新菜单价格重算'],
        ['AppUser 两个候选码','UserId PK；Username UNIQUE','Role用于权限，PasswordHash为scrypt哈希；不向页面导出哈希']],[5.0,4.3,7.9])
    p('数据库完整性分为域、实体、参照和业务过程四部分。CHECK拒绝负库存，PK/UNIQUE拒绝重复标识，FK限制不存在的引用；至少一条明细、库存是否足够、重复确认和取消仅回补一次，需由同一事务内的过程执行。只画ER或只在HTML设置输入范围均不足以保证这些规则。')
    p('金额字段区分单价与聚合总额：单价上限来自decimal(10,2)，订单汇总使用decimal(18,2)。复核已验证两行各100杯且单价99999999.99时，19999999998.00元仍可正常读取。此为合法边界测试，并非常规菜单价格。')

    new('登录与查询在各层如何衔接')
    h('登录的输入 处理和输出',2)
    p('浏览器先GET /api/session取得CSRF；登录表单把username和password以JSON发送到POST /api/login。路由解析对象，Service检查长度并调用DAO，DAO以用户名参数绑定查询启用账号；Service用scrypt验证哈希。成功后清空旧会话，保存用户名和角色并更新CSRF，页面只收到用户名与角色。错误密码统一401，不暴露账号是否存在。')
    code('web/dao.py',46,53)
    p('上面用户名SQL的问号和后续username参数相对应；搜索语句有两个问号，分别绑定包含通配符的搜索值。SQL文本的结构固定，输入不会被拼接成条件或多条语句。运行代码中的全部ODBC和业务SQL只位于dao.py，service.py不直接访问数据库。')
    h('菜单查询示例',2)
    p('输入D001时，app.js发起GET /api/products?q=D001；路由传递q；Service检查登录及搜索长度不超过80；DAO在商品名称和编号上绑定两个LIKE参数；数据库返回有序商品记录；统一JSON交给前端。前端用textContent放置名称、金额等值，避免把商品名称当作HTML执行。')
    p('搜索列表和订单编辑使用的完整商品目录分别维护。否则先搜D001后编辑含D003的草稿，会把未匹配商品从下拉框移走。该缺陷曾被实际复现，修复后已加入交叉场景回归。')
    table(['位置','输入','输出或副作用'],[
        ['index.html 与 app.js','表单、按钮、搜索文字','fetch JSON；绘制菜单和通知；不执行SQL'],
        ['app.py','请求路径、JSON、会话、CSRF','解析与统一响应；生成request_id；每次重查账号有效性'],
        ['service.py','可信当前用户和清洗后的数据','校验角色、输入、所有权；调用DAO'],
        ['dao.py 与 SQL Server','绑定参数及固定角色','打开连接、激活应用角色、查询或事务、关闭连接']],[4.0,6.2,7.0])

    new('订单事务和库存一致性的实现')
    p('顾客草稿保存把非空items数组提交到服务层。后端要求1至50行、每行1至100杯，并拒绝布尔值或小数充当整数。保存过程校验商品存在且启用，确定实际账号和会员关联，在同一事务中写订单头与全部明细；修改时整体替换草稿明细并按当前菜单重新报价。草稿保存本身不扣库存。')
    code('web/dao.py',29,40)
    p('DAO的事务上下文在yield之后统一commit，异常时rollback，finally始终close。连接建立后先激活固定白名单内的应用角色，之后才执行SQL；禁用连接池，避免已激活角色的连接进入别的请求。SQL过程检查与更新在同一个DAO事务中完成。')
    h('确认订单的数据库步骤',2)
    p('1 店员点击确认；服务层先校验可见性和admin/clerk角色。2 usp_OrderAction对订单使用UPDLOCK和HOLDLOCK，拒绝非DRAFT状态。3 将相同商品的多行数量汇总，按商品编号稳定顺序锁定商品与库存。4 每种商品先检查库存足够再扣减；任何一项缺货抛错，已执行的前项扣减也回滚。5 全部成功后写COMPLETED、StockApplied=1及当前店员，统一提交。')
    table(['动作','允许的起始状态','实际更新与限制'],[
        ['保存或编辑','新草稿或自己的DRAFT','原子保存头和明细；顾客不能伪造其他会员'],
        ['确认','DRAFT；仅员工角色','库存扣减一次；状态完成；设置员工和扣库标记'],
        ['取消草稿','DRAFT','状态取消；未扣库不回补'],
        ['取消新增完成单','COMPLETED且StockApplied=1；员工','回补原数量，缺失库存行重建；标记归零；再次取消拒绝'],
        ['删除','DRAFT','同事务删明细和头；完成单不能直接删除'],
        ['取消历史完成单','历史StockApplied=0','拒绝；历史销售已经包含在开库盘点中，不能凭历史单回补']],[3.3,6.0,7.9])

    new('服务端权限 异常处理和日志追踪')
    p('角色判断同时落在可信后端和有效数据库身份。隐藏维护按钮只改善操作界面；直接调用API仍须经过Service.allow。DAO用Windows认证建连接后立即激活mt_auth、mt_admin、mt_clerk或mt_customer，再执行业务SQL；实际测试四个有效身份均非sysadmin、非db_owner，越权SQL真实被拒绝。')
    p('应用角色服务于可信后端，不作为每个顾客独立的数据库登录。顾客所有权由后端会话的UserId传入受限订单过程；角色密码不交给顾客。店员和顾客没有原表任意写权限，管理员也没有架构和账号管理权限。')
    table(['场景','统一状态和错误码','实际处理'],[
        ['错误凭据或未登录','401 AUTH_FAILED / UNAUTHENTICATED','不进入工作区；不暴露账号和哈希'],
        ['越权或CSRF错误','403 FORBIDDEN / CSRF_INVALID','在服务端拒绝；非ASCII错误令牌也返回403'],
        ['不可见或不存在订单','404 NOT_FOUND','统一说明不可访问，避免跨顾客枚举'],
        ['无效输入','400 INPUT_INVALID','服务端类型、范围和空数组检查'],
        ['唯一和FK冲突','409 CONSTRAINT_CONFLICT','数据库原始异常转为友好提示，事务回滚'],
        ['缺货和错误状态','409 BUSINESS_RULE','不部分扣库；重复确认及取消受限'],
        ['真实连接故障','503 DB_UNAVAILABLE','不向界面返回连接地址、SQL或堆栈'],
        ['事务失败分类','503 TRANSACTION_FAILED','40001类错误测试采用明确故障注入，验证分类及日志']],[4.2,6.0,7.0])
    error=next(x for x in browser['requests'] if x['code']=='CONSTRAINT_CONFLICT')
    log=next(json.loads(line) for line in (root/'result/detailed-request-log.jsonl').read_text(encoding='utf-8').splitlines()
             if json.loads(line)['request_id']==error['request_id'])
    p('本轮W11实际请求的公开日志节选如下。界面中的编号与request_id相同；按编号即可定位本机详细原因，公开记录只导出安全字段。')
    para=p(json.dumps(log,ensure_ascii=False,indent=2));para.paragraph_format.line_spacing=1.1
    for run in para.runs:run.font.size=Pt(9)
    p('原始公开证据 result/detailed-request-log.jsonl；每条HTTP记录可与detailed-browser.json按request_id对应。')

    new('运行证据的读取方式与复现实验步骤')
    p('以下每个步骤编号均绑定一次实际执行或实际界面状态。W为真实Edge操作，S为SQLCMD执行，T为pytest执行。图1和图2是模型设计图；后续业务界面均为真实运行截图或其连续矩形裁剪，未改写图中金额、状态和提示。SQL及测试输出在只读核验页展示，页面明确注明来源，不冒充SSMS或终端。')
    table(['编号','执行动作','对应输入和证据'],[
        ['准备','创建独立_Test库并配置test.env','setup从随包SQL建立基线，再执行真实迁移；禁止覆盖现有库'],
        ['T01','执行pytest stage2/tests -v','43个参数化及交叉用例；XML与完整stdout随包提供'],
        ['S01','SQLCMD运行report_verification.sql','查状态计数、完成单总额、六种商品库存销量、11条明细'],
        ['S02','SQLCMD运行regression.sql','双向语义对比、完整性与权限，共13个PASS；临时写入回滚'],
        ['S03','SQLCMD运行normalization_demo.sql','仅临时表；复现修改异常，再分解、连接和独立登记类别'],
        ['W01至W21','运行browser_acceptance --detailed','四账号在真实Edge执行表单、CRUD、确认、取消和故障；21状态截图'],
        ['收尾','再次验证基线并核对源数据','只清理_Test库临时订单和商品；原库与演示库保持保留']],[2.0,6.0,9.2])
    p('首次环境按stage2/README.md创建虚拟环境和独立数据库。已配置环境的采集命令：')
    p('.\\.venv\\Scripts\\python.exe -m stage2.tools.capture_report_evidence\n.\\.venv\\Scripts\\python.exe -m stage2.tools.browser_acceptance --detailed\n.\\.venv\\Scripts\\python.exe -m pytest stage2/tests/test_integration.py::test_baseline_and_migration -q')
    p('上表按建议复现和阅读顺序编排，实际执行时间以UTC记录为准；本轮集成输出在界面采集后复跑，用例清理同时恢复基线。W图属于同一个界面流程；草稿编号以图中WEB编号为准，后续修改、确认、取消均是该编号。不同实验轮次会生成新编号，不应把两个轮次的图当作同一订单。')
    p('执行输出的核验页逐行呈现subprocess实际输出，注明命令、执行时间、退出码及输出SHA256；截图与原始文本的对应行号在result/detailed-runs/manifest.json中可查。')

    new('S03 规范化异常与分解的实际执行',True)
    output('S03_normalization',1,
        '步骤S03：SQLCMD运行normalization_demo.sql。在临时关系R中插入P01、P02，两者均属于C01奶茶；只把P01的类别名称改为鲜奶茶。',
        '观察中间结果，同一个CategoryCode=C01出现两个名称，实际复现修改异常。随后分成商品关系与类别关系，只修改类别表的一行；末尾连接结果两行都为鲜奶茶，且PASS说明原关系还原与独立类别登记检查通过。无损与保持依赖的理论证明见前文，样例只是实现核对。')

    new('S01 基线金额 库存与销量的实际核验',True)
    output('S01_baseline',1,
        '步骤S01：运行sql/report_verification.sql；先按Status分组，再对COMPLETED订单关联明细求和，并查询六种商品当前库存、销量和销售额。',
        '读图先看库名确认是隔离_Test库，再看COMPLETED=6、CANCELLED=1和6单15杯86.0000元。D001库存20、销量4；D003库存5、销量5；D005与D006销量0仍列出。库存是盘点快照，不应再减去历史销售量。')

    new('S01 十一条历史订单明细的实际输出',True)
    output('S01_baseline',2,
        '继续步骤S01：按OrderNo、LineNumber排序查询OrderLine，查看编号、行号、商品、杯数和历史成交单价。',
        '图中保留11条明细，其中取消订单的明细仍存在；销售汇总按订单状态过滤，不能把所有明细都算入完成销售。MT-20261001-001包含D001两杯和D002一杯，验证一张订单可包含多商品。逐行迁移前后expected/actual见before-after.json，13项回归再做双向比较。')

    new('S02 迁移 完整性和权限的实际回归',True)
    output('S02_regression',1,
        '步骤S02：SQLCMD以-b遇错返回非零，运行regression.sql。每项先执行断言，满足后才打印对应PASS；任一不相等或非法写入被接受，脚本会抛错。',
        '图中01至06核对原数据语义与历史库存；07、08以547拒绝非法外码和负库存；09说明当前菜单改价不改历史价；10合法写入成功后回滚；11至13验证店员可读菜单但不能改价或读账号凭据，拒绝码229。共13个PASS、退出码0，原始完整输出也保留末尾业务结果表。')

    new('W01 W02 登录操作和错误密码反馈',True)
    ui('W01',width=14.6,maxheight=7.0,extra='从本机私有账号文件读取各自随机密码；报告和提交包不包含密码。')
    ui('W02',width=18.0,maxheight=2.0,extra='HTTP记录为401 AUTH_FAILED；错误密码不会建立登录会话。',box=(465,915,980,980))
    p('两图分别对应提交前的登录表单和提交错误密码后的实际红色通知。错误提示下附本次请求编号，方便从日志定位；不能把该图当作成功登录的证据。正确登录见下一步骤。')

    new('W03 顾客登录后读取实际商品菜单',True)
    ui('W03',width=24.8,maxheight=12.2,box=(130,100,1310,850),
        extra='登录成功后的用户身份、菜单名称与价格均由后端返回；D001为6.00元、D003为4.00元。截图包含角色入口和六种商品。')
    p('检查要点：customer可以切换菜单、订单和库存；销售统计及管理员维护表单不可见。入口差异与后端权限测试配合使用，后面的越权API用例才是权限拒绝的直接证据。')

    new('W04 W05 多商品草稿的新增和修改',True)
    ui('W04',width=24.8,maxheight=5.0,extra='订单头与两条明细一次保存成功；此时仍为DRAFT，不扣库存。')
    ui('W05',width=24.8,maxheight=5.0,extra='两图订单编号相同。D001数量2到3，金额12到18；D003仍为1杯4元，所以总额16到22元。')
    p('对应链条：POST /api/orders创建，PUT /api/orders/该编号修改，GET读取明细。该组截图把输入数量、计算公式和数据库返回结果放在同一流程中，支持多商品与明细修改要求。')

    new('W07 W08 店员确认订单并实际扣减库存',True)
    ui('W07',width=24.8,maxheight=4.8,extra='与W05为同一订单，完成时仍按原草稿单价计算22.00元；确认由clerk执行。')
    ui('W08',width=24.8,maxheight=6.4,extra='对照S01原库存：D001扣3杯，20−3=17；D003扣1杯，5−1=4。店员页面只有查询，无盘点维护按钮。')

    new('W06 W09 顾客订单隔离与完成状态同步',True)
    ui('W06',width=24.0,maxheight=2.1,extra='这是在customer草稿已经存在时查看guest列表；同库不同会话，看不到他人订单。')
    ui('W09',width=24.0,maxheight=2.5,extra='顾客重新查询后可看到店员处理结果，完成单不再显示草稿编辑与删除按钮。')
    p('查询过程按实际登录账号过滤，而不是让页面自行隐藏他人行。下面SQL的@ActorId由可信会话经DAO传入；顾客条件限制CreatedByUserId，员工可查全部。猜测他人编号后读取或写入的反例另在集成测试中验证。')
    code('sql/application.sql',19,24)
    p('空列表图只说明该次账号查询结果为空；结合已存在的customer订单、不同会话的请求记录和跨顾客拒绝用例，才支持订单隔离的结论。')

    new('W19 W20 散客草稿的创建与必要删除',True)
    ui('W19',width=24.0,maxheight=5.0,extra='guest没有绑定会员，仍可建立自己的新草稿；会员NULL由数据库测试核对，截图本身只展示数量和金额。')
    ui('W20',width=24.0,maxheight=2.1,extra='DELETE后列表为空；集成测试另检查头和明细都已删除。')
    p('会员customer与散客guest在应用中都属于customer角色，区别是账号是否绑定MemberCode。服务与过程根据账号确定会员，不信任顾客提交的任意会员号；因此不能通过修改JSON把草稿挂到别人名下。')
    p('删除仅针对尚未确认的DRAFT。在同一事务先删明细再删头，避免孤立数据；完成单则保留，通过取消记录状态和库存回补。该区别对应课程要求中的必要删除，并不允许为展示CRUD而随意抹去已完成交易。')

    new('W10 管理员新增商品与修改菜单价格',True)
    ui('W10',width=10,maxheight=5.4,extra='新增字段为编号UI_TEST、名称验收测试茶、类别测试饮品、价格3.50、阈值2；再次编辑价格4.00。图展示修改完成后的卡片。')
    p('操作过程：在商品维护表单输入上述值并保存，等待新增卡片；点击该卡片的编辑，在回填表单改价并保存。DAO新增时同事务建立零库存；修改只更新商品行。POST与PUT均实际返回200，见detailed-browser.json的UI_TEST请求。')
    p('菜单当前价与历史成交价是不同事实。本图只证明菜单维护成功；历史订单不受改价影响的结论由S02第09项及集成测试提供。')

    new('W12 管理员盘点库存为八杯',True)
    ui('W12',width=24.8,maxheight=9.0,extra='在库存维护表单输入商品编号UI_TEST、quantity=8并保存，等待表格返回新值。')
    p('读图定位UI_TEST这一行：可售杯数8、预警阈值2、状态充足。管理员比店员多出盘点及删除记录操作。盘点修改的是当前可售杯数，不代表一笔销售，也不会更改订单历史。')
    p('对应接口PUT /api/inventory/UI_TEST，Service要求admin及0至1000000的整数；DAO锁定商品后更新或新增库存，最后统一提交。负数、小数、布尔值和不存在商品的处理见集成测试。')

    new('W13 零库存删除和重新登记',True)
    ui('W13',width=24.8,maxheight=9.0,extra='先将杯数改为0并等待表格确实显示0，之后点击删除记录并确认。图是删除后的查询结果。')
    p('图中UI_TEST商品行仍存在，但杯数和状态显示未登记。这是Product左连接Inventory的结果，说明删除的是库存记录，未把商品一并删掉。随后仍用同一库存表单保存0杯，可重新建立记录；该PUT请求已保存在运行记录。')
    p('同名成功通知可能仍来自上一次保存，因此自动化必须等待表格数值更新再删除，不能只等“库存已保存”。本轮已按实际行值等待，避免把测试脚本竞态误当作应用缺陷。')

    new('W14 删除无订单引用商品后的结果',True)
    ui('W14',width=24.8,maxheight=9.0,extra='零库存记录重建后返回菜单，删除UI_TEST并确认；等待商品已删除通知和菜单刷新。')
    p('图中只剩原六种商品，测试饮品不再存在。此操作只允许无订单引用且库存为0的商品；如果商品已被订单引用，FK将拒绝硬删除，事务回滚，管理员可改为下架。被引用删除的反例由集成测试真实执行，不以当前成功删除图证明。')

    new('W15 订单确认后的销售统计',True)
    ui('W15',width=24.8,maxheight=7.2,extra='在取消订单之前查询，所以该22元完成单应当计入销量。')
    table(['商品或合计','S01完成销售基线','本轮新增完成销售','本步骤实际预期'],[
        ['D001','4杯 24.00元','3杯 18.00元','7杯 42.00元'],
        ['D003','5杯 20.00元','1杯 4.00元','6杯 24.00元'],
        ['全部饮品','15杯 86.00元','4杯 22.00元','19杯 108.00元']],[4.0,6.0,6.0,8.0])
    p('表中合计由图内六行求和得到，页面没有单独展示总额卡片。销售查询仅统计COMPLETED，保留零销量商品；取消后的销售是否退出统计由集成断言核对。')

    new('W17 取消完成单后订单历史仍保留',True)
    ui('W17',width=24.8,maxheight=10.2,extra='找到W04至W07同一WEB编号执行取消。订单金额仍为22.00元，状态改为已取消，而不是直接删除记录。')
    p('原七笔历史订单同时显示在店员列表中，其中原本就有一笔取消单。本步骤应定位本轮新建WEB编号这一行，避免把历史取消单当成取消动作成功的证据。下一图另查实际库存，核对回补结果。')

    new('W18 取消后库存回补的实际数值',True)
    ui('W18',width=24.8,maxheight=8.2,extra='在取消接口返回成功后重新发起库存查询，等待D001=20且D003=5再截图。')
    table(['商品','确认前 S01','确认后 W08','取消后 W18'],[
        ['D001','20','17','20'],['D003','5','4','5']],[4.0,6.0,6.0,8.0])
    p('前后对照支持本轮完成单回补了实际扣减数量；“重复取消不重复回补”及“零库存行被删除后取消仍能重建”的边界结论，由T01对应集成用例再次验证。历史StockApplied=0的完成单不可套用本流程。')

    new('W11 W16 错误反馈和实际请求的对应',True)
    ui('W11',width=20.5,maxheight=2.3,extra='数据库唯一约束真实产生冲突；API为409 CONSTRAINT_CONFLICT，未重复插入商品。')
    ui('W16',width=20.5,maxheight=2.3,extra='临时故障只作用于本次隔离服务；随即恢复原连接配置。API为503 DB_UNAVAILABLE。')
    table(['步骤','HTTP与错误码','实际请求编号'],[
        [step,str(next(r for r in figs[step]['related_recent_responses'][::-1] if r['http_status']>=400)['http_status'])+' '+
              next(r for r in figs[step]['related_recent_responses'][::-1] if r['http_status']>=400)['code'],
              next(r for r in figs[step]['related_recent_responses'][::-1] if r['http_status']>=400)['request_id']]
        for step in ['W11','W16']],[2.0,8.0,14.0])
    p('图中的编号、上表及公开JSONL日志一一对应。两张通知图只证明用户看到的提示；原始请求记录和日志进一步证明错误来自实际请求。界面均未包含SQL、服务器地址、文件路径或异常堆栈。')

    new('W21 移动尺寸页面的实际检查')
    p('步骤W21：使用真实Edge引擎创建390×844视口，以移动布局选项打开登录页。执行document.documentElement.scrollWidth <= window.innerWidth断言通过，再截图。原图为完整页面，页面内容可以纵向滚动。')
    fig(figs['W21']['image'],'W21','390像素宽移动布局的登录页',width=6.3,maxheight=16.0)
    p('图中标题、输入框和登录按钮未横向溢出；本项只验证移动尺寸登录页面，不宣称已覆盖全部手机型号或移动端业务页面。')

    new('测试设计与关键反例的输入和断言')
    p('测试不只检查HTTP成功，还直接查询数据库确认状态、行数、库存和金额。conftest强制加载private/test.env且库名必须以_Test结尾，每例前后恢复Baseline；因此输入相同、预期确定，各用例不会互相依赖脏数据。')
    table(['用例场景','实际输入或触发','预期与实际断言'],[
        ['账号与会话','四角色登录退出；错误密码；停用当前账号','正常200；错误401；停用会话下次请求拒绝'],
        ['后端越权','customer/clerk直接请求商品或库存修改','403；绕过按钮不可获得权限'],
        ['顾客隔离','A创建草稿后B查询、修改、删除该编号','404或拒绝；A数据保留'],
        ['SQL与HTML输入','登录注入、搜索注入、特殊商品名称','无绕过；查询按值绑定；文本不当HTML执行'],
        ['库存参数','负数、小数、布尔值及非法JSON','400；原库存不变'],
        ['引用与唯一','重复编号；被引用商品删除；非法会员','409或业务拒绝；不留下部分头或明细'],
        ['缺货回滚','订单前项D001可扣，后项D004库存0','409；前项已执行扣减回滚，状态仍草稿'],
        ['并发不超卖','D001库存20；两单并发各购买15杯','一单200、一单409；最终库存5，非负'],
        ['重复动作','同一订单确认两次、取消两次','首个合法动作成功，第二次拒绝；不重复扣回'],
        ['历史价格与库存','保存报价后改菜单价；历史单取消','原报价确认；历史开库单禁止回补'],
        ['实际数据库权限','四应用角色查询有效身份并尝试越权SQL','sysadmin=0、db_owner=0；DDL、敏感读写拒绝'],
        ['连接与事务异常','真实不可达连接；注入40001异常','503且友好错误；日志包含对应request_id']],[3.5,6.1,7.6])
    p('下一组三张T01截图连续覆盖完整详细输出，共43个用例。该数包含参数化展开，不应把测试函数个数当作测试例数。命令、实际耗时和XML均来自本轮重新执行。')

    for i,obs in enumerate([
        '本段包括五项复核用例、迁移基线和多角色登录。PASSED只有断言完成后才出现；不是手工把测试名排成通过列表。',
        '本段继续覆盖认证、越权、商品库存CRUD、无效参数、注入和约束、顾客所有权等。参数化用例逐个列出。',
        '本段包括订单事务、缺货回滚、非法会员、并发、真实应用角色限制、连接错误和停用会话。末尾给出43 passed及实际耗时；XML统计tests=43、failures=0、errors=0。'],1):
        new('T01 集成测试实际输出 '+str(i),True)
        output('T01_pytest',i,'步骤T01：执行 .venv\\Scripts\\python.exe -m pytest stage2/tests -v，并生成独立JUnit XML。',obs)

    new('复核发现的问题 修复和再次验证')
    p('初轮通过后，再按交叉操作和边界条件复核，实际复现五个缺陷。五个新增测试在旧实现均失败；修复后五个均通过，再执行完整43例和真实浏览器流程。以下保留问题及影响，避免只给“全部通过”而缺少改进过程。')
    table(['问题和触发','修改前表现','最终处理和验证'],[
        ['搜索D001后编辑含D003草稿','下拉框丢失D003选项','筛选展示与完整目录分开；修改3杯仍为12.00元'],
        ['售空后删零库存行，再取消完成单','返回成功但未恢复库存行','锁定商品并补建缺失库存；恢复2杯；重复取消拒绝'],
        ['合法单价上限与大数量','保存成功，查询总额溢出503','汇总转decimal(18,2)；19999999998.00可读取'],
        ['非ASCII错误CSRF头é','字符串比较触发500','UTF8字节恒定时间比较；返回403 CSRF_INVALID'],
        ['已登录时身份复查遇连接失败','日志角色错误记录anonymous','诊断保留最后认证角色；授权仍依赖实时数据库身份']],[4.5,5.4,7.3])
    p('另外在ER中补全联系名称并注明v0.1的最低一条明细仅为业务规则；规范化证明没有把电话可空唯一误当作全关系候选码。自动化脚本也增加库存行值等待，避免同文字通知导致竞态。证据见course-audit.json及course-review.md。')
    h('失败证据和成功证据的边界',2)
    p('旧版本五项失败的摘要、测试文件和证据摘要值保留在course-audit.json；本轮T01截图展示修复后实际结果。SQL错误229/547、真实连接不可达和并发争抢均为实际SQL Server执行；事务错误40001分类使用故障注入，不能称为已自然发生并复现真实死锁。')
    p('演示截图中库存确认和恢复用一笔可售的22元订单完成；缺货回滚、重复取消等反例由独立集成用例证明。报告明确每张图能证明什么，避免把成功界面扩张为所有边界都正确。')

    new('提交包复现与测试后数据核验')
    p('此前已将提交包解压到独立中文路径，新建虚拟环境并从requirements安装，再用包内SQL建立新数据库。复制后的SQL回归13项、集成43例、浏览器18项以及BAT入口四账号登录均通过；记录位于result/package-replay.json。本版扩写文档和采集工具，应用和核心SQL保持与该已执行副本一致，最终ZIP另校验全部文件摘要。')
    h('空环境复现的主要命令',2)
    p('在解压后包含sql、stage2和启动BAT的根目录执行：')
    p('python -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -r stage2/requirements-dev.txt\n.\\.venv\\Scripts\\python.exe -m stage2.tools.setup --from-scripts --database MilkTeaShopV10_Demo\n.\\.venv\\Scripts\\python.exe -m stage2')
    p('目标库或配置已存在时脚本拒绝覆盖，应换新库名及--env-file。已有v0.1时不使用--from-scripts，脚本先COPY_ONLY备份，再还原到新库后迁移。随机密码保存在初始化机器自己的private目录，不能从公共报告寻找通用密码。')
    h('测试后的核验',2)
    p('本轮浏览器结束后再运行基线测试，清理本轮WEB订单及测试商品并恢复_Test库库存，随后核对原库六表与演示库的原字段。原库和演示库不执行测试清理。收尾证据见result/detailed-cleanup.txt和result/detailed-final-validation.json。')
    table(['复现检查','实际验收记录','本版范围'],[
        ['独立新库和新环境','package-replay.json及package-pytest.xml','此前复制包真实执行；最终检查核心文件摘要一致'],
        ['本轮补采','detailed-browser.json','18项检查、60次HTTP、21个指定界面状态；无未捕获JS异常'],
        ['本轮SQL与测试','detailed-runs/manifest.json','13项SQL、43例集成重新执行；原始stdout和XML齐全'],
        ['提交文件完整性','ZIP内SHA256.json','逐文件摘要、凭据排除、Word/PDF和配图来源检查']],[3.5,6.0,7.7])

    new('三 实验总结与小组责任')
    p('本阶段将v0.1的六表样例扩展为有账号、草稿和库存事务的实际Web应用。ER模型明确可选会员、订单明细和角色关联；FD分析支持保留合理结构；迁移以独立副本和语义回归证明历史不被改写。页面操作与API、DAO、数据库约束和事务有实际对应，结果由金额、杯数、状态和错误请求共同核对。')
    p('复核经验是把操作串起来：搜索会影响草稿编辑，商品上限会影响汇总，库存删除会影响取消。单个接口成功不能替代跨场景验证；截图也必须写清产生条件和观察对象。后续可扩展原料配方、支付退款和公网部署，但这些不在本阶段完成声明中。')
    table(['成员','责任及课堂演示安排'],[
        ['袁远冬','需求、ER、迁移和仓库整合；演示基数、独立副本及迁移前后核验'],
        ['陆乐天','FD、范式、数据字典与DAO；演示无损分解、约束及CRUD回归'],
        ['罗金浩','Web、角色与异常、测试证据与报告；演示22元订单全流程、回滚和请求追踪']],[2.8,14.4])
    p('上表是责任与讲解安排；本次可核验的代码、文档和运行主要由AI辅助形成。没有虚构三人分别手工开发的时长、讨论原话或个人验收签名。人工阅读、独立操作和签字应由本人完成并如实补充。AI使用过程见docs/ai_log.md，分工说明见docs/contribution.md。')
    table(['证据类型','读取方法'],[
        ['设计和迁移','docs/design.md、data-dictionary.md、migration-guide.md；可编辑SVG与SQL'],
        ['逐图索引','result/detailed-figure-index.md；按图号、步骤和原图定位'],
        ['真实界面与请求','result/detailed-screenshots/、detailed-browser.json、detailed-request-log.jsonl'],
        ['实际SQL及测试输出','result/detailed-runs/；manifest记录命令、时间、退出码、行号和SHA256'],
        ['原数据与复核','before-after.json；course-audit.json；package-replay.json']],[4.1,13.1])
    p('课程依据：本地第五周、第六周、第7至9周任务讲解。技术参考：Flask官方Web安全与会话文档；Microsoft Learn的sp_setapprole、应用程序角色及SQL Server表提示文档。课程没有给出明确评分量表，本报告据任务逐项验收，不推断教师分数。')

    polish_tables()
    doc.core_properties.title='校园奶茶店数据库应用第二阶段详细图文实验报告'
    doc.core_properties.author='袁远冬 陆乐天 罗金浩'
    doc.core_properties.subject='第五至第九周 设计 实现 测试及逐步运行截图'
    for border in list(doc.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    target=root/'阶段报告_详细图文版.docx';doc.save(target)
    metadata={'code_commit':c['sha'],'report_file':target.name,'report_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'sql_pass':13,'integration_tests':43,'browser_checks':18,'http_responses':len(browser['requests']),
        'business_state_screenshots':len(figs),'figures':figure_index,'code_excerpts':code_sources,
        'output_viewer_label':'verbatim actual stdout viewer, not native SSMS or terminal screenshot'}
    (root/'result/detailed-report-source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    index=['# 详细图文版逐图证据索引','','图1和图2为ER设计图；以下为实际运行截图及真实输出核验页。',
           '','| 图号 | 步骤 | 截图内容 | 原始证据 |','| --- | --- | --- | --- |']
    for f in figure_index:index.append(f'| {f["figure"]} | {f["step"]} | {f["title"]} | [{f["source"].split("/")[-1]}]({f["source"].removeprefix("result/")}) |')
    index+=['','每图的操作和结果解释位于报告相邻正文。图号与detailed-report-source.json一致；21个界面状态另附detailed-browser.json的动作、时间、SHA256及相邻实际HTTP记录。',
            '','SQL和pytest图片为实际输出核验页。命令与逐字输出见detailed-runs/manifest.json及同目录TXT/XML；图片只裁去空白边缘，不改写结果。']
    (root/'result/detailed-figure-index.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    print('Created',target,'figures including ER:',number)
