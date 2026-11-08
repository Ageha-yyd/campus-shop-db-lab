"""Developer-only: deploy procedure/view changes to explicit stage2 DBs, no source DB writes."""
import argparse
from pathlib import Path
import pyodbc
from .setup import execute_script, ident

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('database');args=p.parse_args()
    ident(args.database)
    if not args.database.startswith('MilkTeaShopV10_'):
        raise SystemExit('Stage2 database required')
    c=pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE='+args.database+';Trusted_Connection=yes;TrustServerCertificate=yes;',autocommit=True)
    source=Path(__file__).resolve().parents[1]/'sql'/'application.sql'
    # Existing grants remain. Reapply only procedures/views before CREATE ROLE.
    import re
    for batch in re.split(r'^\s*GO\s*$',source.read_text(encoding='utf-8'),flags=re.M|re.I):
        if 'CREATE ROLE web_auth' in batch:break
        if batch.strip():
            cur=c.execute(batch)
            while cur.nextset():pass
    c.close();print('PASS procedure/view update '+args.database)
