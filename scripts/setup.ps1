$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Push-Location (Join-Path $repoRoot "backend")
try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv sync --extra dev --extra packaging
    } else {
        if (-not (Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
        & ".venv\Scripts\python.exe" -m pip install -e ".[dev,packaging]"
    }
} finally { Pop-Location }

Push-Location (Join-Path $repoRoot "frontend")
try { pnpm install --frozen-lockfile } finally { Pop-Location }
