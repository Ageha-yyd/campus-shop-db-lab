import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pyodbc
from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

from .dao import DAO, connection_strings
from .errors import AppError
from .service import Service

ROOT = Path(__file__).resolve().parents[1]


def create_app(config=None):
    load_dotenv(ROOT / '.env')
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('FLASK_SECRET_KEY'), DB_CONNECTIONS=connection_strings(),
                      DB_ROLE_PASSWORDS={r:os.environ['DB_PASSWORD_'+r.upper()] for r in ['auth','admin','clerk','customer']},
                      MAX_CONTENT_LENGTH=32768, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      PERMANENT_SESSION_LIFETIME=1800)
    if config:
        app.config.update(config)
    if not app.secret_key:
        raise RuntimeError('Run setup to create local configuration first.')
    dao = DAO(app.config)
    service = Service(dao)
    app.extensions['dao'], app.extensions['service'] = dao, service
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    logger = logging.getLogger('milktea.'+uuid4().hex)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(logs / 'app.jsonl', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

    def ok(data=None):
        return jsonify(ok=True, code='OK', message='操作成功', data=data, request_id=g.request_id)

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise AppError('INPUT_INVALID', '请提交正确的表单数据')
        return data

    @app.before_request
    def before():
        g.request_id, g.started, g.user, g.code = uuid4().hex, time.monotonic(), None, 'OK'
        if request.path.startswith('/api/'):
            if session.get('username'):
                g.user = dao.user(session['username'])
            if request.method not in {'GET','HEAD','OPTIONS'}:
                token = request.headers.get('X-CSRF-Token','')
                if not session.get('csrf') or not secrets.compare_digest(token, session['csrf']):
                    raise AppError('CSRF_INVALID', '页面已过期 请刷新后重试', 403)
            if request.path not in {'/api/session','/api/login'}:
                service.allow(g.user, 'admin','clerk','customer')

    @app.after_request
    def after(response):
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'"
        logger.info(json.dumps({'time':datetime.now(timezone.utc).isoformat(), 'request_id':g.request_id,
            'operation':request.method+' '+request.url_rule.rule if request.url_rule else request.method+' unknown',
            'role':g.user['Role'] if g.user else 'anonymous','code':g.code,
            'result':'success' if response.status_code<400 else 'failure','http_status':response.status_code,
            'duration_ms':round((time.monotonic()-g.started)*1000)},ensure_ascii=False))
        return response

    @app.errorhandler(Exception)
    def handle(exc):
        if isinstance(exc, AppError):
            code, message, status = exc.code, exc.message, exc.status
        elif isinstance(exc, pyodbc.Error):
            detail = str(exc)
            if '51103' in detail:
                code,message,status = 'FORBIDDEN','您没有此操作权限',403
            elif '51104' in detail:
                code,message,status = 'NOT_FOUND','订单不存在或不可访问',404
            elif any(x in detail for x in ['51101','51106']):
                code,message,status = 'BUSINESS_RULE','请检查订单状态 商品和库存后重试',409
            elif exc.args and str(exc.args[0]).startswith('23'):
                code,message,status = 'CONSTRAINT_CONFLICT','记录重复或已被引用 请检查后重试',409
            elif exc.args and str(exc.args[0]).startswith(('08','HYT','28000')):
                code,message,status = 'DB_UNAVAILABLE','系统暂时无法连接 请稍后重试',503
            else:
                code,message,status = 'TRANSACTION_FAILED','操作未完成 数据已回滚 请稍后重试',503
        elif isinstance(exc, HTTPException):
            code,message,status = 'INPUT_INVALID','请求无效 请检查后重试',exc.code
        else:
            code,message,status = 'INTERNAL_ERROR','系统暂时无法完成操作',500
        # Detailed exceptions are server-only. Never log request bodies/passwords.
        logger.error(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'request_id':g.request_id,
            'operation':request.method+' '+(request.url_rule.rule if request.url_rule else 'unknown'),
            'role':g.user['Role'] if g.user else 'anonymous','code':code,'result':'failure',
            'exception_type':type(exc).__name__,'detail':str(exc)},ensure_ascii=False))
        g.code = code
        return jsonify(ok=False,code=code,message=message,data=None,request_id=g.request_id),status

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/api/session')
    def session_info():
        session.setdefault('csrf', secrets.token_urlsafe(32))
        user = {key:g.user[key] for key in ['Username','Role']} if g.user else None
        return ok({'user':user,'csrf':session['csrf']})

    @app.post('/api/login')
    def login():
        user = service.login(body())
        session.clear()
        session.update(username=user['Username'],csrf=secrets.token_urlsafe(32),permanent=True)
        g.user = user
        return ok({'user':{'Username':user['Username'],'Role':user['Role']},'csrf':session['csrf']})

    @app.post('/api/logout')
    def logout():
        session.clear()
        return ok()

    @app.get('/api/products')
    def products():
        search = request.args.get('q','')
        return ok(service.products(g.user,search))

    @app.post('/api/products')
    def product_add():
        return ok(service.product_save(g.user,body()))

    @app.put('/api/products/<code>')
    def product_update(code):
        return ok(service.product_save(g.user,body(),code))

    @app.delete('/api/products/<code>')
    def product_delete(code):
        service.product_delete(g.user,code)
        return ok()

    @app.get('/api/inventory')
    def inventory():
        return ok(service.inventory(g.user))

    @app.put('/api/inventory/<code>')
    def inventory_save(code):
        service.inventory_save(g.user,code,body())
        return ok()

    @app.delete('/api/inventory/<code>')
    def inventory_delete(code):
        service.inventory_delete(g.user,code)
        return ok()

    @app.get('/api/orders')
    def orders():
        return ok(service.orders(g.user))

    @app.post('/api/orders')
    def order_add():
        return ok(service.order_save(g.user,body()))

    @app.get('/api/orders/<number>')
    def order_detail(number):
        return ok(service.detail(g.user,number))

    @app.put('/api/orders/<number>')
    def order_update(number):
        return ok(service.order_save(g.user,body(),number))

    @app.delete('/api/orders/<number>')
    def order_delete(number):
        service.order_action(g.user,number,'delete')
        return ok()

    @app.post('/api/orders/<number>/<action>')
    def order_action(number,action):
        if action not in {'submit','cancel'}:
            raise AppError('INPUT_INVALID','操作不正确')
        service.order_action(g.user,number,action)
        return ok()

    @app.get('/api/sales')
    def sales():
        return ok(service.sales(g.user))

    return app
