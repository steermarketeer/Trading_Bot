# Strategy v3 paper trading (no orders). Task Scheduler: every 2 hours, starting at 00:10 UTC.
#   Program: powershell.exe   Arguments: -ExecutionPolicy Bypass -File "<repo>\scripts\run_shadow_v3.ps1"
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
New-Item -ItemType Directory -Force -Path "shadow_v3" | Out-Null
& $py -m bot shadow-v3 *>> "shadow_v3\run.log"
exit $LASTEXITCODE
