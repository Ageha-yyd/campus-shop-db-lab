"""Independent course audit: cross-feature and numeric/stock boundary regressions."""
import json
from decimal import Decimal
from threading import Thread

import pyodbc
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from stage2.web.app import ROOT


def create_draft(client,headers,items):
    response=client.post('/api/orders',json={'items':items},headers=headers)
    assert response.status_code==200,response.json
    return response.json['data']['order_no']


def test_large_valid_order_total_remains_readable(client,login,db):
    headers=login(client,'clerk')
    db.execute("UPDATE dbo.Product SET UnitPrice=99999999.99 WHERE ProductCode='D001'")
    number=create_draft(client,headers,[{'product_code':'D001','quantity':100}]*2)
    response=client.get('/api/orders/'+number)
    assert response.status_code==200,response.json
    assert Decimal(response.json['data']['order']['Total'])==Decimal('19999999998.00')
    assert client.get('/api/orders').status_code==200


def test_cancel_restores_stock_after_zero_inventory_record_deleted(client,login,db):
    db.execute("INSERT dbo.Product VALUES('AUDIT',N'复核用茶',N'测试',1,1,1); INSERT dbo.Inventory(ProductCode,Quantity) VALUES('AUDIT',2);")
    headers=login(client,'clerk')
    number=create_draft(client,headers,[{'product_code':'AUDIT','quantity':2}])
    assert client.post('/api/orders/'+number+'/submit',json={},headers=headers).status_code==200
    admin_headers=login(client,'admin')
    assert client.delete('/api/inventory/AUDIT',headers=admin_headers).status_code==200
    headers=login(client,'clerk')
    response=client.post('/api/orders/'+number+'/cancel',json={},headers=headers)
    assert response.status_code==200,response.json
    assert db.execute("SELECT Quantity FROM dbo.Inventory WHERE ProductCode='AUDIT'").fetchval()==2
    assert client.post('/api/orders/'+number+'/cancel',json={},headers=headers).status_code==409


def test_non_ascii_csrf_is_rejected_as_input_not_system_error(client):
    client.get('/api/session')
    response=client.post('/api/login',json={'username':'admin','password':'invalid'},headers={'X-CSRF-Token':'é'})
    assert response.status_code==403 and response.json['code']=='CSRF_INVALID'


def test_connection_failure_log_preserves_last_authenticated_role(app,client,login,monkeypatch):
    login(client,'admin')
    def unavailable(*args):
        raise pyodbc.OperationalError('08001','audit connection unavailable')
    monkeypatch.setattr(app.extensions['dao'],'user',unavailable)
    response=client.get('/api/orders')
    assert response.status_code==503
    records=[json.loads(line) for line in (ROOT/'logs/app.jsonl').read_text(encoding='utf-8').splitlines()]
    matches=[r for r in records if r.get('request_id')==response.json['request_id']]
    assert matches and all(r['role']=='admin' for r in matches)


def test_menu_search_does_not_remove_other_products_from_draft_editor(app,client,login,credentials):
    headers=login(client,'customer')
    number=create_draft(client,headers,[{'product_code':'D003','quantity':2}])
    server=make_server('127.0.0.1',5002,app,threaded=True)
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.goto('http://127.0.0.1:5002')
            page.locator('[name=username]').fill('customer')
            page.locator('[name=password]').fill(credentials['customer'])
            page.locator('#login-form button').click()
            expect(page.locator('.product-card')).to_have_count(6)
            page.locator('#search-form input').fill('D001')
            page.locator('#search-form button').click()
            expect(page.locator('.product-card')).to_have_count(1)
            page.locator('[data-tab=orders]').click()
            page.locator('#orders-table tr').filter(has_text=number).get_by_role('button',name='编辑',exact=True).click()
            expect(page.locator('.line-row select')).to_have_value('D003')
            page.locator('.line-row input').fill('3')
            page.locator('#order-form button[type=submit]').click()
            expect(page.locator('#order-detail')).to_contain_text('12.00')
            browser.close()
    finally:
        server.shutdown()
