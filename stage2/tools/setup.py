"""Create a new v0.1 database copy, migrate atomically and provision application roles.
Default source is the existing, preserved MilkTeaShopV01. --from-scripts builds a
fresh isolated v0.1 fixture from the repository, for clean-environment reproduction.
Never drops, renames or overwrites a database. Passwords are local only.
"""
import argparse
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

import pyodbc
from werkzeug.security import generate_password_hash
pyodbc.pooling = False

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'stage2'


def ident(name):
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,100}',name):
        raise ValueError('Invalid database name')
    return '['+name+']'


def literal(value):
    # Administrative DDL does not accept parameter markers for identifiers/paths.
    # These values are generated internally, never from HTTP inputs.
    return "N'"+str(value).replace("'","''")+"'"


def execute_script(conn, path):
    for batch in re.split(r'^\s*GO\s*$',path.read_text(encoding='utf-8-sig'), flags=re.M|re.I):
        if batch.strip():
            cur = conn.execute(batch)
            while True:
                if cur.description:
                    cur.fetchall()
                if not cur.nextset():
                    break


def execute_admin(conn, sql):
    cur = conn.execute(sql)
    while cur.nextset():
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server',default=r'.\SQLEXPRESS')
    parser.add_argument('--source',default='MilkTeaShopV01')
    parser.add_argument('--database',default='MilkTeaShopV10')
    parser.add_argument('--from-scripts',action='store_true')
    parser.add_argument('--env-file',type=Path,default=STAGE/'.env')
    parser.add_argument('--result-dir',type=Path,default=STAGE/'result')
    args = parser.parse_args()
    source,target = ident(args.source),ident(args.database)
    if args.env_file.exists():
        raise SystemExit('Refusing to overwrite local credentials; select a new --env-file.')
    base = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={args.server};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;'
    master = pyodbc.connect(base+'DATABASE=master;',autocommit=True)
    if master.execute('SELECT DB_ID(?)',args.database).fetchval() is not None:
        raise SystemExit('Target already exists; select a new --database. No files/data overwritten.')
    args.result_dir.mkdir(parents=True,exist_ok=True)
    private = STAGE/'private'
    private.mkdir(exist_ok=True)
    manifest = {'time':datetime.now(timezone.utc).isoformat(),'source':args.source if not args.from_scripts else 'repository v0.1 SQL','target':args.database}
    if args.from_scripts:
        master.execute('CREATE DATABASE '+target)
        db = pyodbc.connect(base+'DATABASE='+args.database,autocommit=True)
        for name in ['01_schema.sql','02_seed.sql','09_update_public_menu.sql','05_views.sql']:
            execute_script(db,ROOT/'sql'/name)
        db.close()
    else:
        # Backup in SQL Server's own writable directory; unique name prevents overwrite.
        backup_dir = master.execute("SELECT CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultBackupPath'))").fetchval()
        backup = str(Path(backup_dir)/('Stage2_'+secrets.token_hex(6)+'.bak'))
        execute_admin(master,'BACKUP DATABASE '+source+' TO DISK='+literal(backup)+' WITH COPY_ONLY,CHECKSUM')
        cur=master.execute('RESTORE FILELISTONLY FROM DISK='+literal(backup))
        files=[dict(zip([d[0] for d in cur.description],r)) for r in cur.fetchall()]
        while cur.nextset():
            pass
        data_dir=master.execute("SELECT CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultDataPath'))").fetchval()
        log_dir=master.execute("SELECT CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultLogPath'))").fetchval()
        moves=[]
        for i,f in enumerate(files):
            dest=str(Path(log_dir if f['Type']=='L' else data_dir)/(args.database+'_'+str(i)+('_log.ldf' if f['Type']=='L' else '.mdf')))
            moves.append('MOVE '+literal(f['LogicalName'])+' TO '+literal(dest))
        execute_admin(master,'RESTORE DATABASE '+target+' FROM DISK='+literal(backup)+' WITH '+','.join(moves)+',CHECKSUM')
        manifest['backup_retained']=True
    db=pyodbc.connect(base+'DATABASE='+args.database,autocommit=True)
    execute_script(db,STAGE/'sql'/'migration.sql')
    execute_script(db,STAGE/'sql'/'application.sql')
    db.close()
    # Application roles work under Windows-only authentication, without server changes.
    # Bootstrap connection is immediately restricted via sp_setapprole by the DAO.
    db=pyodbc.connect(base+'DATABASE='+args.database,autocommit=True)
    env=['DB_SERVER='+args.server,'DB_NAME='+args.database,'DB_DRIVER=ODBC Driver 18 for SQL Server','FLASK_SECRET_KEY='+secrets.token_hex(32)]
    accounts={}
    for role in ['auth','admin','clerk','customer']:
        password=secrets.token_urlsafe(32)+'aA1!'
        db.execute('CREATE APPLICATION ROLE [mt_'+role+'] WITH PASSWORD='+literal(password))
        grants=db.execute("SELECT p.permission_name,OBJECT_NAME(p.major_id) FROM sys.database_permissions p JOIN sys.database_principals r ON r.principal_id=p.grantee_principal_id WHERE r.name=? AND p.class=1 AND p.state='G'",'web_'+role).fetchall()
        for permission,obj in grants:
            db.execute('GRANT '+permission+' ON dbo.'+ident(obj)+' TO [mt_'+role+']')
        env.append('DB_PASSWORD_'+role.upper()+'='+password)
    for username,role,employee,member in [('admin','admin','E003',None),('clerk','clerk','E001',None),('customer','customer',None,'M001'),('guest','customer',None,None)]:
        password=secrets.token_urlsafe(12)
        db.execute('INSERT dbo.AppUser(Username,PasswordHash,Role,EmployeeCode,MemberCode) VALUES(?,?,?,?,?)',username,generate_password_hash(password),role,employee,member)
        accounts[username]=password
    args.env_file.parent.mkdir(parents=True,exist_ok=True)
    args.env_file.write_text('\n'.join(env)+'\n',encoding='utf-8')
    credential_path=args.env_file.with_name(args.env_file.name+'.accounts.json')
    # Credentials always under ignored local private directory, even for replay runs.
    credential_path=private/(args.database+'_accounts.json')
    credential_path.write_text(json.dumps(accounts,indent=2),encoding='utf-8')
    manifest.update({'database_security':'password-protected application roles; no role cookie or pooling','windows_auth_mode_unchanged':True,
        'migration_sha256':hashlib.sha256((STAGE/'sql'/'migration.sql').read_bytes()).hexdigest(),
        'business_counts':{t:db.execute('SELECT COUNT(*) FROM dbo.'+ident(t)).fetchval() for t in ['Product','Inventory','Member','Employee','ShopOrder','OrderLine']}})
    (args.result_dir/'setup.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    db.close(); master.close()
    print('PASS isolated copy and migration; credentials saved locally in stage2/private/'+credential_path.name)


if __name__=='__main__':
    main()
