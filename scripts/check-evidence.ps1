$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
function Assert-Hash([string]$RelativePath,[string]$Expected) {
    $actual=(Get-FileHash -LiteralPath (Join-Path $repoRoot $RelativePath) -Algorithm SHA256).Hash
    if ($actual -ne $Expected) { throw "Evidence hash mismatch: $RelativePath" }
}
$run=Get-Content -LiteralPath (Join-Path $repoRoot 'result/verification.json') -Raw | ConvertFrom-Json
if ($run.status -ne 'PASS' -or $run.steps.Count -ne 11) { throw 'Fresh replay did not complete all 11 steps.' }
Assert-Hash 'scripts/run-lab.ps1' $run.runnerSha256
foreach ($step in $run.steps) {
    if ($step.exitCode -ne 0) { throw "Nonzero exit code: $($step.script)" }
    Assert-Hash $step.script $step.sha256
    Assert-Hash "result/$($step.output)" $step.outputSha256
}
$images=@(Get-Content -LiteralPath (Join-Path $repoRoot 'result/screenshots/manifest.json') -Raw | ConvertFrom-Json)
foreach ($entry in $images) {
    Assert-Hash $entry.source $entry.sourceSha256
    Assert-Hash "result/screenshots/$($entry.image)" $entry.imageSha256
    if ($entry.executionStatus -ne '查询已成功执行。') { throw "SSMS execution failed: $($entry.image)" }
}
$files=@(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'result/screenshots') -Filter '*.png')
if ($files.Count -ne $images.Count) { throw 'A screenshot is missing from the manifest.' }
$extra=Get-Content -LiteralPath (Join-Path $repoRoot 'result/additional-verification.json') -Raw | ConvertFrom-Json
foreach ($entry in $extra) {
    if ($entry.status -ne 'PASS') { throw "Additional verification failed: $($entry.name)" }
    foreach ($artifact in $entry.artifacts) { Assert-Hash $artifact.path $artifact.sha256 }
}
Write-Host "PASS: 11 replay steps and $($images.Count) genuine SSMS screenshots match the current source/output hashes."
