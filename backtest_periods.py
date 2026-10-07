"""
Multi-period regime baseline check (NO ML).

Runs the same rule (Bull->long, Bear->short) on several calendar windows
so we can see if the failed holdout is period-specific.

Usage:
    .\\.venv\\Scripts\\python.exe backtest_periods.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backtest_regime_baseline import run_regime_baseline
from regime import compute_regime_5m

PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")

# Use a mid-grid compromise: 8h horizon, PT=2 SL=1.5 (best PF on holdout grid)
HORIZON = 96
PT = 2.0
SL = 1.5
FEE = 0.0004

PERIODS = [
    ("2019-11-27", "2020-12-31", "2019-2020"),
    ("2021-01-01", "2021-12-31", "2021"),
    ("2022-01-01", "2022-12-31", "2022"),
    ("2023-01-01", "2023-12-31", "2023"),
    ("2024-01-01", "2024-12-31", "2024"),
    ("2025-01-01", "2025-12-31", "2025"),
    ("2026-03-26", "2026-09-22", "holdout_2026"),
]


def main() -> None:
    # Prefer full tagged train+holdout concat for coverage
    train = pd.read_parquet(PROCESSED / "train_5m_h48.parquet")
    hold = pd.read_parquet(PROCESSED / "holdout_5m_h48.parquet")
    df = pd.concat([train, hold], ignore_index=True).drop_duplicates("open_time").sort_values("open_time")

    reg = compute_regime_5m()[["open_time", "regime"]]
    df = df.merge(reg, on="open_time", how="left")
    df["regime"] = df["regime"].fillna("Neutral")

    print(f"Multi-period baseline  h={HORIZON} PT={PT} SL={SL} fee={FEE}")
    print(f"Rows: {len(df):,}  range: {df['open_time'].iloc[0]} -> {df['open_time'].iloc[-1]}")
    print()

    rows = []
    for start, end, name in PERIODS:
        part = df[(df["open_time"] >= start) & (df["open_time"] <= end + " 23:59:59+00:00")].copy()
        if len(part) < 500:
            print(f"{name:16s} | SKIP (too few rows: {len(part)})")
            continue
        mix = part["regime"].value_counts().to_dict()
        r = run_regime_baseline(
            part.reset_index(drop=True),
            part["regime"].to_numpy(),
            horizon=HORIZON,
            pt_mult=PT,
            sl_mult=SL,
            fee=FEE,
            reenter_every_bars=HORIZON,
        )
        edge = r["total_return"] > 0 and r["profit_factor"] > 1.0 and r["n_trades"] >= 20
        row = {
            "period": name,
            "start": start,
            "end": end,
            "n_bars": int(len(part)),
            "regime_mix": mix,
            "n_trades": r["n_trades"],
            "total_return": r["total_return"],
            "win_rate": r["win_rate"],
            "profit_factor": r["profit_factor"],
            "max_drawdown": r["max_drawdown"],
            "longs": r["longs"],
            "shorts": r["shorts"],
            "has_edge": edge,
        }
        rows.append(row)
        flag = " EDGE" if edge else ""
        print(
            f"{name:16s} | bars={len(part):6d} mix={mix} | "
            f"n={r['n_trades']:4d} ret={r['total_return']:+8.1%} "
            f"win={r['win_rate']:.1%} PF={r['profit_factor']:.2f} "
            f"DD={r['max_drawdown']:.1%} L/S={r['longs']}/{r['shorts']}{flag}"
        )

    edges = [r for r in rows if r["has_edge"]]
    print("\n" + "=" * 60)
    print(f"Periods with edge: {len(edges)} / {len(rows)}")
    if edges:
        for e in edges:
            print(f"  {e['period']}: ret={e['total_return']:+.1%} PF={e['profit_factor']:.2f}")
        verdict = (
            "Edge appears in some historical windows. "
            "Holdout failure may be period-specific — do walk-forward next, still no live."
        )
    else:
        verdict = (
            "No calendar year shows edge with this baseline setup. "
            "Current regime+ATR barrier hypothesis is weak for ETH 5m — rethink strategy before more ML."
        )
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    # json-safe
    out_rows = []
    for r in rows:
        out_rows.append({
            **{k: v for k, v in r.items() if k != "regime_mix"},
            "regime_mix": {str(k): int(v) for k, v in r["regime_mix"].items()},
        })
    summary = {
        "settings": {"horizon_bars": HORIZON, "pt_atr": PT, "sl_atr": SL, "fee": FEE},
        "periods": out_rows,
        "n_edge_periods": len(edges),
        "verdict": verdict,
    }
    path = MODELS_DIR / "period_baseline_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.DataFrame(out_rows).to_csv(MODELS_DIR / "period_baseline_results.csv", index=False)
    print(f"\nSaved {path}")
    print(f"Saved models/period_baseline_results.csv")


if __name__ == "__main__":
    main()
