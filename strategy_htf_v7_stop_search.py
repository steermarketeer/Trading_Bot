"""
HTF v7 — stop_pct risk search on frozen S1/S2/S3 bases.

Goal: reduce chop / fake-Bull / dump damage without abandoning WF discipline.
Gate (same as v4/v5):
  >=50% edged folds, median PF > 1, compounded OOS > 0

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_v7_stop_search.py
"""
from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd

from model_policy import policy_dict
from strategy_htf_trend import build_daily, load_eth_5m
from strategy_htf_v4_pass import enrich, make_folds
from strategy_htf_v5_search import Cfg5, enrich_with_btc, eval_wf

MODELS = Path("models")

# Frozen bases (no stop today)
BASES = [
    Cfg5("both_align_no_stop", "both", entry_sma=50, exit_sma=30, align=True,
         regime_stable=5, stop_pct=None, dd_halt=0.25, cooldown=5, atr_max=0.08, atr_min=0.01),
    Cfg5("both_cool7_stable7", "both", entry_sma=50, exit_sma=30, align=True,
         regime_stable=7, stop_pct=None, dd_halt=0.25, cooldown=7, atr_max=0.08, atr_min=0.01),
    Cfg5("both_btc_confirm", "both", entry_sma=50, exit_sma=30, align=True,
         regime_stable=5, stop_pct=None, dd_halt=0.25, cooldown=5, atr_max=0.08, atr_min=0.01,
         btc_confirm=True),
]

STOPS = [None, 0.08, 0.10, 0.12, 0.15]


def configs() -> list[Cfg5]:
    out: list[Cfg5] = []
    for base in BASES:
        for sp in STOPS:
            tag = "nostop" if sp is None else f"stop{int(sp * 100)}"
            name = f"{base.name}__{tag}"
            out.append(replace(base, name=name, stop_pct=sp))
        # tighter vol + modest stop
        out.append(replace(base, name=f"{base.name}__stop10_atr06", stop_pct=0.10, atr_max=0.06))
    return out


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    print("HTF v7 — stop_pct search on S1/S2/S3 bases")
    print(f"Policy: {policy_dict()['name']}\n")

    daily = enrich_with_btc(enrich(build_daily(load_eth_5m())))
    folds = make_folds(daily)
    print(f"Daily bars: {len(daily):,}  folds: {len(folds)}\n")

    results = []
    for cfg in configs():
        res = eval_wf(daily, cfg, folds)
        results.append(res)
        flag = " PASS" if res["pass"] else ""
        print(
            f"{cfg.name:40s} | edged={res['n_edge']}/{res['n_folds']} "
            f"({res['edge_frac']:.0%}) | OOS={res['compounded_oos_ret']:+7.1%} "
            f"medPF={res['median_pf']:.2f} DD={res['worst_dd']:.1%}{flag}"
        )

    passed = [r for r in results if r.get("pass")]
    # Prefer PASS with stop (risk fix), else best PASS overall, else best effort with stop
    with_stop = [r for r in passed if (r.get("params") or {}).get("stop_pct")]
    print("\n" + "=" * 60)
    if with_stop:
        winner = max(with_stop, key=lambda r: (r["compounded_oos_ret"], r["median_pf"], r["edge_frac"]))
        gate = "PASS"
        verdict = (
            f"Stop-aware PASS: '{winner['cfg']}' "
            f"edged={winner['n_edge']}/{winner['n_folds']} "
            f"OOS={winner['compounded_oos_ret']:+.1%} medPF={winner['median_pf']:.2f} "
            f"stop={winner['params'].get('stop_pct')}. "
            "Candidate to replace/augment matching base in shadow after review."
        )
    elif passed:
        winner = max(passed, key=lambda r: (r["compounded_oos_ret"], r["median_pf"], r["edge_frac"]))
        gate = "PASS_NOSTOP_ONLY"
        verdict = (
            f"Only no-stop configs PASS. Best '{winner['cfg']}'. "
            "Stops hurt OOS gate here — keep paper shadow on current winners; "
            "use portfolio agreement / S2-primary for risk, not forced stops."
        )
    else:
        winner = max(results, key=lambda r: (r["compounded_oos_ret"], r["median_pf"], r["edge_frac"]))
        gate = "FAIL"
        verdict = (
            f"No PASS. Best effort '{winner['cfg']}' "
            f"edged={winner['n_edge']}/{winner['n_folds']} OOS={winner['compounded_oos_ret']:+.1%}."
        )

    print(verdict)
    print(f"Research gate: {gate}")
    print("=" * 60)

    freeze = {
        "status": gate,
        "role": "stop_risk_search_v7",
        "verdict": verdict,
        "winner": winner.get("params"),
        "walkforward": {
            "edged": f"{winner['n_edge']}/{winner['n_folds']}",
            "compounded_oos_ret": winner["compounded_oos_ret"],
            "median_pf": winner["median_pf"],
            "worst_dd": winner["worst_dd"],
            "pass": winner.get("pass"),
        },
        "folds": winner.get("folds"),
        "all_passes": [r["cfg"] for r in passed],
        "stop_passes": [r["cfg"] for r in with_stop] if passed else [],
        "model_policy": policy_dict(),
        "note": (
            "If stop_passes empty, do not force stops into live shadow winners. "
            "Prefer portfolio agreement_2of3 / s2_primary for delivery risk framing."
        ),
    }
    (MODELS / "htf_v7_stop_winner.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    summary = {
        "strategy": "htf_v7_stop_search",
        "gate": gate,
        "verdict": verdict,
        "winner": {k: v for k, v in winner.items() if k != "folds"},
        "n_pass": len(passed),
        "n_stop_pass": len(with_stop),
        "all": [{k: v for k, v in r.items() if k != "folds"} for r in results],
    }
    (MODELS / "htf_v7_stop_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("folds", "params")} for r in results]).to_csv(
        MODELS / "htf_v7_stop_leaderboard.csv", index=False
    )
    print("Saved models/htf_v7_stop_winner.json")
    print("Saved models/htf_v7_stop_summary.json")
    print("Saved models/htf_v7_stop_leaderboard.csv")


if __name__ == "__main__":
    main()
