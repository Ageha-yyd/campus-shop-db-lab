"""The only runtime module containing SQL/ODBC. Values always use bound parameters."""
import os
from contextlib import contextmanager

import pyodbc
pyodbc.pooling = False  # Role-activated connections are destroyed, never returned to a pool.

from .errors import AppError


class DAO:
    def __init__(self, config):
        self.config = config

    def connect(self, role):
        # Fixed allowlist, never a caller-supplied SQL identifier.
        if role not in {'auth', 'admin', 'clerk', 'customer'}:
            raise AppError('FORBIDDEN', '您没有此操作权限', 403)
        conn = pyodbc.connect(self.config['DB_CONNECTIONS'][role], timeout=3, autocommit=True)
        try:
            # ODBC CALL uses a top-level RPC; prepared EXEC would fail SQL error 15422.
            conn.execute('{CALL sys.sp_setapprole (?,?)}', 'mt_'+role, self.config['DB_ROLE_PASSWORDS'][role])
            conn.autocommit = False
            return conn
        except Exception:
            conn.close()
            raise

    @contextmanager
    def transaction(self, role):
        conn = self.connect(role)
        try:
            conn.execute('SET XACT_ABORT ON; SET ANSI_WARNINGS ON; SET ARITHABORT ON; SET NUMERIC_ROUNDABORT OFF;')
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def rows(cur):
        return [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]

    def user(self, username):
        with self.transaction('auth') as conn:
            rows = self.rows(conn.execute('SELECT UserId,Username,PasswordHash,Role,EmployeeCode,MemberCode FROM dbo.AppUser WHERE Username=? AND IsActive=1', username))
            return rows[0] if rows else None

    def products(self, role, search=''):
        with self.transaction(role) as c:
            return self.rows(c.execute('SELECT ProductCode,ProductName,Category,UnitPrice,RestockThreshold,IsActive FROM dbo.Product WHERE ProductName LIKE ? OR ProductCode LIKE ? ORDER BY ProductCode', '%'+search+'%', '%'+search+'%'))

    def product_save(self, code, values, new):
        with self.transaction('admin') as c:
            if new:
                c.execute('INSERT dbo.Product(ProductCode,ProductName,Category,UnitPrice,RestockThreshold,IsActive) VALUES(?,?,?,?,?,?)', code, *values)
                c.execute('INSERT dbo.Inventory(ProductCode,Quantity) VALUES(?,0)', code)
            elif c.execute('UPDATE dbo.Product SET ProductName=?,Category=?,UnitPrice=?,RestockThreshold=?,IsActive=? WHERE ProductCode=?', *values, code).rowcount != 1:
                raise AppError('NOT_FOUND', '商品不存在', 404)

    def product_delete(self, code):
        with self.transaction('admin') as c:
            stock = c.execute('SELECT Quantity FROM dbo.Inventory WITH(UPDLOCK,HOLDLOCK) WHERE ProductCode=?', code).fetchone()
            if stock and stock[0] != 0:
                raise AppError('BUSINESS_RULE', '请先盘点并清空该商品库存', 409)
            c.execute('DELETE dbo.Inventory WHERE ProductCode=?', code)
            if c.execute('DELETE dbo.Product WHERE ProductCode=?', code).rowcount != 1:
                raise AppError('NOT_FOUND', '商品不存在', 404)

    def inventory(self, role):
        with self.transaction(role) as c:
            return self.rows(c.execute('SELECT p.ProductCode,p.ProductName,i.Quantity,p.RestockThreshold,i.UpdatedAt FROM dbo.Product p LEFT JOIN dbo.Inventory i ON i.ProductCode=p.ProductCode ORDER BY p.ProductCode'))

    def inventory_save(self, code, quantity):
        with self.transaction('admin') as c:
            # Lock product first, consistent with draft save and stock confirmation.
            if not c.execute('SELECT ProductCode FROM dbo.Product WITH(UPDLOCK,HOLDLOCK) WHERE ProductCode=?', code).fetchone():
                raise AppError('NOT_FOUND', '商品不存在', 404)
            if c.execute('SELECT Quantity FROM dbo.Inventory WITH(UPDLOCK,HOLDLOCK) WHERE ProductCode=?', code).fetchone():
                c.execute('UPDATE dbo.Inventory SET Quantity=?,UpdatedAt=SYSUTCDATETIME() WHERE ProductCode=?', quantity, code)
            else:
                c.execute('INSERT dbo.Inventory(ProductCode,Quantity) VALUES(?,?)', code, quantity)

    def inventory_delete(self, code):
        with self.transaction('admin') as c:
            row = c.execute('SELECT Quantity FROM dbo.Inventory WITH(UPDLOCK,HOLDLOCK) WHERE ProductCode=?', code).fetchone()
            if row is None:
                raise AppError('NOT_FOUND', '库存记录不存在', 404)
            if row[0] != 0:
                raise AppError('BUSINESS_RULE', '仅可删除数量为零的库存记录', 409)
            c.execute('DELETE dbo.Inventory WHERE ProductCode=?', code)

    def orders(self, user, number=None):
        with self.transaction(user['Role']) as c:
            return self.rows(c.execute('EXEC dbo.usp_Orders ?,?', user['UserId'], number))

    def lines(self, user, number):
        with self.transaction(user['Role']) as c:
            return self.rows(c.execute('EXEC dbo.usp_OrderLines ?,?', user['UserId'], number))

    def order_save(self, user, number, items, member, new):
        with self.transaction(user['Role']) as c:
            c.execute('EXEC dbo.usp_OrderSave ?,?,?,?,?', user['UserId'], number, items, member, new)

    def order_action(self, user, number, action):
        with self.transaction(user['Role']) as c:
            c.execute('EXEC dbo.usp_OrderAction ?,?,?', user['UserId'], number, action)

    def sales(self, role):
        with self.transaction(role) as c:
            return self.rows(c.execute('SELECT * FROM dbo.vw_ProductSales ORDER BY ProductCode'))


def connection_strings():
    # ODBC escaping prevents configuration delimiters from changing connection options.
    def quote(value):
        return '{'+value.replace('}', '}}')+'}'
    base = ';'.join(f'{key}={quote(os.environ[name])}' for key, name in [('DRIVER','DB_DRIVER'),('SERVER','DB_SERVER'),('DATABASE','DB_NAME')])
    return {role: base+';Encrypt=yes;TrustServerCertificate=yes;Trusted_Connection=yes;' for role in ['auth','admin','clerk','customer']}
