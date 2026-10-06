param(
    [string]$OutputPath = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) '提交包/奶茶店数据库_v0.1_袁远冬_陆乐天_罗金浩.zip')
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$required = @('README.md','docs/data-dictionary.md','docs/ai_log.md','docs/contribution.md','阶段报告.docx','阶段报告.pdf','复现.ps1')
foreach ($item in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $item) -PathType Leaf)) { throw "Missing submission file: $item" }
}
& (Join-Path $PSScriptRoot 'check-evidence.ps1')
$tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$stage = Join-Path $tempBase ('milk-tea-submission-' + [guid]::NewGuid().ToString('N'))
$root = Join-Path $stage '奶茶店数据库_v0.1'
try {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    foreach ($directory in @('sql','result','result/screenshots')) {
        New-Item -ItemType Directory -Path (Join-Path $root $directory) -Force | Out-Null
    }
    $sqlNames = @('00_create_database','01_schema','02_seed','03_crud','04_queries','05_views','06_constraints','07_roles','08_acceptance','09_update_public_menu','10_database_overview','11_reporting_evidence')
    foreach ($name in $sqlNames) {
        Copy-Item -LiteralPath (Join-Path $repoRoot "sql/$name.sql") -Destination (Join-Path $root "sql/$name.sql")
        $logName = if ($name -eq '11_reporting_evidence') { '12_reporting_evidence' } else { $name }
        Copy-Item -LiteralPath (Join-Path $repoRoot "result/$logName.txt") -Destination (Join-Path $root "result/$logName.txt")
    }
    $images = @(Get-Content -LiteralPath (Join-Path $repoRoot 'result/screenshots/manifest.json') -Raw | ConvertFrom-Json)
    foreach ($entry in $images) {
        Copy-Item -LiteralPath (Join-Path $repoRoot "result/screenshots/$($entry.image)") -Destination (Join-Path $root "result/screenshots/$($entry.image)")
    }
    foreach ($file in @('阶段报告.docx','阶段报告.pdf','复现.ps1')) {
        Copy-Item -LiteralPath (Join-Path $repoRoot $file) -Destination $root
    }
    $readme = Get-Content -LiteralPath (Join-Path $repoRoot 'README.md') -Raw
    $readme = ($readme -split '## 仓库补充资料')[0].TrimEnd()
    $readme = $readme.Replace('docs/data-dictionary.md','数据字典.md').Replace('docs/ai_log.md','ai_log.md').Replace('docs/contribution.md','组内分工.md')
    [IO.File]::WriteAllText((Join-Path $root 'README.md'),$readme+"`n",[Text.UTF8Encoding]::new($false))
    $dictionary = (Get-Content -LiteralPath (Join-Path $repoRoot 'docs/data-dictionary.md') -Raw).Replace('../sql/','sql/').Replace('；菜单参考和样例安排见 [数据说明](data-sources.md)。','。')
    [IO.File]::WriteAllText((Join-Path $root '数据字典.md'),$dictionary,[Text.UTF8Encoding]::new($false))
    $ai = (Get-Content -LiteralPath (Join-Path $repoRoot 'docs/ai_log.md') -Raw).Replace('(contribution.md)','(组内分工.md)').Replace('result/submission-verification.json','result/复现记录.txt')
    [IO.File]::WriteAllText((Join-Path $root 'ai_log.md'),$ai,[Text.UTF8Encoding]::new($false))
    $division = (Get-Content -LiteralPath (Join-Path $repoRoot 'docs/contribution.md') -Raw) -replace '\r?\n组内材料的整合过程见.*',''
    $division = $division.Replace('`requirements.md`','阶段报告第一部分').Replace('`data-dictionary.md`','`数据字典.md`').Replace('复现脚本','`复现.ps1`').Replace('`stage-report.md`','阶段报告').Replace('`evidence-checklist.md`','`result/README.md`')
    [IO.File]::WriteAllText((Join-Path $root '组内分工.md'),$division,[Text.UTF8Encoding]::new($false))
    $legend = (Get-Content -LiteralPath (Join-Path $repoRoot 'docs/evidence-checklist.md') -Raw) -split '## 真实SSMS截图'
    $legend = ($legend[1] -split '截图manifest')[0].Trim().Replace('../result/screenshots/','screenshots/')
    $legend = "# 结果说明`n`n本目录包含15张SSMS截图及12份完整SQLCMD输出。截图在screenshots目录；同编号txt记录完整结果，补充SQL11的文本为12_reporting_evidence.txt。复现脚本执行后新增复现记录.txt。`n`n" + $legend + "`n`n截图来自实际SSMS执行；未显示的行可查完整文本输出。`n"
    [IO.File]::WriteAllText((Join-Path $root 'result/README.md'),$legend,[Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath (Join-Path $repoRoot 'result/复现记录.txt')) {
        Copy-Item -LiteralPath (Join-Path $repoRoot 'result/复现记录.txt') -Destination (Join-Path $root 'result/复现记录.txt')
    }
    $forbidden = @(Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Extension -in @('.bak','.mdf','.ldf','.tmp') -or $_.FullName -match '[\\/]\.git[\\/]' })
    if ($forbidden.Count -gt 0) { throw 'Database files, backups, temporary files or Git internals must not enter the submission.' }
    $files = @(Get-ChildItem -LiteralPath $root -File -Recurse | Sort-Object FullName | ForEach-Object {
        [ordered]@{
            path = [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\','/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    })
    if (@($files | Where-Object { $_.path -like '*.json' }).Count -gt 0) { throw 'Technical JSON records must not enter the course submission.' }
    $target = [IO.Path]::GetFullPath($OutputPath)
    New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
    $newArchive = Join-Path $stage 'submission.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($root, $newArchive, [IO.Compression.CompressionLevel]::Optimal, $true)
    Move-Item -LiteralPath $newArchive -Destination $target -Force
    Write-Host "Created: $target"
    Write-Host "Files: $($files.Count); JSON: 0; SHA256: $((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash)"
} finally {
    $resolvedStage = [IO.Path]::GetFullPath($stage)
    if (-not $resolvedStage.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolvedStage -Leaf) -notlike 'milk-tea-submission-*') { throw 'Unexpected staging directory.' }
    if (Test-Path -LiteralPath $resolvedStage) { Remove-Item -LiteralPath $resolvedStage -Recurse -Force }
}
