param(
    [Parameter(Mandatory)][string]$SqlFile,
    [Parameter(Mandatory)][string]$ImageName,
    [Parameter(Mandatory)][string]$SsmsPath,
    [string]$ServerInstance = '.\SQLEXPRESS',
    [string]$Database = 'MilkTeaShopV01',
    [switch]$ScrollResults
)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
$source=(Resolve-Path (Join-Path $repoRoot $SqlFile)).Path
$destination=Join-Path $repoRoot "result/screenshots/$ImageName"
if ([IO.Path]::GetFileName($ImageName) -ne $ImageName) { throw 'ImageName must be a filename.' }
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing
if (-not ('LabWindowCapture' -as [type])) {
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class LabWindowCapture {
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint f);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
}
'@
}
# SSMS must be visible to collect genuine interactive query results.
$process=Start-Process -FilePath $SsmsPath -ArgumentList @($source,'-S',$ServerInstance,'-d',$Database,'-C','-nosplash') -PassThru
$loaded=$null
for ($i=0;$i -lt 60;$i++) {
    Start-Sleep -Milliseconds 500
    $loaded=Get-Process -Id $process.Id -ErrorAction SilentlyContinue
    if ($loaded -and $loaded.MainWindowTitle -match [regex]::Escape([IO.Path]::GetFileName($source))) { break }
}
if (-not $loaded -or $loaded.MainWindowTitle -notmatch [regex]::Escape([IO.Path]::GetFileName($source))) { throw 'SSMS query window did not load.' }
$root=[System.Windows.Automation.AutomationElement]::FromHandle($loaded.MainWindowHandle)
$nodes=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$execute=$nodes | Where-Object { $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '执行' } | Select-Object -First 1
if (-not $execute -or -not $execute.Current.IsEnabled) { throw 'SSMS Execute is unavailable.' }
$invoke=$null
[void]$execute.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)
$invoke.Invoke()
$success=$false
for ($i=0;$i -lt 30;$i++) {
    Start-Sleep -Milliseconds 500
    $nodes=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    if (@($nodes | Where-Object { $_.Current.Name -eq '查询执行失败。' }).Count) { throw 'SSMS query execution failed; inspect the open window.' }
    if (@($nodes | Where-Object { $_.Current.Name -eq '查询已成功执行。' }).Count) { $success=$true; break }
}
if (-not $success) { throw 'SSMS did not report successful completion.' }
Start-Sleep -Seconds 1
if ($ScrollResults) {
    for ($i=0;$i -lt 16;$i++) {
        [void][LabWindowCapture]::PostMessage($loaded.MainWindowHandle,0x020A,[IntPtr](-7864320),[IntPtr]((1000 -shl 16) -bor 1000))
        Start-Sleep -Milliseconds 100
    }
    Start-Sleep -Seconds 1
}
$rect=New-Object LabWindowCapture+RECT
[void][LabWindowCapture]::GetWindowRect($loaded.MainWindowHandle,[ref]$rect)
$width=$rect.Right-$rect.Left; $height=$rect.Bottom-$rect.Top
$bitmap=[System.Drawing.Bitmap]::new($width,$height)
$graphics=[System.Drawing.Graphics]::FromImage($bitmap)
$dc=$graphics.GetHdc()
$ok=[LabWindowCapture]::PrintWindow($loaded.MainWindowHandle,$dc,2)
$graphics.ReleaseHdc($dc)
if (-not $ok) { throw 'SSMS PrintWindow capture failed.' }
# Use the actual query status row as the bottom boundary, excluding account text.
$statusNode=$nodes | Where-Object { $_.Current.Name -eq '查询已成功执行。' -and $_.Current.BoundingRectangle.Height -gt 0 } | Select-Object -First 1
$cropHeight=$height-316
if ($statusNode) {
    $statusTop=[int]$statusNode.Current.BoundingRectangle.Top-$rect.Top
    if ($statusTop -gt 206 -and $statusTop -lt $height) { $cropHeight=$statusTop-206 }
}
# Crop only window title/connection account edges. Query and result pixels are unchanged.
$crop=$bitmap.Clone([System.Drawing.Rectangle]::new(0,206,$width,$cropHeight),[System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
$crop.Save($destination,[System.Drawing.Imaging.ImageFormat]::Png)
$crop.Dispose(); $graphics.Dispose(); $bitmap.Dispose()
$manifestPath=Join-Path $repoRoot 'result/screenshots/manifest.json'
$entries=@()
if (Test-Path -LiteralPath $manifestPath) { $entries=@(Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json) }
$entries=@($entries | Where-Object { $_.image -ne $ImageName })
$entries += [ordered]@{
    image=$ImageName; capturedUtc=[DateTime]::UtcNow.ToString('o'); source=$SqlFile
    sourceSha256=(Get-FileHash -LiteralPath $source).Hash; imageSha256=(Get-FileHash -LiteralPath $destination).Hash
    ssmsVersion=(Get-Item -LiteralPath $SsmsPath).VersionInfo.FileVersion
    database=$Database; executionStatus='查询已成功执行。'; scrolled=[bool]$ScrollResults
    crop='window title/connection edges removed; query/results unchanged'
}
ConvertTo-Json -InputObject @($entries) -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Host "Captured $SqlFile => $ImageName : SSMS execution succeeded."
[void]$loaded.CloseMainWindow()
