"""
HTF strategy #3 search — walk-forward PASS, distinct from S1 and S2.

Excluded:
  S1 both_align_no_stop
  S2 both_cool7_stable7

Same gate: >=50% edged folds, median PF>1, compounded OOS>0.
Stateless / no trade-pattern memory.

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_v6_s3_search.py
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from model_policy import policy_dict
from strategy_htf_trend import build_daily, load_eth_5m
from strategy_htf_v4_pass import enrich, make_folds
from strategy_htf_v5_search import Cfg5, enrich_with_btc, eval_wf

MODELS_DIR = Path("models")
EXCLUDE = {"both_align_no_stop", "both_cool7_stable7"}


def configs_s3() -> list[Cfg5]:
    return [
        # Best v5 PASSes (re-rank as #3)
        Cfg5("both_btc_confirm", "both", exit_sma=30, stop_pct=None, btc_confirm=True, dd_halt=0.25),
        Cfg5("long_only_sma20_nostop", "long_only", exit_sma=20, stop_pct=None, dd_halt=0.25, regime_stable=3),
        Cfg5("long_btc_sma20", "long_only", exit_sma=20, stop_pct=None, btc_confirm=True, dd_halt=0.20, regime_stable=3),
        Cfg5("long_only_stable7", "long_only", exit_sma=30, regime_stable=7, stop_pct=None, dd_halt=0.25),
        Cfg5("align_both_sma30_nostop", "both", exit_sma=30, stop_pct=None, dd_halt=0.20),
        # New variants aiming for diversity
        Cfg5("long_only_cool7_stable7", "long_only", exit_sma=30, regime_stable=7, cooldown=7, stop_pct=None, dd_halt=0.25),
        Cfg5("both_btc_cool7", "both", exit_sma=30, regime_stable=7, cooldown=7, stop_pct=None, btc_confirm=True, dd_halt=0.25),
        Cfg5("long_btc_cool5", "long_only", exit_sma=30, cooldown=5, stop_pct=None, btc_confirm=True, dd_halt=0.25),
        Cfg5("both_sma30_dd20_cool7", "both", exit_sma=30, cooldown=7, stop_pct=None, dd_halt=0.20, regime_stable=5),
        Cfg5("short_btc_stable7", "short_only", exit_sma=30, regime_stable=7, cooldown=7, stop_pct=None, btc_confirm=True, dd_halt=0.20),
        Cfg5("long_only_entry100_nostop", "long_only", entry_sma=100, exit_sma=50, stop_pct=None, dd_halt=0.25, regime_stable=5),
        Cfg5("both_btc_sma20", "both", exit_sma=20, stop_pct=None, btc_confirm=True, dd_halt=0.25, regime_stable=5, cooldown=5),
    ]


def diversity_bonus(name: str) -> float:
    """Prefer configs unlike S1/S2 (btc / long_only)."""
    score = 0.0
    if "btc" in name:
        score += 0.05
    if "long_only" in name or name.startswith("long_"):
        score += 0.03
    if "short" in name:
        score += 0.02
    return score


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("Strategy #3 search (exclude S1/S2)")
    print(f"Excluded: {sorted(EXCLUDE)}")
    print(f"Policy: {policy_dict()['name']}\n")

    daily = enrich_with_btc(enrich(build_daily(load_eth_5m())))
    folds = make_folds(daily)
    print(f"Daily bars: {len(daily):,}  folds: {len(folds)}\n")

    results = []
    for cfg in configs_s3():
        if cfg.name in EXCLUDE:
            continue
        res = eval_wf(daily, cfg, folds)
        results.append(res)
        flag = " PASS" if res["pass"] else ""
        print(
            f"{cfg.name:30s} | edged={res['n_edge']}/{res['n_folds']} "
            f"({res['edge_frac']:.0%}) | OOS={res['compounded_oos_ret']:+7.1%} "
            f"medPF={res['median_pf']:.2f} DD={res['worst_dd']:.1%}{flag}"
        )

    passed = [r for r in results if r.get("pass") and r["cfg"] not in EXCLUDE]
    print("\n" + "=" * 60)
    if not passed:
        best = max(results, key=lambda r: (r["compounded_oos_ret"], r["median_pf"], r["edge_frac"]))
        verdict = f"No new PASS for #3. Best effort: {best['cfg']}"
        print(verdict)
        gate = "FAIL"
        winner = best
    else:
        # Rank: pass already; prefer OOS, medPF, edge_frac, then diversity
        winner = max(
            passed,
            key=lambda r: (
                r["compounded_oos_ret"] + diversity_bonus(r["cfg"]),
                r["median_pf"],
                r["edge_frac"],
                -abs(r["worst_dd"]),
            ),
        )
        gate = "PASS"
        verdict = (
            f"Strategy #3 PASS: '{winner['cfg']}' "
            f"edged={winner['n_edge']}/{winner['n_folds']} "
            f"OOS={winner['compounded_oos_ret']:+.1%} medPF={winner['median_pf']:.2f}. "
            "Not added to shadow yet."
        )
        print(f"STRATEGY #3 WINNER: {winner['cfg']}")
        print(
            f"  edged={winner['n_edge']}/{winner['n_folds']} "
            f"OOS={winner['compounded_oos_ret']:+.1%} medPF={winner['median_pf']:.2f} "
            f"worstDD={winner['worst_dd']:.1%}"
        )
        freeze = {
            "status": "WALK_FORWARD_PASS",
            "role": "strategy_3",
            "complements": ["both_align_no_stop", "both_cool7_stable7"],
            "winner": winner["params"],
            "walkforward": {
                "edged": f"{winner['n_edge']}/{winner['n_folds']}",
                "compounded_oos_ret": winner["compounded_oos_ret"],
                "median_pf": winner["median_pf"],
                "worst_dd": winner["worst_dd"],
            },
            "folds": winner["folds"],
            "model_policy": policy_dict(),
            "note": "Third PASS strategy. Stateless. Wire into shadow when requested.",
        }
        (MODELS_DIR / "htf_v6_s3_winner.json").write_text(
            json.dumps(freeze, indent=2), encoding="utf-8"
        )
        print("Frozen -> models/htf_v6_s3_winner.json")

    print(f"Research gate: {gate}")
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    out = {
        "strategy": "htf_v6_strategy3_search",
        "excluded": list(EXCLUDE),
        "gate": gate,
        "verdict": verdict,
        "winner": {k: v for k, v in winner.items() if k != "folds"},
        "all_passes": [r["cfg"] for r in passed],
        "leaderboard": [{k: v for k, v in r.items() if k not in ("folds", "params")} for r in results],
    }
    (MODELS_DIR / "htf_v6_s3_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("folds", "params")} for r in results]).to_csv(
        MODELS_DIR / "htf_v6_s3_leaderboard.csv", index=False
    )
    print("Saved models/htf_v6_s3_summary.json")
    print("Saved models/htf_v6_s3_leaderboard.csv")


if __name__ == "__main__":
    main()
