param(
    [string]$OutputPath = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) '提交包/奶茶店数据库_v0.1_袁远冬_陆乐天_罗金浩.zip')
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$required = @('README.md','提交验收清单.md','docs/stage-report.md','docs/ai_log.md','docs/contribution.md','deliverables/v0.1/阶段报告.docx','deliverables/v0.1/阶段报告.pdf','result/submission-verification.json')
foreach ($item in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $item) -PathType Leaf)) { throw "Missing submission file: $item" }
}
& (Join-Path $PSScriptRoot 'check-evidence.ps1')
$tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$stage = Join-Path $tempBase ('milk-tea-submission-' + [guid]::NewGuid().ToString('N'))
$root = Join-Path $stage '奶茶店数据库_v0.1'
try {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    foreach ($directory in @('sql','scripts','data','docs','result','deliverables')) {
        Copy-Item -LiteralPath (Join-Path $repoRoot $directory) -Destination $root -Recurse
    }
    foreach ($file in @('README.md','提交验收清单.md')) {
        Copy-Item -LiteralPath (Join-Path $repoRoot $file) -Destination $root
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
    $commit = $null
    $dirty = $null
    if ((Test-Path -LiteralPath (Join-Path $repoRoot '.git')) -and (Get-Command git -ErrorAction SilentlyContinue)) {
        $commit = (& git -C $repoRoot rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Cannot determine source commit.' }
        $dirty = @(& git -C $repoRoot status --porcelain).Count -gt 0
    } elseif (Test-Path -LiteralPath (Join-Path $repoRoot 'package-manifest.json')) {
        $commit = (Get-Content -LiteralPath (Join-Path $repoRoot 'package-manifest.json') -Raw | ConvertFrom-Json).sourceCommit
    }
    [ordered]@{
        title = '奶茶店数据库 v0.1'
        members = @('袁远冬','陆乐天','罗金浩')
        sourceCommit = $commit
        sourceHasUncommittedChanges = $dirty
        createdUtc = [DateTime]::UtcNow.ToString('o')
        manifestExcludesItself = $true
        fileCount = $files.Count
        files = $files
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'package-manifest.json') -Encoding utf8NoBOM
    $target = [IO.Path]::GetFullPath($OutputPath)
    New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
    $newArchive = Join-Path $stage 'submission.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($root, $newArchive, [IO.Compression.CompressionLevel]::Optimal, $true)
    Move-Item -LiteralPath $newArchive -Destination $target -Force
    Write-Host "Created: $target"
    Write-Host "Files: $($files.Count + 1); SHA256: $((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash)"
} finally {
    $resolvedStage = [IO.Path]::GetFullPath($stage)
    if (-not $resolvedStage.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolvedStage -Leaf) -notlike 'milk-tea-submission-*') { throw 'Unexpected staging directory.' }
    if (Test-Path -LiteralPath $resolvedStage) { Remove-Item -LiteralPath $resolvedStage -Recurse -Force }
}
