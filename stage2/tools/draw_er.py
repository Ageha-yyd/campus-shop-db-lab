"""Editable, deterministic SVG ER source and lossless PNG exports via Edge."""
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
W,H=1680,1400
FIELDS={
'Product':['PK ProductCode','ProductName','Category','UnitPrice','RestockThreshold','IsActive'],
'Inventory':['PK FK ProductCode','Quantity','UpdatedAt'],
'Employee':['PK EmployeeCode','DisplayName','JobTitle','IsActive'],
'Member':['PK MemberCode','DisplayName','Phone ? UNIQUE if not null','JoinedAt'],
'ShopOrder':['PK OrderNo','OrderedAt','FK EmployeeCode','FK MemberCode ?','Status'],
'OrderLine':['PK FK OrderNo','PK LineNumber','FK ProductCode','Quantity','UnitPrice (historical)'],
'AppUser':['PK UserId | AK Username','PasswordHash','Role / IsActive','FK EmployeeCode ? UNIQUE*','FK MemberCode ? UNIQUE*']}


def draw(version):
    if version=='v01':
        nodes={'Employee':(35,130),'ShopOrder':(625,130),'Member':(1215,130),'Product':(35,800),'OrderLine':(625,800),'Inventory':(1215,800)}
        fields={k:list(v) for k,v in FIELDS.items()}
        links=[('Employee','ShopOrder','1','0..N',[(455,310),(625,310)],(495,288)),
        ('Member','ShopOrder','0..1','0..N',[(1215,310),(1045,310)],(1085,288)),
        ('ShopOrder','OrderLine','1','1..N*',[(835,440),(835,800)],(850,620)),
        ('Product','OrderLine','1','0..N',[(455,970),(625,970)],(490,949)),
        ('Product','Inventory','1','0..1',[(245,1110),(245,1225),(1425,1225),(1425,1110)],(745,1203))]
    else:
        nodes={'Employee':(35,130),'AppUser':(625,130),'Member':(1215,130),'Product':(35,650),'ShopOrder':(625,650),'Inventory':(35,1040),'OrderLine':(1215,950)}
        fields={k:list(v) for k,v in FIELDS.items()}
        fields['ShopOrder'][2]='FK EmployeeCode ? (draft)'
        fields['ShopOrder']+=['FK CreatedByUserId ?','StockApplied']
        links=[('Employee','AppUser','0..1','0..1',[(455,285),(625,285)],(486,261)),
        ('Member','AppUser','0..1','0..1',[(1215,285),(1045,285)],(1088,261)),
        ('AppUser','ShopOrder','0..1','0..N',[(835,440),(835,650)],(850,550)),
        ('Employee','ShopOrder','0..1*','0..N',[(245,440),(245,510),(720,510),(720,650)],(355,492)),
        ('Member','ShopOrder','0..1','0..N',[(1425,440),(1425,510),(950,510),(950,650)],(1145,492)),
        ('Product','Inventory','1','0..1',[(245,960),(245,1040)],(260,1015)),
        ('Product','OrderLine','1','0..N',[(455,820),(535,820),(535,1305),(1425,1305),(1425,1260)],(885,1287)),
        ('ShopOrder','OrderLine','1','1..N*',[(1045,855),(1120,855),(1120,1090),(1215,1090)],(1133,991))]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#20382c;font-size:23px}.title{font-size:30px;font-weight:bold}.heading{font-size:27px;font-weight:bold}.card{fill:#fff;stroke:#829984;stroke-width:2}.label{font-size:22px;font-weight:bold;paint-order:stroke;stroke:white;stroke-width:8px;stroke-linejoin:round}</style>',
        '<rect width="1680" height="1400" fill="white"/>',f'<text x="35" y="48" class="title">校园奶茶店 {version.replace("v01","v0.1").replace("v10","v1.0")} 实体联系图</text>',
        '<text x="35" y="90">PK 主码   AK 候选码   FK 外码   ? 可空   min..max 为该端可关联记录数   * 见业务规则</text>']
    names={
      ('Employee','AppUser'):('员工账号',490,335),('Member','AppUser'):('会员账号',1080,335),
      ('AppUser','ShopOrder'):('创建',853,600),
      ('Employee','ShopOrder'):('经办',485,355) if version=='v01' else ('经办',390,550),
      ('Member','ShopOrder'):('归属会员',1080,355) if version=='v01' else ('归属会员',1110,550),
      ('ShopOrder','OrderLine'):('包含',858,675) if version=='v01' else ('包含',1134,1020),
      ('Product','OrderLine'):('对应饮品',480,1015) if version=='v01' else ('对应饮品',800,1284),
      ('Product','Inventory'):('库存快照',760,1260) if version=='v01' else ('库存',120,1006)}
    for a,b,mina,minb,points,label in links:
        out.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+'" fill="none" stroke="#627d64" stroke-width="3"/>')
        # Label cardinalities at each actual endpoint; optional participation via zero.
        for point,adjacent,txt in [(points[0],points[1],mina),(points[-1],points[-2],minb)]:
            x,y=point;dx,dy=adjacent[0]-x,adjacent[1]-y
            tx=x+(13 if dx>=0 else -65);ty=y+(33 if dy>0 else -14)
            out.append(f'<text x="{tx}" y="{ty}" class="label">{txt}</text>')
        name,nx,ny=names[(a,b)]
        out.append(f'<text x="{nx}" y="{ny}" style="font-size:20px">{name}</text>')
    for name,(x,y) in nodes.items():
        ff=fields[name];height=230 if version=='v10' and name=='Inventory' else 310
        out+=[f'<g id="{name}"><rect x="{x}" y="{y}" width="420" height="{height}" rx="10" class="card"/>',f'<rect x="{x+1}" y="{y+1}" width="418" height="50" rx="8" fill="#e6eddf"/>',f'<text x="{x+17}" y="{y+34}" class="heading">{name}</text>']
        for i,f in enumerate(ff):out.append(f'<text x="{x+16}" y="{y+85+i*36}">{escape(f)}</text>')
        out.append('</g>')
    notes=['* 订单至少一行是业务要求；v0.1外码不能保证，v1.0由事务过程实现。']
    if version=='v10':notes=['* 完成单必须有员工；草稿可无员工。订单至少一行由事务过程保证。','* 历史单创建账号可空；账号的员工或会员非空时唯一，按角色选择。']
    for i,n in enumerate(notes):out.append(f'<text x="35" y="{1350+i*32}">{n}</text>')
    out.append('</svg>')
    path=ROOT/'docs'/('er-'+version+'.svg');path.write_text('\n'.join(out),encoding='utf-8');return path


if __name__=='__main__':
    with sync_playwright() as p:
        b=p.chromium.launch(channel='msedge',headless=True)
        page=b.new_page(viewport={'width':W,'height':H},device_scale_factor=1.5)
        for version in ['v01','v10']:
            path=draw(version);page.goto(path.as_uri());page.screenshot(path=str(path.with_suffix('.png')))
        b.close()
    print('PASS two editable SVG diagrams and high resolution PNG exports')
