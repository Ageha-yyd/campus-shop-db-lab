"""Execute real SQL/pytest, then photograph explicitly labelled output viewers.

The output screenshots are not SSMS/terminal screenshots. Each viewer presents
verbatim subprocess stdout, its exact command, exit code, time and SHA256.
Browser business-flow evidence is captured separately by browser_acceptance.
"""
import hashlib
import html
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
OUT=ROOT/'result'/'detailed-runs'
SHOTS=ROOT/'result'/'detailed-screenshots'
PRIVATE=ROOT/'private'/'detailed-viewers'


def main():
    for folder in [OUT,SHOTS,PRIVATE]:folder.mkdir(parents=True,exist_ok=True)
    env=dotenv_values(ROOT/'private/test.env')
    if not env['DB_NAME'].endswith('_Test'):raise RuntimeError('Explicit isolated test DB required')
    base=['sqlcmd','-S',env['DB_SERVER'],'-d',env['DB_NAME'],'-E','-C','-b','-f','65001','-W','-w','180']
    verification=ROOT/'sql/report_verification.sql'
    jobs=[('T01_pytest','真实SQL Server集成测试',
           [sys.executable,'-m','pytest','stage2/tests','-v','--junitxml=stage2/result/detailed-runs/pytest.xml']),
          ('S01_baseline','SQL基线和业务数值核验',base+['-i',str(verification)]),
          ('S02_regression','迁移与权限SQL回归',base+['-i',str(ROOT/'sql/regression.sql')]),
          ('S03_normalization','规范化异常和分解演示',base+['-i',str(ROOT/'sql/normalization_demo.sql')])]
    runs=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1480,'height':1100},device_scale_factor=1)
        for key,title,command in jobs:
            start=datetime.now(timezone.utc).isoformat()
            result=subprocess.run(command,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
            output=result.stdout.decode('utf-8',errors='strict').replace('\r\n','\n')
            target=OUT/(key+'.txt');target.write_text(output,encoding='utf-8',newline='\n')
            entry={'step':key,'title':title,'database':env['DB_NAME'],'command':command,'started_utc':start,
                   'ended_utc':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,
                   'stdout_file':target.relative_to(ROOT).as_posix(),'stdout_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'figures':[]}
            if result.returncode:raise RuntimeError(f'{key} failed; inspect {target}')
            # Paginate verbatim output, never retype or synthesize test results.
            lines=output.splitlines();chunks=[lines[i:i+18] for i in range(0,len(lines),18)]
            for i,chunk in enumerate(chunks,1):
                source=PRIVATE/f'{key}-{i}.html'
                command_text=subprocess.list2cmdline(command)
                source.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:36px;color:#17232b;background:white;font:20px "Microsoft YaHei"}h1{font-size:28px}p{font-size:16px;overflow-wrap:anywhere}pre{font:19px/1.65 Consolas,"Microsoft YaHei",monospace;white-space:pre-wrap;overflow-wrap:anywhere;border-top:1px solid #ccc;padding-top:18px}footer{font-size:15px;color:#45545d}</style>'
                    +f'<h1>{html.escape(title)} 实际输出 {i}/{len(chunks)}</h1><p>这是执行输出的只读核验页，非SSMS或终端原生界面。原文逐行保留。</p>'
                    +f'<p>数据库 {html.escape(env["DB_NAME"])}　退出码 {result.returncode}　执行开始 UTC {start}</p>'
                    +f'<p>执行命令 {html.escape(command_text)}</p><pre>{html.escape(chr(10).join(chunk))}</pre>'
                    +f'<footer>原始输出 {entry["stdout_file"]}　SHA256 {entry["stdout_sha256"]}<br>本页为原输出第 {(i-1)*18+1} 至 {min(i*18,len(lines))} 行</footer>',encoding='utf-8')
                page.goto(source.as_uri());page.evaluate('document.fonts.ready')
                shot=SHOTS/f'{key}-{i}.png';page.screenshot(path=str(shot),full_page=True)
                entry['figures'].append({'image':shot.relative_to(ROOT).as_posix(),'line_start':(i-1)*18+1,
                    'line_end':min(i*18,len(lines)),'sha256':hashlib.sha256(shot.read_bytes()).hexdigest()})
            runs.append(entry)
        browser.close()
    (OUT/'manifest.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS actual execution and labelled screenshots:',len(runs),'commands,',sum(len(x['figures']) for x in runs),'screenshots')


if __name__=='__main__':main()
