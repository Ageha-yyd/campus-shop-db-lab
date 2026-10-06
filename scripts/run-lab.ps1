param(
    [string]$ServerInstance = '.\SQLEXPRESS',
    [string]$SqlcmdPath = 'sqlcmd',
    [string]$OutputDirectory = ''
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $repoRoot 'result' }
$sqlcmdCommand = (Get-Command $SqlcmdPath -ErrorAction Stop).Source
$common = @('-S', $ServerInstance, '-E', '-C', '-f', '65001', '-b', '-W', '-w', '240')
# Refuse an existing database before touching stored evidence. Never drop user data.
$probe = & $sqlcmdCommand @common -h -1 -Q "SET NOCOUNT ON; SELECT CASE WHEN DB_ID(N'MilkTeaShopV01') IS NULL THEN 'ABSENT' ELSE 'EXISTS' END;"
if ($LASTEXITCODE -ne 0) { throw 'SQL Server preflight connection failed.' }
if (($probe -join '').Trim() -ne 'ABSENT') { throw 'MilkTeaShopV01 already exists. Preserve/rename it before a fresh replay; no evidence was overwritten.' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$manifestPath = Join-Path $OutputDirectory 'verification.json'
$manifest = [ordered]@{
    status = 'RUNNING'; database = 'MilkTeaShopV01'; startedUtc = [DateTime]::UtcNow.ToString('o')
    runnerSha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    connection = 'Windows integrated authentication; local certificate trusted for course lab'
    steps = @()
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$sequence = @('00_create_database','01_schema','02_seed','09_update_public_menu','03_crud','04_queries','05_views','06_constraints','07_roles','08_acceptance','10_database_overview')
foreach ($step in $sequence) {
    $source = Join-Path $repoRoot "sql/$step.sql"
    $destination = Join-Path $OutputDirectory "$step.txt"
    $database = if ($step -eq '00_create_database') { 'master' } else { 'MilkTeaShopV01' }
    & $sqlcmdCommand @common -d $database -i $source -o $destination
    $stepExitCode = $LASTEXITCODE
    # Keep evidence byte hashes stable when Git clones text files on Windows.
    $outputText = [IO.File]::ReadAllText($destination).Replace("`r`n", "`n")
    [IO.File]::WriteAllText($destination, $outputText, [Text.UTF8Encoding]::new($false))
    $manifest.steps += [ordered]@{
        script = "sql/$step.sql"; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        output = "$step.txt"; outputSha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
        exitCode = $stepExitCode; completedUtc = [DateTime]::UtcNow.ToString('o')
    }
    if ($stepExitCode -ne 0) {
        $manifest.status = 'FAILED'
        $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
        throw "Replay stopped at $step (exit $stepExitCode). See $destination."
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Write-Host "$step : PASS"
}
$manifest.status = 'PASS'
$manifest.finishedUtc = [DateTime]::UtcNow.ToString('o')
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Host 'PASS: fresh database replay completed; script and output hashes recorded.'
