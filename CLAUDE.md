# Project rules for Claude

## Accuracy and audits (applies to every task)
- Target: **zero errors that can change results** (numbers, signals, trades, win rates, P&L, backtest/shadow outcomes).
- After building or changing anything that produces results, verify it and re-audit **only for issues that can
  impact results**: lookahead/hindsight, wrong formulas, sign/direction mistakes, off-by-one in entries/exits,
  wrong costs/funding/leverage math, misaligned rows, data errors, statistical mistakes, misleading report numbers.
- Repeat fix -> re-verify until no result-impacting issue remains.
- **Global rule (the user's standing instruction): re-audit until there are 0 errors.** Every new or changed study,
  strategy, report or chart number gets an independent audit (a fresh reviewer that did not write the code, given
  the code and the project conventions, not the author's conclusions) before its results are presented as final.
  Fix every confirmed result-impacting issue, rerun, and audit again; stop only when a full audit round finds zero.
  Results shown before that are labelled "audit still running". Every report states the audit rounds and the outcome.
- **Do not** spend audit rounds on cosmetic issues, wording, style, warm-up-only edge cases or code that cannot
  change a result. Fix those only if trivial, and don't re-audit for them.
- When reporting, say plainly what was verified and whether any result-impacting issue is still open.

## Project basics
- Paper only: no code places real exchange orders.
- One engine (`bot/engine.py`) for backtest and shadow; strategies are YAML in `strategies/`.
- Research/holdout discipline: choose rules on data before 2025-11-01; the holdout is for final checks only.
- Run tests with `python -m pytest -q tests`.
