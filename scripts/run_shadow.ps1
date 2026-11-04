# Daily paper shadow (new engine). Point Windows Task Scheduler at this file:
#   Program: powershell.exe
#   Arguments: -ExecutionPolicy Bypass -File "<repo>\scripts\run_shadow.ps1"
# Runs after 00:05 UTC are fine; it processes every completed day it hasn't seen yet.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
New-Item -ItemType Directory -Force -Path "shadow_v2" | Out-Null
& $py -m bot shadow *>> "shadow_v2\run.log"
exit $LASTEXITCODE
