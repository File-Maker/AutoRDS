$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontend = Join-Path $repoRoot "frontend"
$source = Join-Path $frontend "dist"
$target = Join-Path $repoRoot "backend\app\static"

Push-Location $frontend
try { pnpm build } finally { Pop-Location }

if (-not (Test-Path (Join-Path $source "index.html"))) { throw "Frontend build did not produce index.html" }
$resolvedBackend = (Resolve-Path (Join-Path $repoRoot "backend\app")).Path
$targetParent = Split-Path $target -Parent
if ((Resolve-Path $targetParent).Path -ne $resolvedBackend) { throw "Refusing to replace an unexpected static directory" }
if (Test-Path $target) { Remove-Item -LiteralPath $target -Recurse -Force }
New-Item -ItemType Directory -Path $target | Out-Null
Copy-Item -Path (Join-Path $source "*") -Destination $target -Recurse -Force
Write-Host "Production frontend copied to $target"
