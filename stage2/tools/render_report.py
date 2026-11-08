"""Render through the packaged render_docx.py using native Word PDF on Windows.
The Windows runtime does not bundle LibreOffice (runtime.json: null). Preserve the
canonical renderer's Poppler PNG pipeline, substituting only native DOCX->PDF.
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SKILL=Path(r'D:\codex\.codex\plugins\cache\openai-primary-runtime\documents\26.1105.12137\skills\documents')
PDF=ROOT/'阶段报告.pdf'
script=ROOT/'private'/'export-report.ps1'
script.write_text('''$ErrorActionPreference='Stop'
$word=New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
try {
 $report=$word.Documents.Open([string]$args[0],$false,$true)
 $report.Repaginate()
 $report.ExportAsFixedFormat([string]$args[1],17)
 $report.Close(0)
} finally {$word.Quit()}
''',encoding='utf-8-sig')
subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),str(ROOT/'阶段报告.docx'),str(PDF)],check=True,timeout=120)
spec=importlib.util.spec_from_file_location('packaged_render_docx',SKILL/'render_docx.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def native_pdf(doc_path,user_profile,convert_tmp_dir,stem,verbose=False):
    target=Path(convert_tmp_dir)/(stem+'.pdf');shutil.copy2(PDF,target)
    return str(target),'Native Microsoft Word PDF export; no bundled LibreOffice on Windows.'
module.convert_to_pdf=native_pdf
images=module.rasterize(str(ROOT/'阶段报告.docx'),str(ROOT/'private'/'report-qa'),150,False,False)
print('PASS packaged render_docx.py with native Word PDF backend:',len(images),'pages')
