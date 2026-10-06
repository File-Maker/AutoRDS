$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
& (Join-Path $PSScriptRoot "build.ps1")
$python = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Backend environment is missing. Run scripts\setup.ps1 first." }
Push-Location $repoRoot
try { & $python -m PyInstaller --noconfirm --clean "AutoRDS.spec" } finally { Pop-Location }
Write-Host "Standalone package: $repoRoot\dist\AutoRDS.exe"
