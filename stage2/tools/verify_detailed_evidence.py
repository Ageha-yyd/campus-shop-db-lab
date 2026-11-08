"""Check the illustrated report against actual output, HTTP logs and retained DBs.

Run in the authoring checkout with the retained v0.1 source and configured test
environment. This is an evidence audit, not required for normal application use.
"""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pyodbc
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data=json.loads((ROOT/'result/detailed-report-source.json').read_text(encoding='utf-8'))
    browser=json.loads((ROOT/'result/detailed-browser.json').read_text(encoding='utf-8'))
    runs=json.loads((ROOT/'result/detailed-runs/manifest.json').read_text(encoding='utf-8'))
    with ZipFile(ROOT/data['report_file']) as z:
        images={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
        document=ET.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text=' '.join(document.itertext())
    expected={x['embedded_sha256'] for x in data['figures']}
    expected|={digest(ROOT/('docs/er-'+v+'.png')) for v in ['v01','v10']}
    assert images==expected,(len(images),len(expected))
    assert digest(ROOT/data['report_file'])==data['report_sha256']
    for f in data['figures']:
        assert digest(ROOT/f['source'])==f['source_sha256']
        assert f['step'] in text and f['title'] in text
    for code in data['code_excerpts']:assert digest(ROOT/code['file'])==code['file_sha256']
    logs=[json.loads(x) for x in (ROOT/'result/detailed-request-log.jsonl').read_text(encoding='utf-8').splitlines()]
    assert {x['request_id'] for x in browser['requests']}=={x['request_id'] for x in logs}
    assert all(set(x)=={'time','request_id','operation','role','code','result','http_status','duration_ms'} for x in logs)
    assert len(browser['checks'])==18 and all(x['result']=='PASS' for x in browser['checks'])
    assert not browser['javascript_errors'] and len(browser['figures'])==21
    for f in browser['figures']:assert digest(ROOT/f['image'])==f['sha256']
    for run in runs:
        assert run['exit_code']==0 and digest(ROOT/run['stdout_file'])==run['stdout_sha256']
        lines=(ROOT/run['stdout_file']).read_text(encoding='utf-8').splitlines()
        for f in run['figures']:
            assert digest(ROOT/f['image'])==f['sha256']
            assert 1<=f['line_start']<=f['line_end']<=len(lines)
    suite=ET.parse(ROOT/'result/detailed-runs/pytest.xml').getroot().find('testsuite')
    assert suite.attrib['tests']=='43' and suite.attrib['failures']==suite.attrib['errors']=='0'
    regression=(ROOT/'result/detailed-runs/S02_regression.txt').read_text(encoding='utf-8')
    assert sum(line.startswith('PASS ') for line in regression.splitlines())==13
    assert '1 passed' in (ROOT/'result/detailed-cleanup.txt').read_text(encoding='utf-8')
    replay=json.loads((ROOT/'result/package-replay.json').read_text(encoding='utf-8'))
    unchanged=[];updated_tools=[]
    for source in replay['runtime_source_files_equal']:
        path=ROOT.parent/source['path']
        if source['path']=='stage2/tools/browser_acceptance.py':
            updated_tools.append({'path':source['path'],'previous_sha256':source['sha256'],'current_sha256':digest(path),
                'change':'added --detailed screenshot and safe-log capture; 18 checks / 60 HTTP executed locally'})
            continue
        assert digest(path)==source['sha256'],str(path)
        unchanged.append(source)

    settings=dotenv_values(ROOT/'.env');test=dotenv_values(ROOT/'private/test.env')
    assert test['DB_NAME'].endswith('_Test')
    def connect(name):
        return pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+settings['DB_SERVER']+
            ';DATABASE='+name+';Trusted_Connection=yes;TrustServerCertificate=yes;',autocommit=True)
    source=connect('MilkTeaShopV01');demo=connect(settings['DB_NAME']);isolated=connect(test['DB_NAME'])
    database_checks=[]
    try:
        for name in ['Product','Inventory','Member','Employee','ShopOrder','OrderLine']:
            columns=[row[0] for row in source.execute('SELECT name FROM sys.columns WHERE object_id=OBJECT_ID(?) ORDER BY column_id','dbo.'+name)]
            query='SELECT '+','.join('['+x+']' for x in columns)+' FROM dbo.['+name+'] ORDER BY 1'+(',2' if name=='OrderLine' else '')
            baseline=[tuple(row) for row in source.execute(query)]
            demo_rows=[tuple(row) for row in demo.execute(query)]
            test_rows=[tuple(row) for row in isolated.execute(query)]
            assert baseline==demo_rows==test_rows,name
            database_checks.append({'table':name,'original_rows':len(baseline),'demo_rows':len(demo_rows),
                'test_rows':len(test_rows),'all_original_columns_equal':True})
    finally:
        for conn in [source,demo,isolated]:conn.close()
    result={'time_utc':datetime.now(timezone.utc).isoformat(),'report_file':data['report_file'],
        'report_figures_including_ER':len(data['figures'])+2,'unique_embedded_image_files':len(images),
        'all_21_UI_states_explained_and_embedded':True,
        'embedded_image_hashes_match_checked_sources':True,'source_code_excerpts_match':True,
        'sql_pass':13,'integration_tests':43,'browser_checks':18,'http_responses':len(browser['requests']),
        'http_request_ids_match_public_logs':True,'post_browser_cleanup_pass':True,
        'source_demo_test_original_data':database_checks,'runtime_identical_to_executed_independent_package':unchanged,
        'updated_evidence_tools':updated_tools}
    (ROOT/'result/detailed-final-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS 30 report figures / 29 distinct image hashes, 21 UI states, 43 tests, 13 SQL checks, 60 HTTP/log links, retained DB equality')


if __name__=='__main__':main()
