"""Build a classroom ZIP without local credentials, logs, venvs or QA intermediates."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED,ZipFile

REPO=Path(__file__).resolve().parents[2]
STAGE=REPO/'stage2'
NAME='奶茶店数据库_v1.0_袁远冬_陆乐天_罗金浩'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=REPO.parent/'提交包'/(NAME+'.zip'));a=p.parse_args()
    a.output.parent.mkdir(exist_ok=True,parents=True)
    files=[]
    for source in sorted(STAGE.rglob('*')):
        rel=source.relative_to(STAGE)
        if not source.is_file() or any(x in {'private','logs','__pycache__','.pytest_cache','.venv'} for x in rel.parts) or source.name=='.env':continue
        files.append((source,Path('stage2')/rel))
    for name in ['01_schema.sql','02_seed.sql','09_update_public_menu.sql','05_views.sql']:
        files.append((REPO/'sql'/name,Path('sql')/name))
    files.append((REPO/'启动第二阶段.bat',Path('启动第二阶段.bat')))
    manifest={str(rel).replace('\\','/'):hashlib.sha256(source.read_bytes()).hexdigest() for source,rel in files}
    readme='''# 校园奶茶店数据库应用 v1.0 第二阶段提交

成员：袁远冬、陆乐天、罗金浩。第五至第九周全部成果。

- [阶段报告 Word](stage2/阶段报告.docx)
- [阶段报告 PDF](stage2/阶段报告.pdf)
- [配置与复现步骤](stage2/README.md)
- [操作手册](stage2/docs/user-manual.md)
- [逐周要求与成果对应](stage2/docs/requirements-mapping.md)

本目录就是命令中的“仓库根目录”。先按stage2/README创建.venv、安装依赖和初始化SQL Server独立副本，再运行python -m stage2或双击启动第二阶段.bat。
sql/提供从空环境建立v0.1基线所需的四份脚本，stage2/sql/提供真正迁移、应用过程及回归；不需要父目录课件或原机私有文件。
登录密码在初始化时随机生成，保存在本机private目录；本包不包含.env、任何密码、数据库备份、详细本机日志或虚拟环境。
提交文件SHA256见SHA256.json。实际验收记录见stage2/result/，人工分工与AI记录见stage2/docs/。
'''
    with ZipFile(a.output,'w',ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr(NAME+'/README.md',readme)
        for source,rel in files:z.write(source,NAME+'/'+rel.as_posix())
        z.writestr(NAME+'/SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with ZipFile(a.output) as z:
        assert not z.testzip()
        for name in z.namelist():
            assert not any(x in name.split('/') for x in ['.env','private','logs','.venv','__pycache__'])
        assert len(manifest)==len(files)
    digest=hashlib.sha256(a.output.read_bytes()).hexdigest()
    a.output.with_suffix('.sha256').write_text(digest+'  '+a.output.name+'\n',encoding='utf-8')
    print('PASS '+str(a.output)+' files='+str(len(files))+' sha256='+digest)


if __name__=='__main__':main()
