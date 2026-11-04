#!/usr/bin/env bash
# Strategy v3 paper trading. Run every 2 hours, 10 minutes after the candle close (UTC), e.g. cron:
#   10 */2 * * * /path/to/repo/scripts/run_shadow_v3.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
mkdir -p shadow_v3
"$PY" -m bot shadow-v3 >> shadow_v3/run.log 2>&1
