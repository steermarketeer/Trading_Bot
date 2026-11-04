# Project rules for Claude

## Accuracy and audits (applies to every task)
- Target: **zero errors that can change results** (numbers, signals, trades, win rates, P&L, backtest/shadow outcomes).
- After building or changing anything that produces results, verify it and re-audit **only for issues that can
  impact results**: lookahead/hindsight, wrong formulas, sign/direction mistakes, off-by-one in entries/exits,
  wrong costs/funding/leverage math, misaligned rows, data errors, statistical mistakes, misleading report numbers.
- Repeat fix -> re-verify until no result-impacting issue remains.
- **Do not** spend audit rounds on cosmetic issues, wording, style, warm-up-only edge cases or code that cannot
  change a result. Fix those only if trivial, and don't re-audit for them.
- When reporting, say plainly what was verified and whether any result-impacting issue is still open.

## Project basics
- Paper only: no code places real exchange orders.
- One engine (`bot/engine.py`) for backtest and shadow; strategies are YAML in `strategies/`.
- Research/holdout discipline: choose rules on data before 2025-11-01; the holdout is for final checks only.
- Run tests with `python -m pytest -q tests`.
