param(
    [string]$ServerInstance = '.\SQLEXPRESS',
    [string]$SqlcmdPath = 'sqlcmd'
)
$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$command = (Get-Command $SqlcmdPath -ErrorAction Stop).Source
$common = @('-S',$ServerInstance,'-E','-C','-f','65001','-b','-W','-w','240')
$probe = & $command @common -h -1 -Q "SET NOCOUNT ON; SELECT CASE WHEN DB_ID(N'MilkTeaShopV01') IS NULL THEN 'ABSENT' ELSE 'EXISTS' END;"
if ($LASTEXITCODE -ne 0) { throw 'SQL Server connection failed.' }
if (($probe -join '').Trim() -ne 'ABSENT') { throw 'MilkTeaShopV01 already exists. Preserve/rename it before replay. No data or evidence was changed.' }
$result = Join-Path $repoRoot 'result'
New-Item -ItemType Directory -Path $result -Force | Out-Null
$sequence = @('00_create_database','01_schema','02_seed','09_update_public_menu','03_crud','04_queries','05_views','06_constraints','07_roles','08_acceptance','10_database_overview')
foreach ($step in $sequence) {
    $database = if ($step -eq '00_create_database') { 'master' } else { 'MilkTeaShopV01' }
    $destination = Join-Path $result "$step.txt"
    & $command @common -d $database -i (Join-Path $repoRoot "sql/$step.sql") -o $destination
    if ($LASTEXITCODE -ne 0) { throw "Failed at $step. See $destination" }
    $content = [IO.File]::ReadAllText($destination).Replace("`r`n","`n")
    [IO.File]::WriteAllText($destination,$content,[Text.UTF8Encoding]::new($false))
    Write-Host "$step : PASS"
}
$record = @("Replay: PASS (11 steps)","Finished UTC: $([DateTime]::UtcNow.ToString('o'))",'Connection: Windows integrated authentication','Database: MilkTeaShopV01','Expected: 6 tables, 4 views; row counts 6/6/4/3/7/11; completed revenue 86.00','Detailed acceptance: result/08_acceptance.txt')
[IO.File]::WriteAllText((Join-Path $result '复现记录.txt'),($record -join "`n")+"`n",[Text.UTF8Encoding]::new($false))
Write-Host 'PASS: all 11 steps completed. Read result/08_acceptance.txt for baseline and boundary checks.'
