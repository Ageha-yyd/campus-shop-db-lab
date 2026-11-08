import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pyodbc
import pytest

from stage2.web.app import ROOT


def draft(c,h,items=None,**extra):
    r=c.post('/api/orders',json={'items':items or [{'product_code':'D001','quantity':2}],**extra},headers=h)
    assert r.status_code==200,r.json
    return r.json['data']['order_no']


def count(db,table):
    return db.execute('SELECT COUNT(*) FROM dbo.'+table).fetchval()


def test_baseline_and_migration(db):
    assert count(db,'Product')==6 and count(db,'ShopOrder')==7 and count(db,'OrderLine')==11
    assert db.execute('SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales').fetchval()==Decimal('86.00')
    assert db.execute('SELECT COUNT(*) FROM dbo.Inventory i JOIN dbo.Baseline_Inventory b ON i.ProductCode=b.ProductCode AND i.Quantity=b.Quantity').fetchval()==6


@pytest.mark.parametrize('role',['admin','clerk','customer','guest'])
def test_login_all_roles_and_logout(client,login,role):
    h=login(client,role)
    assert client.get('/api/products').status_code==200
    assert client.post('/api/logout',json={},headers=h).status_code==200
    assert client.get('/api/products').status_code==401


def test_unauthenticated_and_csrf(client):
    assert client.get('/api/orders').json['code']=='UNAUTHENTICATED'
    assert client.post('/api/login',json={}).json['code']=='CSRF_INVALID'


@pytest.mark.parametrize('name', ["admin' OR 1=1--",'admin','unknown'])
def test_bad_credentials_and_login_injection(client,name):
    token=client.get('/api/session').json['data']['csrf']
    r=client.post('/api/login',json={'username':name,'password':'wrong-password'},headers={'X-CSRF-Token':token})
    assert r.status_code==401 and r.json['code']=='AUTH_FAILED'


@pytest.mark.parametrize('role',['clerk','customer'])
def test_backend_role_denial(client,login,role):
    h=login(client,role)
    assert client.put('/api/inventory/D001',json={'quantity':999},headers=h).json['code']=='FORBIDDEN'
    assert client.delete('/api/products/D001',headers=h).status_code==403
    assert client.post('/api/products',json={},headers=h).status_code==403


def test_product_and_inventory_crud(client,login,db):
    h=login(client)
    p={'product_code':'T001','name':'测试茶','category':'测试','price':'3.50','threshold':2,'active':True}
    assert client.post('/api/products',json=p,headers=h).status_code==200
    p['price']='4.00'
    assert client.put('/api/products/T001',json=p,headers=h).status_code==200
    assert client.put('/api/inventory/T001',json={'quantity':8},headers=h).status_code==200
    assert client.delete('/api/inventory/T001',headers=h).json['code']=='BUSINESS_RULE'
    client.put('/api/inventory/T001',json={'quantity':0},headers=h)
    assert client.delete('/api/inventory/T001',headers=h).status_code==200
    assert client.put('/api/inventory/T001',json={'quantity':0},headers=h).status_code==200
    assert client.delete('/api/products/T001',headers=h).status_code==200
    assert db.execute("SELECT COUNT(*) FROM dbo.Product WHERE ProductCode='T001'").fetchval()==0


@pytest.mark.parametrize('value',[-1,1.5,True,'3',None,1000001])
def test_invalid_inventory_parameters(client,login,value):
    h=login(client)
    r=client.put('/api/inventory/D001',json={'quantity':value},headers=h)
    assert r.status_code==400 and r.json['code']=='INPUT_INVALID'


def test_missing_and_invalid_json(client,login):
    h=login(client)
    assert client.put('/api/inventory/NOTFOUND',json={'quantity':3},headers=h).status_code==404
    assert client.post('/api/orders',data='{bad',content_type='application/json',headers=h).status_code==400
    assert client.post('/api/orders',json={'items':[]},headers=h).status_code==400
    assert client.post('/api/orders',json={'items':[{'product_code':'D001','quantity':True}]},headers=h).status_code==400


def test_search_parameterization_and_output_escaping(client,login,db):
    h=login(client)
    assert client.get('/api/products',query_string={'q':"'; DROP TABLE dbo.Product;--"}).json['data']==[]
    assert count(db,'Product')==6
    p={'product_code':'XSS','name':'<img src=x onerror=alert(1)>','category':'测试','price':'1.00','threshold':1}
    assert client.post('/api/products',json=p,headers=h).status_code==200
    assert client.get('/api/products?q=XSS').json['data'][0]['ProductName']==p['name']


def test_constraint_duplicate_and_referenced_delete(client,login,db):
    h=login(client)
    p={'product_code':'D001','name':'重复','category':'奶茶','price':'1.00','threshold':1}
    r=client.post('/api/products',json=p,headers=h)
    assert r.status_code==409 and r.json['code']=='CONSTRAINT_CONFLICT'
    client.put('/api/inventory/D001',json={'quantity':0},headers=h)
    r=client.delete('/api/products/D001',headers=h)
    assert r.status_code==409 and r.json['code']=='CONSTRAINT_CONFLICT'
    assert db.execute("SELECT COUNT(*) FROM dbo.Inventory WHERE ProductCode='D001'").fetchval()==1


def test_customer_full_draft_crud_and_ownership(app,client,login,db):
    h=login(client,'customer')
    n=draft(client,h,[{'product_code':'D001','quantity':1},{'product_code':'D001','quantity':2}])
    assert len(client.get('/api/orders/'+n).json['data']['lines'])==2
    assert db.execute('SELECT MemberCode FROM dbo.ShopOrder WHERE OrderNo=?',n).fetchval()=='M001'
    assert client.put('/api/orders/'+n,json={'items':[{'product_code':'D003','quantity':2}]},headers=h).status_code==200
    assert len(client.get('/api/orders/'+n).json['data']['lines'])==1
    assert client.post('/api/orders/'+n+'/submit',json={},headers=h).status_code==403
    other=app.test_client(); other_h=login(other,'guest')
    assert other.get('/api/orders').json['data']==[]
    assert other.get('/api/orders/'+n).status_code==404
    assert other.delete('/api/orders/'+n,headers=other_h).status_code==404
    assert client.delete('/api/orders/'+n,headers=h).status_code==200
    assert count(db,'ShopOrder')==7


def test_guest_and_customer_cannot_forge_member(client,login,db):
    h=login(client,'guest'); n=draft(client,h,member_code='M002')
    assert db.execute('SELECT MemberCode FROM dbo.ShopOrder WHERE OrderNo=?',n).fetchval() is None


def test_submit_stock_prices_cancel_and_repeat(client,login,db):
    h=login(client,'clerk')
    n=draft(client,h,[{'product_code':'D001','quantity':2},{'product_code':'D001','quantity':3},{'product_code':'D003','quantity':1}])
    db.execute("UPDATE dbo.Product SET UnitPrice=9.90 WHERE ProductCode='D001'")
    r=client.post('/api/orders/'+n+'/submit',json={},headers=h)
    assert r.status_code==200,r.json
    assert db.execute("SELECT Quantity FROM dbo.Inventory WHERE ProductCode='D001'").fetchval()==15
    assert db.execute('SELECT SUM(UnitPrice*Quantity) FROM dbo.OrderLine WHERE OrderNo=?',n).fetchval()==34
    assert client.post('/api/orders/'+n+'/submit',json={},headers=h).status_code==409
    assert client.put('/api/orders/'+n,json={'items':[{'product_code':'D001','quantity':1}]},headers=h).status_code==409
    assert client.delete('/api/orders/'+n,headers=h).status_code==409
    assert client.post('/api/orders/'+n+'/cancel',json={},headers=h).status_code==200
    assert db.execute("SELECT Quantity FROM dbo.Inventory WHERE ProductCode='D001'").fetchval()==20
    assert client.post('/api/orders/'+n+'/cancel',json={},headers=h).status_code==409
    assert db.execute('SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales').fetchval()==86


def test_short_stock_rolls_back_earlier_product_deduction(client,login,db):
    h=login(client,'clerk')
    n=draft(client,h,[{'product_code':'D001','quantity':2},{'product_code':'D004','quantity':1}])
    r=client.post('/api/orders/'+n+'/submit',json={},headers=h)
    assert r.status_code==409,r.json
    assert db.execute("SELECT Quantity FROM dbo.Inventory WHERE ProductCode='D001'").fetchval()==20
    assert db.execute('SELECT Status FROM dbo.ShopOrder WHERE OrderNo=?',n).fetchval()=='DRAFT'


def test_invalid_member_whole_order_rollback(client,login,db):
    h=login(client,'clerk')
    r=client.post('/api/orders',json={'items':[{'product_code':'D001','quantity':1}],'member_code':'NO_MEMBER'},headers=h)
    assert r.status_code==409 and r.json['code']=='CONSTRAINT_CONFLICT'
    assert count(db,'ShopOrder')==7 and count(db,'OrderLine')==11


def test_inactive_product_and_empty_order(client,login,db):
    h=login(client,'clerk')
    db.execute("UPDATE dbo.Product SET IsActive=0 WHERE ProductCode='D001'")
    r=client.post('/api/orders',json={'items':[{'product_code':'D001','quantity':1}]},headers=h)
    assert r.status_code==409 and count(db,'ShopOrder')==7


def test_historical_order_cancellation_is_blocked(client,login,db):
    h=login(client,'clerk')
    r=client.post('/api/orders/MT-20261001-001/cancel',json={},headers=h)
    assert r.status_code==403
    assert db.execute('SELECT SUM(SalesAmount) FROM dbo.vw_ProductSales').fetchval()==86


def test_concurrent_stock_no_overselling(app,login,db):
    clients=[app.test_client(),app.test_client()]
    headers=[login(c,'clerk') for c in clients]
    numbers=[draft(c,h,[{'product_code':'D001','quantity':15}]) for c,h in zip(clients,headers)]
    def submit(i):
        return clients[i].post('/api/orders/'+numbers[i]+'/submit',json={},headers=headers[i]).status_code
    with ThreadPoolExecutor(2) as pool:
        statuses=list(pool.map(submit,range(2)))
    assert sorted(statuses)==[200,409]
    assert db.execute("SELECT Quantity FROM dbo.Inventory WHERE ProductCode='D001'").fetchval()==5


@pytest.mark.parametrize('role',['auth','admin','clerk','customer'])
def test_actual_restricted_database_accounts(app,role):
    with app.extensions['dao'].transaction(role) as c:
        assert tuple(c.execute('SELECT IS_SRVROLEMEMBER(\'sysadmin\'),IS_ROLEMEMBER(\'db_owner\')').fetchone())==(0,0)
        with pytest.raises(pyodbc.Error):
            c.execute('DROP TABLE dbo.Product')


@pytest.mark.parametrize('role',['clerk','customer'])
def test_direct_database_product_and_stock_mutation_denied(app,role):
    for sql in ["UPDATE dbo.Product SET UnitPrice=1 WHERE ProductCode='D001'", "UPDATE dbo.Inventory SET Quantity=999 WHERE ProductCode='D001'",'SELECT PasswordHash FROM dbo.AppUser','SELECT * FROM dbo.ShopOrder','DELETE dbo.OrderLine']:
        with pytest.raises(pyodbc.Error):
            with app.extensions['dao'].transaction(role) as c:
                c.execute(sql)


def test_database_connection_failure_is_sanitized(app,client,login):
    login(client)
    old=app.config['DB_CONNECTIONS']['auth']
    app.config['DB_CONNECTIONS']['auth']='DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:127.0.0.1,1;DATABASE=missing;UID=hidden-user;PWD=hidden-password;Encrypt=yes;TrustServerCertificate=yes'
    r=client.get('/api/products')
    app.config['DB_CONNECTIONS']['auth']=old
    assert r.status_code==503 and r.json['code']=='DB_UNAVAILABLE'
    assert all(x not in r.text for x in ['hidden-password','pyodbc','SQL','127.0.0.1','Traceback'])


def test_transaction_failure_is_sanitized_and_logged(app,client,login,monkeypatch):
    h=login(client,'clerk')
    def fail(*args):
        raise pyodbc.Error('40001','SQL internal transaction detail hidden')
    monkeypatch.setattr(app.extensions['dao'],'order_save',fail)
    r=client.post('/api/orders',json={'items':[{'product_code':'D001','quantity':1}]},headers=h)
    assert r.status_code==503 and r.json['code']=='TRANSACTION_FAILED'
    assert 'internal' not in r.text
    records=[json.loads(line) for line in (ROOT/'logs'/'app.jsonl').read_text(encoding='utf-8').splitlines()]
    matching=[x for x in records if x['request_id']==r.json['request_id']]
    assert len(matching)>=2
    assert any(x.get('role')=='clerk' and x.get('code')=='TRANSACTION_FAILED' for x in matching)


def test_deactivated_account_session_is_rejected(client,login,db):
    login(client,'customer')
    db.execute("UPDATE dbo.AppUser SET IsActive=0 WHERE Username='customer'")
    assert client.get('/api/orders').status_code==401
