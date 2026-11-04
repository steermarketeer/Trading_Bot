#!/usr/bin/env bash
# Daily paper shadow (new engine). Example cron (00:15 UTC daily):
#   15 0 * * * /path/to/repo/scripts/run_shadow.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
mkdir -p shadow_v2
"$PY" -m bot shadow >> shadow_v2/run.log 2>&1
