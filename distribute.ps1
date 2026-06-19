param(
    [string]$Version = "v2.0"
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $Root "dist"
$Zip  = Join-Path $Root "OmniWorkspace-$Version.zip"

# Step 1 — Build
Write-Host "[BUILD] Running PyInstaller..." -ForegroundColor Cyan
Push-Location $Root
pyinstaller build.spec 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] Build failed" -ForegroundColor Red; exit 1 }
Pop-Location

# Step 2 — Verify
$Exe = Join-Path $Dist "OmniWorkspace.exe"
if (-not (Test-Path $Exe)) { Write-Host "[FAIL] $Exe not found" -ForegroundColor Red; exit 1 }
$Size = (Get-Item $Exe).Length / 1MB
Write-Host "[OK]   OmniWorkspace.exe ($([math]::Round($Size,1)) MB)" -ForegroundColor Green

# Step 3 — Package
if (Test-Path $Zip) { Remove-Item $Zip }
Write-Host "[ZIP]  Packaging dist/ -> $Zip ..." -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($Dist, $Zip, [System.IO.Compression.CompressionLevel]::Optimal, $false)

$ZipSize = (Get-Item $Zip).Length / 1MB
Write-Host "[OK]   $Zip ($([math]::Round($ZipSize,1)) MB)" -ForegroundColor Green
Write-Host "[DONE] Distribution package ready" -ForegroundColor Cyan
