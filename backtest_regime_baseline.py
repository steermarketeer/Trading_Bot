"""
Regime-only baseline (NO machine learning).

Rule: Bull -> long, Bear -> short, Neutral -> flat.
Same Mode B barriers, fees, one-position-at-a-time as the ML backtests.
Compares against saved ML results if present.

Usage:
    .\\.venv\\Scripts\\python.exe backtest_regime_baseline.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_first_model import simulate_trade
from regime import allowed_side, compute_regime_5m

PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")


def run_regime_baseline(
    df: pd.DataFrame,
    regimes: np.ndarray,
    horizon: int,
    pt_mult: float,
    sl_mult: float,
    fee: float,
    *,
    reenter_every_bars: int = 1,
) -> dict:
    """
    When flat and regime allows a side, enter that side.
    reenter_every_bars=1 means enter on the next bar after exit if still allowed.
    """
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    atr = df["atr_14"].to_numpy(float)
    times = df["open_time"].to_numpy()

    trades = []
    i = 0
    n = len(df)
    cooldown = 0
    while i < n - 1:
        if cooldown > 0:
            cooldown -= 1
            i += 1
            continue

        allow = allowed_side(str(regimes[i]))
        if allow is None:
            i += 1
            continue

        net, held, reason = simulate_trade(
            allow, i, close, high, low, atr, horizon, pt_mult, sl_mult, fee
        )
        if held <= 0:
            i += 1
            continue

        trades.append({
            "entry_time": str(times[i]),
            "side": allow,
            "regime": str(regimes[i]),
            "net_return": net,
            "bars_held": held,
            "exit_reason": reason,
            "entry_price": float(close[i]),
        })
        i += held + 1
        cooldown = max(0, reenter_every_bars - 1)

    if not trades:
        return {
            "n_trades": 0,
            "total_return": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_return": 0.0,
            "max_drawdown": 0.0,
            "longs": 0,
            "shorts": 0,
            "exit_reasons": {},
            "trades": [],
        }

    tdf = pd.DataFrame(trades)
    rets = tdf["net_return"].to_numpy()
    equity = np.cumprod(1.0 + rets)
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    wins = rets[rets > 0].sum() if (rets > 0).any() else 0.0
    losses = -rets[rets <= 0].sum() if (rets <= 0).any() else 0.0
    pf = (wins / losses) if losses > 0 else 999.0
    return {
        "n_trades": int(len(tdf)),
        "total_return": float(equity[-1] - 1.0),
        "win_rate": float((rets > 0).mean()),
        "profit_factor": float(pf),
        "avg_return": float(rets.mean()),
        "max_drawdown": float(dd.min()),
        "longs": int((tdf["side"] == "long").sum()),
        "shorts": int((tdf["side"] == "short").sum()),
        "exit_reasons": tdf["exit_reason"].value_counts().to_dict(),
        "regime_counts": tdf["regime"].value_counts().to_dict(),
        "trades": trades,
    }


def _load_ml_best(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if "best_gated" in data:
        return data["best_gated"]
    if "best" in data:
        return data["best"]
    if "selected" in data:
        return data["selected"]
    return None


def main() -> None:
    meta = json.loads((PROCESSED / "dataset_meta.json").read_text(encoding="utf-8"))
    hold = pd.read_parquet(meta["holdout_path"])

    print("Regime-only baseline (no ML)")
    print(f"  holdout:  {hold['open_time'].iloc[0]} -> {hold['open_time'].iloc[-1]}")
    print(f"  horizon:  {meta['horizon_bars']} bars ({meta.get('horizon_hours', '?')}h)")
    print(f"  barriers: PT={meta['pt_atr_mult']}*ATR  SL={meta['sl_atr_mult']}*ATR")
    print(f"  fee/side: {meta['taker_fee']}")
    print()

    reg = compute_regime_5m()[["open_time", "regime"]]
    hold = hold.merge(reg, on="open_time", how="left")
    hold["regime"] = hold["regime"].fillna("Neutral")
    print("Holdout regime mix:")
    print(hold["regime"].value_counts().to_string())
    print()

    # Variant A: re-enter immediately when flat + regime allows
    # Variant B: wait one full horizon between entries (less churn)
    variants = {
        "immediate_reentry": 1,
        "wait_1_horizon": int(meta["horizon_bars"]),
        "wait_1_day": 288,  # 288 * 5m = 24h
    }

    results = {}
    for name, gap in variants.items():
        r = run_regime_baseline(
            hold,
            hold["regime"].to_numpy(),
            horizon=int(meta["horizon_bars"]),
            pt_mult=float(meta["pt_atr_mult"]),
            sl_mult=float(meta["sl_atr_mult"]),
            fee=float(meta["taker_fee"]),
            reenter_every_bars=gap,
        )
        results[name] = {k: v for k, v in r.items() if k != "trades"}
        print(
            f"{name:20s} | trades={r['n_trades']:4d} | ret={r['total_return']:+.2%} | "
            f"win={r['win_rate']:.1%} | PF={r['profit_factor']:.2f} | "
            f"avg={r['avg_return']:+.3%} | maxDD={r['max_drawdown']:.1%} | "
            f"L/S={r['longs']}/{r['shorts']}"
        )
        print(f"{'':20s}   exits={r['exit_reasons']}")

    # Pick least-bad / best by total return then PF
    best_name = max(results, key=lambda k: (results[k]["total_return"], results[k]["profit_factor"]))
    best = results[best_name]
    edge = best["total_return"] > 0 and best["profit_factor"] > 1.0

    print("\n" + "=" * 60)
    print(f"BEST baseline variant: {best_name}")
    print(f"  trades:        {best['n_trades']}")
    print(f"  total return:  {best['total_return']:+.2%}")
    print(f"  win rate:      {best['win_rate']:.1%}")
    print(f"  profit factor: {best['profit_factor']:.2f}")
    print(f"  max drawdown:  {best['max_drawdown']:.1%}")
    print(f"  edge?:         {'YES' if edge else 'NO'}")
    print("=" * 60)

    # Compare to ML
    print("\n--- vs prior ML runs (same holdout / barriers) ---")
    comparisons = {
        "ML v1 gated": _load_ml_best(MODELS_DIR / "holdout_backtest_gated.json"),
        "ML dual Bull/Bear": _load_ml_best(MODELS_DIR / "holdout_backtest_dual.json"),
    }
    # gated file may have been overwritten by v2 run — still fine
    for label, m in comparisons.items():
        if not m:
            print(f"  {label}: (no saved summary)")
            continue
        print(
            f"  {label:20s} | trades={m.get('n_trades')} | "
            f"ret={m.get('total_return', 0):+.2%} | PF={m.get('profit_factor', 0):.2f}"
        )
    print(
        f"  {'regime baseline':20s} | trades={best['n_trades']} | "
        f"ret={best['total_return']:+.2%} | PF={best['profit_factor']:.2f}"
    )

    if edge:
        verdict = "Baseline HAS edge. ML must beat this before it is useful."
    elif best["total_return"] > (comparisons.get("ML dual Bull/Bear") or {}).get("total_return", -9e9):
        verdict = (
            "Baseline also loses, but is competitive with / better than ML. "
            "ML is not adding value on this holdout — fix labels/features/barriers, not the algorithm."
        )
    else:
        verdict = (
            "Both baseline and ML lose on this holdout. "
            "Problem is the trade setup (barriers/horizon/period), not which model."
        )
    print(f"\nVERDICT: {verdict}")

    # Save full immediate variant trades for inspection
    full = run_regime_baseline(
        hold,
        hold["regime"].to_numpy(),
        horizon=int(meta["horizon_bars"]),
        pt_mult=float(meta["pt_atr_mult"]),
        sl_mult=float(meta["sl_atr_mult"]),
        fee=float(meta["taker_fee"]),
        reenter_every_bars=variants[best_name],
    )
    pd.DataFrame(full["trades"]).to_csv(MODELS_DIR / "holdout_trades_baseline.csv", index=False)
    out = {
        "variants": results,
        "best_variant": best_name,
        "best": best,
        "has_edge": edge,
        "verdict": verdict,
        "ml_comparison": {
            k: ({kk: vv for kk, vv in (v or {}).items() if kk != "trades"} if v else None)
            for k, v in comparisons.items()
        },
    }
    (MODELS_DIR / "holdout_backtest_baseline.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print(f"\nSaved models/holdout_trades_baseline.csv")
    print(f"Saved models/holdout_backtest_baseline.json")


if __name__ == "__main__":
    main()
