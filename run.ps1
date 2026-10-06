$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot
$python = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
$staticIndex = Join-Path $repoRoot "backend\app\static\index.html"

if (-not (Test-Path $python)) { & (Join-Path $repoRoot "scripts\setup.ps1") }
if (-not (Test-Path $staticIndex)) { & (Join-Path $repoRoot "scripts\build.ps1") }

$waiter = @'
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8134/api/health" -TimeoutSec 1
        if ($response.StatusCode -eq 200) { Start-Process "http://127.0.0.1:8134"; break }
    } catch { Start-Sleep -Milliseconds 500 }
}
'@
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", $waiter
Push-Location (Join-Path $repoRoot "backend")
try { & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8134 } finally { Pop-Location }
