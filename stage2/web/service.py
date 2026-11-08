"""Business validation, role and ownership checks. No SQL in this layer."""
import json
import re
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from werkzeug.security import check_password_hash

from .errors import AppError


def text(data, key, maximum, required=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        raise AppError('INPUT_INVALID', '请检查必填项及文字长度')
    return value.strip()


def integer(data, key, low, high):
    value = data.get(key)
    if type(value) is not int or not low <= value <= high:
        raise AppError('INPUT_INVALID', '请输入范围内的整数')
    return value


def identifier(value, maximum=12):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,'+str(maximum)+'}', value):
        raise AppError('INPUT_INVALID', '编号只能包含字母 数字 横线或下划线')
    return value


class Service:
    def __init__(self, dao):
        self.dao = dao

    @staticmethod
    def allow(user, *roles):
        if not user:
            raise AppError('UNAUTHENTICATED', '请先登录', 401)
        if user['Role'] not in roles:
            raise AppError('FORBIDDEN', '您没有此操作权限', 403)

    def login(self, data):
        name = text(data, 'username', 40)
        password = text(data, 'password', 128)
        user = self.dao.user(name)
        # Constant-cost hash on unknown usernames also limits account enumeration timing.
        check_hash = user['PasswordHash'] if user else 'scrypt:32768:8:1$abcdefghijklmnop$'+'0'*128
        valid = check_password_hash(check_hash, password)
        if not user or not valid:
            raise AppError('AUTH_FAILED', '用户名或密码错误', 401)
        return user

    def products(self, user, search=''):
        self.allow(user, 'admin', 'clerk', 'customer')
        if len(search) > 80:
            raise AppError('INPUT_INVALID', '搜索文字过长')
        return self.dao.products(user['Role'], search)

    def inventory(self, user):
        self.allow(user, 'admin', 'clerk', 'customer')
        return self.dao.inventory(user['Role'])

    def orders(self, user):
        self.allow(user, 'admin', 'clerk', 'customer')
        return self.dao.orders(user)

    def detail(self, user, number):
        return {'order': self.visible_order(user, number), 'lines': self.dao.lines(user, number)}

    def product_save(self, user, data, code=None):
        self.allow(user, 'admin')
        new = code is None
        code = identifier(text(data, 'product_code', 12)) if new else identifier(code)
        name, category = text(data, 'name', 80), text(data, 'category', 30)
        try:
            price = Decimal(str(data.get('price', '')))
            if not price.is_finite() or not Decimal('0.01') <= price <= Decimal('99999999.99') or price.as_tuple().exponent < -2:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            raise AppError('INPUT_INVALID', '价格应为正数且最多两位小数') from None
        threshold = integer(data, 'threshold', 1, 1000000)
        active = data.get('active', True)
        if type(active) is not bool:
            raise AppError('INPUT_INVALID', '上架状态不正确')
        self.dao.product_save(code, (name, category, price, threshold, active), new)
        return {'product_code': code}

    def product_delete(self, user, code):
        self.allow(user, 'admin')
        self.dao.product_delete(identifier(code))

    def inventory_save(self, user, code, data):
        self.allow(user, 'admin')
        self.dao.inventory_save(identifier(code), integer(data, 'quantity', 0, 1000000))

    def inventory_delete(self, user, code):
        self.allow(user, 'admin')
        self.dao.inventory_delete(identifier(code))

    def order_save(self, user, data, number=None):
        self.allow(user, 'admin', 'clerk', 'customer')
        items = data.get('items')
        if not isinstance(items, list) or not 1 <= len(items) <= 50:
            raise AppError('INPUT_INVALID', '订单需要一至五十条明细')
        clean = []
        for item in items:
            if not isinstance(item, dict):
                raise AppError('INPUT_INVALID', '订单明细格式不正确')
            clean.append({'product_code': identifier(text(item, 'product_code', 12)), 'quantity': integer(item, 'quantity', 1, 100)})
        new = number is None
        if new:
            number = 'WEB-'+uuid4().hex[:20]
        else:
            identifier(number, 24)
            self.visible_order(user, number)
        member = text(data, 'member_code', 12, required=False) or None
        if member:
            identifier(member)
        # Replacing a draft's lines refreshes its price quote from current menu prices.
        self.dao.order_save(user, number, json.dumps(clean), member, new)
        return {'order_no': number}

    def visible_order(self, user, number):
        self.allow(user, 'admin', 'clerk', 'customer')
        rows = self.dao.orders(user, identifier(number, 24))
        if not rows:
            raise AppError('NOT_FOUND', '订单不存在或不可访问', 404)
        return rows[0]

    def order_action(self, user, number, action):
        self.visible_order(user, number)
        if action == 'submit':
            self.allow(user, 'admin', 'clerk')
        self.dao.order_action(user, number, action)

    def sales(self, user):
        self.allow(user, 'admin', 'clerk')
        return self.dao.sales(user['Role'])
