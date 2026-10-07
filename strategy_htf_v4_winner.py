"""
Frozen HTF v4 winner (walk-forward PASS) + stress report.

Config: both_align_no_stop
  - both sides, SMA alignment, exit SMA30, regime stable 5d
  - dd_halt 25%, cooldown 5d, no hard stop

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_v4_winner.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from model_policy import policy_dict
from strategy_htf_v4_pass import Cfg, enrich, run_cfg
from strategy_htf_trend import build_daily, load_eth_5m

MODELS_DIR = Path("models")

WINNER = Cfg(
    name="both_align_no_stop",
    mode="both",
    entry_sma=50,
    exit_sma=30,
    align=True,
    regime_stable=5,
    stop_pct=None,
    dd_halt=0.25,
    cooldown=5,
    atr_max=0.08,
    atr_min=0.01,
)

STRESS = [
    ("covid_2020", "2020-02-15", "2020-04-30"),
    ("bear_2022_h1", "2022-01-01", "2022-06-30"),
    ("ftx_2022", "2022-11-01", "2022-12-15"),
    ("chop_2024", "2024-01-01", "2024-06-30"),
    ("holdout_2026", "2026-03-26", "2026-09-22"),
    ("full", "2020-01-16", "2026-09-22"),
]


def main() -> None:
    daily = enrich(build_daily(load_eth_5m()))
    print(f"Frozen winner: {WINNER.name}")
    print(f"Policy: {policy_dict()['name']}\n")

    rows = []
    for name, start, end in STRESS:
        part = daily[
            (daily["open_time"] >= pd.Timestamp(start, tz="UTC"))
            & (daily["open_time"] <= pd.Timestamp(end, tz="UTC"))
        ].reset_index(drop=True)
        if len(part) < 20:
            continue
        r = run_cfg(part, WINNER)
        rows.append({
            "window": name,
            "start": start,
            "end": end,
            "n_days": len(part),
            "n_trades": r["n_trades"],
            "total_return": r["total_return"],
            "profit_factor": r["profit_factor"],
            "max_drawdown": r["max_drawdown"],
            "win_rate": r["win_rate"],
        })
        print(
            f"{name:14s} | n={r['n_trades']:3d} ret={r['total_return']:+8.1%} "
            f"PF={r['profit_factor']:.2f} DD={r['max_drawdown']:.1%} win={r['win_rate']:.1%}"
        )

    # Save full-sample trades
    full = daily
    fr = run_cfg(full, WINNER)
    pd.DataFrame(fr["trades"]).to_csv(MODELS_DIR / "htf_v4_winner_trades.csv", index=False)

    payload = {
        "status": "WALK_FORWARD_PASS",
        "winner": WINNER.__dict__,
        "model_policy": policy_dict(),
        "walkforward": {
            "edged": "5/8",
            "compounded_oos_ret": 0.33,
            "median_pf": 1.20,
            "worst_dd": -0.216,
            "source": "htf_v4_pass_summary.json",
        },
        "stress": rows,
        "note": (
            "Research gate passed. Next optional step: shadow daily logger. "
            "Not live. Stateless policy remains."
        ),
    }
    (MODELS_DIR / "htf_v4_winner.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nSaved models/htf_v4_winner.json")
    print(f"Saved models/htf_v4_winner_trades.csv ({fr['n_trades']} trades)")


if __name__ == "__main__":
    main()
