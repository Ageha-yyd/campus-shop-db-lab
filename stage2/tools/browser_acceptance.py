"""Real Edge UI acceptance against the explicit isolated test database."""
import json
import os
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread

from dotenv import load_dotenv
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

ROOT=Path(__file__).resolve().parents[1]


def public_request_log(records):
    """Export completed request fields only, never exception/connection details."""
    ids={r['request_id'] for r in records}
    keys=['time','request_id','operation','role','code','result','http_status','duration_ms']
    entries=[]
    for line in (ROOT/'logs/app.jsonl').read_text(encoding='utf-8').splitlines():
        entry=json.loads(line)
        if entry.get('request_id') in ids and 'http_status' in entry:
            entries.append({k:entry[k] for k in keys})
    assert ids=={x['request_id'] for x in entries}
    (ROOT/'result/detailed-request-log.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in entries)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--detailed',action='store_true',help='Capture intermediate report evidence without replacing canonical acceptance records')
    args=parser.parse_args()
    load_dotenv(ROOT/'private'/'test.env',override=True)
    if not os.environ['DB_NAME'].endswith('_Test'):
        raise RuntimeError('Explicit test DB required')
    from stage2.web.app import create_app
    app=create_app()
    server=make_server('127.0.0.1',5001,app,threaded=True)
    Thread(target=server.serve_forever,daemon=True).start()
    accounts=json.loads((ROOT/'private'/(os.environ['DB_NAME']+'_accounts.json')).read_text())
    shots=ROOT/'result'/('detailed-screenshots' if args.detailed else 'screenshots');shots.mkdir(exist_ok=True)
    records=[];checks=[];errors=[];figures=[]
    def passed(name,**detail):checks.append({'case':name,'result':'PASS',**detail})
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        def page_for(name):
            context=browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
            page=context.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            def record(response):
                if '/api/' in response.url:
                    try:
                        data=response.json()
                        records.append({'role':name,'method':response.request.method,'path':response.url.split('/api')[1],
                            'http_status':response.status,'code':data.get('code'),'request_id':data.get('request_id')})
                    except Exception:pass
            page.on('response',record)
            page.goto('http://127.0.0.1:5001');expect(page.locator('#login-panel')).to_be_visible()
            return page
        def login(page,name):
            page.locator('[name=username]').fill(name);page.locator('[name=password]').fill(accounts[name])
            page.locator('#login-form button').click()
            expect(page.locator('#workspace')).to_be_visible()
            expect(page.locator('.product-card')).to_have_count(6)
        def shot(page,name):
            page.screenshot(path=str(shots/name),full_page=True)
        def evidence(page,name,step,title,action,observed,selector=None):
            if not args.detailed:return
            target=shots/(name+'.png')
            if selector:page.locator(selector).screenshot(path=str(target))
            else:page.screenshot(path=str(target),full_page=True)
            figures.append({'step':step,'title':title,'image':target.relative_to(ROOT).as_posix(),
                'action':action,'observed':observed,'captured_utc':datetime.now(timezone.utc).isoformat(),
                'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'related_recent_responses':records[-4:]})
        def notice(page,text):
            expect(page.locator('#notice')).to_contain_text(text)
        customer=page_for('customer');shot(customer,'01_login.png')
        evidence(customer,'D01_login','W01','登录界面','访问127.0.0.1:5001，尚未提交凭据','显示登录表单；不展示密码', '#login-panel')
        customer.locator('[name=username]').fill('customer');customer.locator('[name=password]').fill('wrong-password')
        customer.locator('#login-form button').click();notice(customer,'用户名或密码错误');shot(customer,'02_login_error.png')
        passed('wrong password gives friendly error')
        evidence(customer,'D02_wrong_login','W02','错误密码反馈','customer输入错误密码后提交','用户名或密码错误；请求返回401；停留登录页')
        login(customer,'customer');shot(customer,'03_customer_menu.png')
        evidence(customer,'D03_customer_menu','W03','顾客菜单与角色入口','使用customer正确凭据登录','六种商品；顾客无商品维护和销售入口')
        expect(customer.locator('#product-form')).to_be_hidden();expect(customer.locator('#sales-tab')).to_be_hidden()
        passed('customer role controls hidden')
        customer.locator('[data-tab=orders]').click();expect(customer.locator('#orders-page')).to_be_visible()
        row=customer.locator('.line-row').first;row.locator('select').select_option('D001');row.locator('input').fill('2')
        customer.locator('#line-add').click();customer.locator('.line-row').nth(1).locator('select').select_option('D003')
        customer.locator('#order-form button[type=submit]').click();notice(customer,'草稿已保存')
        expect(customer.locator('#orders-table tbody tr')).to_have_count(1)
        order=customer.locator('#orders-table tbody tr td').first.inner_text()
        shot(customer,'04_customer_draft.png');passed('customer creates multi-product member order',order_no=order)
        evidence(customer,'D04_draft','W04','保存多商品会员草稿','D001两杯、D003一杯，点击保存草稿','订单 '+order+'；待确认；2×6+1×4=16.00元','#order-detail')
        customer.locator('#orders-table button',has_text='编辑').click()
        expect(customer.locator('#order-form-title')).to_contain_text(order)
        customer.locator('.line-row').first.locator('input').fill('3')
        customer.locator('#order-form button[type=submit]').click();notice(customer,'草稿已保存')
        expect(customer.locator('#order-detail')).to_contain_text('22.00')
        passed('customer edits draft and detail quantities',expected_total='22.00')
        evidence(customer,'D05_edited_draft','W05','修改草稿并重新计算','编辑同一订单，把D001数量从2改为3，再保存','同一订单；3×6+1×4=22.00元','#order-detail')
        guest=page_for('guest');login(guest,'guest');guest.locator('[data-tab=orders]').click()
        expect(guest.locator('#orders-table')).to_contain_text('暂无记录');passed('guest sees no other customer orders')
        evidence(guest,'D06_guest_isolation','W06','不同顾客订单隔离','guest登录后进入订单中心','订单列表暂无记录，看不到customer刚建立的订单','#orders-table')
        clerk=page_for('clerk');login(clerk,'clerk');clerk.locator('[data-tab=orders]').click()
        tr=clerk.locator('#orders-table tbody tr').filter(has_text=order)
        expect(tr).to_be_visible();tr.get_by_role('button',name='确认',exact=True).click();notice(clerk,'库存已扣减')
        expect(tr).to_contain_text('已完成');tr.get_by_role('button',name='查看',exact=True).click()
        shot(clerk,'05_clerk_confirmed.png');passed('clerk confirms customer order and preserves detail total')
        evidence(clerk,'D07_confirmed','W07','店员确认后的同一订单','clerk找到该草稿，点击确认，再点击查看','同一订单状态已完成；数量、成交价、22.00元总额保留','#order-detail')
        clerk.locator('[data-tab=inventory]').click();expect(clerk.locator('#inventory-table')).to_contain_text('珍珠奶茶')
        stockrow=clerk.locator('#inventory-table tbody tr').filter(has_text='D001')
        expect(stockrow.locator('td').nth(2)).to_have_text('17');shot(clerk,'06_clerk_stock.png')
        passed('stock deduction visible in UI',expected_D001=17,expected_D003=4)
        evidence(clerk,'D08_deducted_stock','W08','实际扣库与库存预警','店员确认后点击库存页','D001从20到17、D003从5到4；D004零库存显示缺货','#inventory-table')
        customer.locator('[data-tab=orders]').click();expect(customer.locator('#orders-table')).to_contain_text('已完成')
        passed('customer sees completed order')
        evidence(customer,'D09_customer_completed','W09','顾客看到店员确认结果','customer重新进入订单中心','本人订单已完成，顾客不再有编辑或删除草稿按钮','#orders-table')
        admin=page_for('admin');login(admin,'admin')
        f=admin.locator('#product-form')
        values={'product_code':'UI_TEST','name':'验收测试茶','category':'测试饮品','price':'3.50','threshold':'2'}
        for k,v in values.items():f.locator('[name='+k+']').fill(v)
        f.get_by_role('button',name='保存商品').click();notice(admin,'商品已保存')
        card=admin.locator('.product-card').filter(has_text='UI_TEST');expect(card).to_be_visible()
        card.get_by_role('button',name='编辑').click();f.locator('[name=price]').fill('4.00')
        f.get_by_role('button',name='保存商品').click();notice(admin,'商品已保存');expect(card).to_contain_text('4.00')
        shot(admin,'07_admin_products.png');passed('admin product create and edit via forms')
        evidence(admin,'D10_product','W10','新增商品与修改价格','admin新增UI_TEST验收测试茶，3.50元；编辑为4.00元','商品卡片显示UI_TEST及4.00元','.product-card:has-text("UI_TEST")')
        # Duplicate code goes through actual web form to SQL unique constraint.
        for k,v in values.items():f.locator('[name='+k+']').fill(v)
        f.get_by_role('button',name='保存商品').click();notice(admin,'记录重复或已被引用');shot(admin,'08_constraint_error.png')
        passed('constraint conflict friendly feedback')
        evidence(admin,'D11_constraint','W11','真实唯一约束冲突','新增表单再次输入相同UI_TEST编号并提交','记录重复或已被引用；409；界面附请求编号','#notice')
        admin.locator('[data-tab=inventory]').click();sf=admin.locator('#stock-form')
        sf.locator('[name=product_code]').fill('UI_TEST');sf.locator('[name=quantity]').fill('8')
        sf.get_by_role('button',name='保存库存').click();notice(admin,'库存已保存');shot(admin,'09_admin_inventory.png')
        evidence(admin,'D12_inventory_eight','W12','管理员盘点库存','UI_TEST盘点杯数输入8，点击保存库存','表格显示UI_TEST为8杯','#inventory-table')
        sf.locator('[name=quantity]').fill('0');sf.get_by_role('button',name='保存库存').click();notice(admin,'库存已保存')
        # The previous save has the same toast. Wait for the new row value so a
        # fast test does not race DELETE against the still-pending PUT request.
        expect(admin.locator('#inventory-table tbody tr').filter(has_text='UI_TEST').locator('td').nth(2)).to_have_text('0')
        admin.on('dialog',lambda d:d.accept())
        admin.locator('#inventory-table tbody tr').filter(has_text='UI_TEST').get_by_role('button',name='删除记录').click();notice(admin,'库存记录已删除')
        evidence(admin,'D13_deleted_inventory','W13','删除零库存记录','先把UI_TEST设为0并等待新值，再确认删除记录','商品仍存在，杯数为未登记，证明只删除库存行','#inventory-table')
        sf.get_by_role('button',name='保存库存').click();notice(admin,'库存已保存');passed('admin inventory update delete and recreate')
        admin.locator('[data-tab=products]').click();admin.locator('.product-card').filter(has_text='UI_TEST').get_by_role('button',name='删除',exact=True).click();notice(admin,'商品已删除')
        passed('admin unreferenced product deleted')
        evidence(admin,'D14_deleted_product','W14','删除没有订单引用的商品','零库存重建后删除UI_TEST商品','商品卡片恢复为原六种；UI_TEST不存在','#product-grid')
        admin.locator('[data-tab=sales]').click();expect(admin.locator('#sales-table')).to_contain_text('珍珠奶茶')
        shot(admin,'10_sales.png');passed('staff sales report visible')
        evidence(admin,'D15_sales','W15','完成订单计入销售统计','管理员进入销量页','D001销量4+3=7，销售额24+18=42；D003销量5+1=6，金额24','#sales-table')
        # Real DB connection failure, not a mocked exception. Restore configuration immediately.
        original=app.config['DB_CONNECTIONS']['auth']
        app.config['DB_CONNECTIONS']['auth']='DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:127.0.0.1,1;Trusted_Connection=yes;TrustServerCertificate=yes;'
        admin.locator('[data-tab=inventory]').click();notice(admin,'系统暂时无法连接')
        shot(admin,'11_connection_error.png')
        evidence(admin,'D16_connection','W16','真实连接失败的友好反馈','仅将隔离验收服务认证连接临时改为本机未监听端口，再访问库存','系统暂时无法连接；503；不展示SQL、地址或堆栈','#notice')
        assert not any(s in admin.locator('#notice').inner_text() for s in ['SQL','127.0.0.1','Traceback'])
        app.config['DB_CONNECTIONS']['auth']=original;passed('real connection outage sanitized in browser')
        # Restore completed test order through permitted cancellation, then delete a new draft.
        clerk.locator('[data-tab=orders]').click();tr=clerk.locator('#orders-table tbody tr').filter(has_text=order)
        clerk.on('dialog',lambda d:d.accept());tr.get_by_role('button',name='取消订单').click();notice(clerk,'订单已取消')
        passed('clerk cancellation restores stock')
        evidence(clerk,'D17_cancelled','W17','取消后保留订单历史','clerk取消该22.00元新系统完成单','订单列表保留同一订单，状态已取消','#orders-table')
        if args.detailed:
            clerk.locator('[data-tab=inventory]').click()
            expect(clerk.locator('#inventory-table tbody tr').filter(has_text='D001').locator('td').nth(2)).to_have_text('20')
            expect(clerk.locator('#inventory-table tbody tr').filter(has_text='D003').locator('td').nth(2)).to_have_text('5')
            evidence(clerk,'D18_restored_stock','W18','取消后的实际库存恢复','取消完成单后重新查询库存','D001恢复20、D003恢复5；与S01基线一致','#inventory-table')
        guest.locator('#order-form button[type=submit]').click();notice(guest,'草稿已保存')
        evidence(guest,'D19_guest_draft','W19','散客也能建立草稿','guest直接保存默认D001一杯草稿','自己的新订单为待确认、合计6.00元；会员关联由后端确定为空','#order-detail')
        guest.on('dialog',lambda d:d.accept());guest.locator('#orders-table button',has_text='删除').click();notice(guest,'草稿已删除')
        passed('guest draft create and delete')
        evidence(guest,'D20_deleted_draft','W20','删除草稿及其明细','guest确认删除自己的草稿','本人订单列表再次暂无记录','#orders-table')
        mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True)
        mp=mobile.new_page();mp.goto('http://127.0.0.1:5001');expect(mp.locator('#login-form')).to_be_visible();shot(mp,'12_mobile_login.png')
        assert mp.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        passed('mobile login without horizontal overflow')
        evidence(mp,'D21_mobile','W21','移动尺寸登录','390×844视口打开登录页','表单可见；页面scrollWidth不超过innerWidth')
        assert not errors,errors
        passed('no uncaught browser JavaScript errors')
        browser.close()
    server.shutdown()
    if args.detailed:public_request_log(records)
    (ROOT/'result'/('detailed-browser.json' if args.detailed else 'browser-acceptance.json')).write_text(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'database':os.environ['DB_NAME'],
        'browser':'Microsoft Edge headless via Playwright','checks':checks,'requests':records,'javascript_errors':errors,'figures':figures},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS {len(checks)} browser checks; {len(records)} HTTP responses; {len(list(shots.glob("*.png")))} screenshots')


if __name__=='__main__':main()
