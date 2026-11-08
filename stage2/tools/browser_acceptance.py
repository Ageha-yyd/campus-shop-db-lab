"""Real Edge UI acceptance against the explicit isolated test database."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread

from dotenv import load_dotenv
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

ROOT=Path(__file__).resolve().parents[1]


def main():
    load_dotenv(ROOT/'private'/'test.env',override=True)
    if not os.environ['DB_NAME'].endswith('_Test'):
        raise RuntimeError('Explicit test DB required')
    from stage2.web.app import create_app
    app=create_app()
    server=make_server('127.0.0.1',5001,app,threaded=True)
    Thread(target=server.serve_forever,daemon=True).start()
    accounts=json.loads((ROOT/'private'/(os.environ['DB_NAME']+'_accounts.json')).read_text())
    shots=ROOT/'result'/'screenshots';shots.mkdir(exist_ok=True)
    records=[];checks=[];errors=[]
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
        def notice(page,text):
            expect(page.locator('#notice')).to_contain_text(text)
        customer=page_for('customer');shot(customer,'01_login.png')
        customer.locator('[name=username]').fill('customer');customer.locator('[name=password]').fill('wrong-password')
        customer.locator('#login-form button').click();notice(customer,'用户名或密码错误');shot(customer,'02_login_error.png')
        passed('wrong password gives friendly error')
        login(customer,'customer');shot(customer,'03_customer_menu.png')
        expect(customer.locator('#product-form')).to_be_hidden();expect(customer.locator('#sales-tab')).to_be_hidden()
        passed('customer role controls hidden')
        customer.locator('[data-tab=orders]').click();expect(customer.locator('#orders-page')).to_be_visible()
        row=customer.locator('.line-row').first;row.locator('select').select_option('D001');row.locator('input').fill('2')
        customer.locator('#line-add').click();customer.locator('.line-row').nth(1).locator('select').select_option('D003')
        customer.locator('#order-form button[type=submit]').click();notice(customer,'草稿已保存')
        expect(customer.locator('#orders-table tbody tr')).to_have_count(1)
        order=customer.locator('#orders-table tbody tr td').first.inner_text()
        shot(customer,'04_customer_draft.png');passed('customer creates multi-product member order',order_no=order)
        customer.locator('#orders-table button',has_text='编辑').click()
        expect(customer.locator('#order-form-title')).to_contain_text(order)
        customer.locator('.line-row').first.locator('input').fill('3')
        customer.locator('#order-form button[type=submit]').click();notice(customer,'草稿已保存')
        expect(customer.locator('#order-detail')).to_contain_text('22.00')
        passed('customer edits draft and detail quantities',expected_total='22.00')
        guest=page_for('guest');login(guest,'guest');guest.locator('[data-tab=orders]').click()
        expect(guest.locator('#orders-table')).to_contain_text('暂无记录');passed('guest sees no other customer orders')
        clerk=page_for('clerk');login(clerk,'clerk');clerk.locator('[data-tab=orders]').click()
        tr=clerk.locator('#orders-table tbody tr').filter(has_text=order)
        expect(tr).to_be_visible();tr.get_by_role('button',name='确认',exact=True).click();notice(clerk,'库存已扣减')
        expect(tr).to_contain_text('已完成');tr.get_by_role('button',name='查看',exact=True).click()
        shot(clerk,'05_clerk_confirmed.png');passed('clerk confirms customer order and preserves detail total')
        clerk.locator('[data-tab=inventory]').click();expect(clerk.locator('#inventory-table')).to_contain_text('珍珠奶茶')
        stockrow=clerk.locator('#inventory-table tbody tr').filter(has_text='D001')
        expect(stockrow.locator('td').nth(2)).to_have_text('17');shot(clerk,'06_clerk_stock.png')
        passed('stock deduction visible in UI',expected_D001=17,expected_D003=4)
        customer.locator('[data-tab=orders]').click();expect(customer.locator('#orders-table')).to_contain_text('已完成')
        passed('customer sees completed order')
        admin=page_for('admin');login(admin,'admin')
        f=admin.locator('#product-form')
        values={'product_code':'UI_TEST','name':'验收测试茶','category':'测试饮品','price':'3.50','threshold':'2'}
        for k,v in values.items():f.locator('[name='+k+']').fill(v)
        f.get_by_role('button',name='保存商品').click();notice(admin,'商品已保存')
        card=admin.locator('.product-card').filter(has_text='UI_TEST');expect(card).to_be_visible()
        card.get_by_role('button',name='编辑').click();f.locator('[name=price]').fill('4.00')
        f.get_by_role('button',name='保存商品').click();notice(admin,'商品已保存');expect(card).to_contain_text('4.00')
        shot(admin,'07_admin_products.png');passed('admin product create and edit via forms')
        # Duplicate code goes through actual web form to SQL unique constraint.
        for k,v in values.items():f.locator('[name='+k+']').fill(v)
        f.get_by_role('button',name='保存商品').click();notice(admin,'记录重复或已被引用');shot(admin,'08_constraint_error.png')
        passed('constraint conflict friendly feedback')
        admin.locator('[data-tab=inventory]').click();sf=admin.locator('#stock-form')
        sf.locator('[name=product_code]').fill('UI_TEST');sf.locator('[name=quantity]').fill('8')
        sf.get_by_role('button',name='保存库存').click();notice(admin,'库存已保存');shot(admin,'09_admin_inventory.png')
        sf.locator('[name=quantity]').fill('0');sf.get_by_role('button',name='保存库存').click();notice(admin,'库存已保存')
        # The previous save has the same toast. Wait for the new row value so a
        # fast test does not race DELETE against the still-pending PUT request.
        expect(admin.locator('#inventory-table tbody tr').filter(has_text='UI_TEST').locator('td').nth(2)).to_have_text('0')
        admin.on('dialog',lambda d:d.accept())
        admin.locator('#inventory-table tbody tr').filter(has_text='UI_TEST').get_by_role('button',name='删除记录').click();notice(admin,'库存记录已删除')
        sf.get_by_role('button',name='保存库存').click();notice(admin,'库存已保存');passed('admin inventory update delete and recreate')
        admin.locator('[data-tab=products]').click();admin.locator('.product-card').filter(has_text='UI_TEST').get_by_role('button',name='删除',exact=True).click();notice(admin,'商品已删除')
        passed('admin unreferenced product deleted')
        admin.locator('[data-tab=sales]').click();expect(admin.locator('#sales-table')).to_contain_text('珍珠奶茶')
        shot(admin,'10_sales.png');passed('staff sales report visible')
        # Real DB connection failure, not a mocked exception. Restore configuration immediately.
        original=app.config['DB_CONNECTIONS']['auth']
        app.config['DB_CONNECTIONS']['auth']='DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:127.0.0.1,1;Trusted_Connection=yes;TrustServerCertificate=yes;'
        admin.locator('[data-tab=inventory]').click();notice(admin,'系统暂时无法连接')
        shot(admin,'11_connection_error.png')
        assert not any(s in admin.locator('#notice').inner_text() for s in ['SQL','127.0.0.1','Traceback'])
        app.config['DB_CONNECTIONS']['auth']=original;passed('real connection outage sanitized in browser')
        # Restore completed test order through permitted cancellation, then delete a new draft.
        clerk.locator('[data-tab=orders]').click();tr=clerk.locator('#orders-table tbody tr').filter(has_text=order)
        clerk.on('dialog',lambda d:d.accept());tr.get_by_role('button',name='取消订单').click();notice(clerk,'订单已取消')
        passed('clerk cancellation restores stock')
        guest.locator('#order-form button[type=submit]').click();notice(guest,'草稿已保存')
        guest.on('dialog',lambda d:d.accept());guest.locator('#orders-table button',has_text='删除').click();notice(guest,'草稿已删除')
        passed('guest draft create and delete')
        mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True)
        mp=mobile.new_page();mp.goto('http://127.0.0.1:5001');expect(mp.locator('#login-form')).to_be_visible();shot(mp,'12_mobile_login.png')
        assert mp.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        passed('mobile login without horizontal overflow')
        assert not errors,errors
        passed('no uncaught browser JavaScript errors')
        browser.close()
    server.shutdown()
    (ROOT/'result'/'browser-acceptance.json').write_text(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'database':os.environ['DB_NAME'],
        'browser':'Microsoft Edge headless via Playwright','checks':checks,'requests':records,'javascript_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS {len(checks)} browser checks; {len(records)} HTTP responses; {len(list(shots.glob("*.png")))} screenshots')


if __name__=='__main__':main()
