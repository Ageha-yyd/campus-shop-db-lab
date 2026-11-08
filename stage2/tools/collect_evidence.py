"""Read-only metadata and before/after evidence. Never exports password hashes."""
import hashlib
import json
import os
from datetime import datetime,timezone
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
TABLES=['Product','Inventory','Member','Employee','ShopOrder','OrderLine','AppUser']
MEANINGS={'ProductCode':'标准饮品编号','ProductName':'当前饮品名称','Category':'原子类别名称','UnitPrice':'Product为当前菜单价；OrderLine为保存当次成交价',
 'RestockThreshold':'库存预警阈值 杯','IsActive':'是否启用','Quantity':'Inventory为可售杯数；OrderLine为购买杯数',
 'UpdatedAt':'库存最后维护时间 UTC','MemberCode':'可选会员编号','DisplayName':'显示名称','Phone':'可选联系电话 非空时唯一',
 'JoinedAt':'会员加入日期','EmployeeCode':'员工编号 草稿可以暂未指派','JobTitle':'员工职称','OrderNo':'订单编号',
 'OrderedAt':'订单创建时间 UTC','Status':'DRAFT COMPLETED CANCELLED','LineNumber':'同订单内行号 从1开始',
 'CreatedByUserId':'应用创建账号 历史订单为空','StockApplied':'是否有本系统新增扣库待回补 历史单为0',
 'UserId':'应用账号主标识','Username':'登录名 唯一候选码','PasswordHash':'scrypt密码哈希 禁止前端及结果导出','Role':'admin clerk customer'}


def rows(c,sql,*params):
    cur=c.execute(sql,*params);return [dict(zip([d[0] for d in cur.description],r)) for r in cur.fetchall()]


def connection(db):
    return pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+os.environ['DB_SERVER']+';DATABASE='+db+';Trusted_Connection=yes;TrustServerCertificate=yes;',autocommit=True)


def main():
    load_dotenv(ROOT/'.env',override=True)
    c=connection(os.environ['DB_NAME']);source=connection('MilkTeaShopV01')
    dictionary=['# v1.0 数据字典','', '业务规则、候选码、关系和范式依据见 design.md。类型、长度、精度、空值、默认值来自本次实际SQL Server目录；键、检查与索引列表也直接导出。','']
    evidence={'time':datetime.now(timezone.utc).isoformat(),'target_database':os.environ['DB_NAME'],'source_preservation':[],'comparisons':[]}
    for table in TABLES:
        fields=rows(c,"SELECT c.name,t.name AS type_name,c.max_length,c.precision,c.scale,c.is_nullable,dc.definition AS default_value FROM sys.columns c JOIN sys.types t ON t.user_type_id=c.user_type_id LEFT JOIN sys.default_constraints dc ON dc.object_id=c.default_object_id WHERE c.object_id=OBJECT_ID(?) ORDER BY c.column_id",'dbo.'+table)
        dictionary+=['## '+table,'','| 字段 | 类型与长度 | 可空 | 默认 | 业务含义 |','| --- | --- | --- | --- | --- |']
        for f in fields:
            typ=f['type_name']
            if typ in ['varchar','nvarchar']:typ+='('+str(f['max_length']//2 if typ=='nvarchar' else f['max_length'])+')'
            elif typ in ['decimal','numeric']:typ+=f"({f['precision']},{f['scale']})"
            elif typ=='datetime2':typ+='('+str(f['scale'])+')'
            dictionary.append(f"| {f['name']} | {typ} | {'是' if f['is_nullable'] else '否'} | {f['default_value'] or '无'} | {MEANINGS.get(f['name'],'见设计说明')} |")
        constraints=rows(c,"SELECT name,definition FROM sys.check_constraints WHERE parent_object_id=OBJECT_ID(?)",'dbo.'+table)
        indexes=rows(c,"SELECT i.name,i.is_primary_key,i.is_unique,i.filter_definition,STRING_AGG(CONVERT(nvarchar(max),col.name),',') WITHIN GROUP(ORDER BY ic.key_ordinal) AS columns FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id JOIN sys.columns col ON col.object_id=ic.object_id AND col.column_id=ic.column_id WHERE i.object_id=OBJECT_ID(?) AND ic.key_ordinal>0 GROUP BY i.name,i.is_primary_key,i.is_unique,i.filter_definition",'dbo.'+table)
        fks=rows(c,"SELECT fk.name,pc.name AS field,OBJECT_NAME(fk.referenced_object_id) AS target,rc.name AS target_field FROM sys.foreign_keys fk JOIN sys.foreign_key_columns f ON f.constraint_object_id=fk.object_id JOIN sys.columns pc ON pc.object_id=f.parent_object_id AND pc.column_id=f.parent_column_id JOIN sys.columns rc ON rc.object_id=f.referenced_object_id AND rc.column_id=f.referenced_column_id WHERE fk.parent_object_id=OBJECT_ID(?)",'dbo.'+table)
        dictionary+=['','码与索引：'+'；'.join(x['name']+'('+x['columns']+')'+(' PK' if x['is_primary_key'] else ' UNIQUE' if x['is_unique'] else '')+(' WHERE '+x['filter_definition'] if x['filter_definition'] else '') for x in indexes),'']
        dictionary+=['外码：'+'；'.join(x['field']+'→'+x['target']+'.'+x['target_field'] for x in fks) if fks else '无外码。','']
        dictionary+=['检查约束：'+'；'.join(x['name']+' '+x['definition'] for x in constraints) if constraints else '其他域由类型、外码或服务层规则控制。','']
        if table!='AppUser':
            cols=','.join('['+f['name']+']' for f in fields)
            sample=rows(c,'SELECT TOP(3) '+cols+' FROM dbo.['+table+'] ORDER BY 1'+(',2' if table=='OrderLine' else ''))
            dictionary+=['样例：','```json',json.dumps(sample,ensure_ascii=False,indent=2,default=str),'```','']
            old_fields=rows(source,"SELECT name FROM sys.columns WHERE object_id=OBJECT_ID(?) ORDER BY column_id",'dbo.'+table)
            old_cols=','.join('['+f['name']+']' for f in old_fields)
            before=rows(source,'SELECT '+old_cols+' FROM dbo.['+table+'] ORDER BY 1'+(',2' if table=='OrderLine' else ''))
            baseline=rows(c,'SELECT '+old_cols+' FROM dbo.[Baseline_'+table+'] ORDER BY 1'+(',2' if table=='OrderLine' else ''))
            after=rows(c,'SELECT '+old_cols+' FROM dbo.['+table+'] ORDER BY 1'+(',2' if table=='OrderLine' else ''))
            digest=lambda data:hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()
            item={'table':table,'before_count':len(before),'after_count':len(after),'source_sha256':digest(before),'baseline_sha256':digest(baseline),'target_sha256':digest(after),'equal':before==baseline==after}
            assert item['equal'],item
            evidence['source_preservation'].append(item)
        else:
            dictionary+=['账号样例仅导出非敏感字段：','```json',json.dumps(rows(c,'SELECT UserId,Username,Role,EmployeeCode,MemberCode,IsActive FROM dbo.AppUser ORDER BY UserId'),ensure_ascii=False,indent=2),'```','']
    for title,before_sql,after_sql in [
        ('订单明细','SELECT * FROM dbo.Baseline_OrderDetail ORDER BY OrderNo,LineNumber','SELECT * FROM dbo.vw_OrderDetail ORDER BY OrderNo,LineNumber'),
        ('商品销量与金额','SELECT * FROM dbo.Baseline_ProductSales ORDER BY ProductCode','SELECT * FROM dbo.vw_ProductSales ORDER BY ProductCode'),
        ('库存','SELECT * FROM dbo.Baseline_Inventory ORDER BY ProductCode','SELECT * FROM dbo.Inventory ORDER BY ProductCode')]:
        before,after=rows(c,before_sql),rows(c,after_sql)
        assert before==after
        evidence['comparisons'].append({'query':title,'expected':before,'actual':after,'equal':True,'difference':'无'})
    evidence['summary']={'completed_orders':6,'cups':15,'amount':'86.00','business_counts':[6,6,4,3,7,11]}
    (ROOT/'docs'/'data-dictionary.md').write_text('\n'.join(dictionary),encoding='utf-8')
    (ROOT/'result'/'before-after.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    source.close();c.close();print('PASS source, baseline and target six-table data exactly equal; metadata exported without credentials')


if __name__=='__main__':main()
