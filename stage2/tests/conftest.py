import json
import os
from pathlib import Path

import pyodbc
import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
# Explicit, separately provisioned test environment. Never use the demo/source DB.
load_dotenv(ROOT/'private'/'test.env',override=True)
if not os.environ.get('DB_NAME','').endswith('_Test'):
    raise RuntimeError('Run setup --database MilkTeaShopV10_Test --from-scripts --env-file stage2/private/test.env first.')

from stage2.web.app import create_app


@pytest.fixture(scope='session')
def db():
    conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+os.environ['DB_SERVER']+';DATABASE='+os.environ['DB_NAME']+';Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;',autocommit=True)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean(db):
    def restore():
        db.execute("DELETE dbo.OrderLine WHERE OrderNo LIKE 'WEB-%'; DELETE dbo.ShopOrder WHERE OrderNo LIKE 'WEB-%';")
        db.execute("DELETE dbo.Inventory WHERE ProductCode NOT IN(SELECT ProductCode FROM dbo.Baseline_Product); DELETE dbo.Product WHERE ProductCode NOT IN(SELECT ProductCode FROM dbo.Baseline_Product);")
        db.execute('UPDATE i SET Quantity=b.Quantity,UpdatedAt=b.UpdatedAt FROM dbo.Inventory i JOIN dbo.Baseline_Inventory b ON i.ProductCode=b.ProductCode;')
        db.execute('UPDATE p SET ProductName=b.ProductName,Category=b.Category,UnitPrice=b.UnitPrice,RestockThreshold=b.RestockThreshold,IsActive=b.IsActive FROM dbo.Product p JOIN dbo.Baseline_Product b ON p.ProductCode=b.ProductCode;')
        db.execute('UPDATE dbo.AppUser SET IsActive=1;')
    restore()
    yield
    restore()


@pytest.fixture
def app():
    return create_app({'TESTING':True})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def credentials():
    return json.loads((ROOT/'private'/(os.environ['DB_NAME']+'_accounts.json')).read_text())


@pytest.fixture
def login(credentials):
    def inner(client,name='admin'):
        token=client.get('/api/session').json['data']['csrf']
        response=client.post('/api/login',json={'username':name,'password':credentials[name]},headers={'X-CSRF-Token':token})
        assert response.status_code==200,response.json
        return {'X-CSRF-Token':response.json['data']['csrf']}
    return inner
