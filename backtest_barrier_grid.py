"""
Barrier x horizon grid on the regime-only baseline (NO ML).

Sweeps PT/SL ATR multiples and label horizons on the same holdout.
Also runs a simple daily trend-follow variant (enter once per day in Bear/Bull).

Usage:
    .\\.venv\\Scripts\\python.exe backtest_barrier_grid.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_first_model import simulate_trade
from backtest_regime_baseline import run_regime_baseline
from regime import allowed_side, compute_regime_5m

PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")

# Horizons in 5m bars
HORIZONS = [
    12,   # 1h
    48,   # 4h
    96,   # 8h
    288,  # 1d
]

# (pt_mult, sl_mult) — reward:risk implied
BARRIERS = [
    (1.0, 1.0),
    (1.5, 1.0),
    (1.5, 1.5),
    (2.0, 1.0),  # current Mode B
    (2.0, 1.5),
    (3.0, 1.0),
    (3.0, 1.5),
    (3.0, 2.0),
]


def run_daily_trend_follow(
    df: pd.DataFrame,
    regimes: np.ndarray,
    fee: float,
) -> dict:
    """
    Once per UTC day: if regime is Bull/Bear at first bar of day, enter that side
    and hold until end of day close (or stop at 2x daily ATR approx using 5m ATR*sqrt(288)).
    Simplified: hold to day close, fees both sides, no intraday stop (diagnostic).
    """
    times = pd.to_datetime(df["open_time"], utc=True)
    close = df["close"].to_numpy(float)
    day = times.dt.floor("D")
    trades = []

    for d, idx in df.groupby(day).groups.items():
        idx = list(idx)
        if len(idx) < 2:
            continue
        i0, i1 = idx[0], idx[-1]
        allow = allowed_side(str(regimes[i0]))
        if allow is None:
            continue
        px0, px1 = close[i0], close[i1]
        if allow == "long":
            gross = (px1 - px0) / px0
        else:
            gross = (px0 - px1) / px0
        net = gross - 2.0 * fee
        trades.append({
            "entry_time": str(times.iloc[i0]),
            "side": allow,
            "regime": str(regimes[i0]),
            "net_return": net,
            "bars_held": i1 - i0,
            "exit_reason": "eod",
            "entry_price": float(px0),
        })

    if not trades:
        return {
            "name": "daily_eod_hold",
            "n_trades": 0,
            "total_return": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_return": 0.0,
            "max_drawdown": 0.0,
            "longs": 0,
            "shorts": 0,
            "exit_reasons": {},
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
        "name": "daily_eod_hold",
        "n_trades": int(len(tdf)),
        "total_return": float(equity[-1] - 1.0),
        "win_rate": float((rets > 0).mean()),
        "profit_factor": float(pf),
        "avg_return": float(rets.mean()),
        "max_drawdown": float(dd.min()),
        "longs": int((tdf["side"] == "long").sum()),
        "shorts": int((tdf["side"] == "short").sum()),
        "exit_reasons": tdf["exit_reason"].value_counts().to_dict(),
        "trades": trades,
    }


def main() -> None:
    meta = json.loads((PROCESSED / "dataset_meta.json").read_text(encoding="utf-8"))
    hold = pd.read_parquet(meta["holdout_path"])
    fee = float(meta["taker_fee"])

    reg = compute_regime_5m()[["open_time", "regime"]]
    hold = hold.merge(reg, on="open_time", how="left")
    hold["regime"] = hold["regime"].fillna("Neutral")
    regimes = hold["regime"].to_numpy()

    print("Barrier x horizon grid (regime baseline, no ML)")
    print(f"Holdout: {hold['open_time'].iloc[0]} -> {hold['open_time'].iloc[-1]}")
    print(f"Regimes: {hold['regime'].value_counts().to_dict()}")
    print()

    rows = []
    for h in HORIZONS:
        # re-enter at most once per horizon to limit churn
        gap = h
        for pt, sl in BARRIERS:
            r = run_regime_baseline(
                hold, regimes,
                horizon=h,
                pt_mult=pt,
                sl_mult=sl,
                fee=fee,
                reenter_every_bars=gap,
            )
            row = {
                "horizon_bars": h,
                "horizon_hours": h * 5 / 60,
                "pt_atr": pt,
                "sl_atr": sl,
                "rr": pt / sl if sl else None,
                "n_trades": r["n_trades"],
                "total_return": r["total_return"],
                "win_rate": r["win_rate"],
                "profit_factor": r["profit_factor"],
                "avg_return": r["avg_return"],
                "max_drawdown": r["max_drawdown"],
                "longs": r["longs"],
                "shorts": r["shorts"],
            }
            rows.append(row)
            flag = " <<" if r["total_return"] > 0 and r["profit_factor"] > 1 and r["n_trades"] >= 20 else ""
            print(
                f"h={h:3d} PT={pt:.1f} SL={sl:.1f} | "
                f"n={r['n_trades']:4d} ret={r['total_return']:+7.2%} "
                f"win={r['win_rate']:.1%} PF={r['profit_factor']:.2f} "
                f"DD={r['max_drawdown']:.1%}{flag}"
            )

    grid = pd.DataFrame(rows)
    grid_path = MODELS_DIR / "barrier_grid_results.csv"
    grid.to_csv(grid_path, index=False)

    # Rank: require enough trades, prefer PF then return
    usable = grid[grid["n_trades"] >= 20].copy()
    if len(usable):
        usable = usable.sort_values(
            ["profit_factor", "total_return"], ascending=[False, False]
        )
        best = usable.iloc[0].to_dict()
    else:
        best = grid.sort_values("total_return", ascending=False).iloc[0].to_dict()

    edge_rows = grid[(grid["total_return"] > 0) & (grid["profit_factor"] > 1.0) & (grid["n_trades"] >= 20)]
    print("\n" + "=" * 60)
    print("BEST grid cell (n>=20, rank PF then return):")
    print(
        f"  horizon={best['horizon_bars']} bars ({best['horizon_hours']}h) "
        f"PT={best['pt_atr']}*ATR SL={best['sl_atr']}*ATR"
    )
    print(
        f"  trades={int(best['n_trades'])} ret={best['total_return']:+.2%} "
        f"win={best['win_rate']:.1%} PF={best['profit_factor']:.2f} "
        f"DD={best['max_drawdown']:.1%}"
    )
    print(f"  cells with edge (ret>0 & PF>1 & n>=20): {len(edge_rows)} / {len(grid)}")
    print("=" * 60)

    print("\n--- Daily EOD trend-follow (no ATR stop) ---")
    daily = run_daily_trend_follow(hold, regimes, fee)
    print(
        f"daily_eod_hold | trades={daily['n_trades']} ret={daily['total_return']:+.2%} "
        f"win={daily['win_rate']:.1%} PF={daily['profit_factor']:.2f} "
        f"DD={daily['max_drawdown']:.1%} L/S={daily['longs']}/{daily['shorts']}"
    )

    daily_edge = daily["total_return"] > 0 and daily["profit_factor"] > 1.0 and daily["n_trades"] >= 20
    any_edge = len(edge_rows) > 0 or daily_edge

    if any_edge:
        verdict = (
            "At least one setup shows edge on this holdout. "
            "Freeze that rule, then test walk-forward / Bull periods before adding ML."
        )
    else:
        verdict = (
            "No barrier/horizon cell and no daily EOD rule shows edge on this Bear holdout. "
            "Do not train more ML yet. Next: test on Bull-inclusive history or change market hypothesis."
        )
    print(f"\nVERDICT: {verdict}")

    # Top 5 by PF
    top = usable.head(5) if len(usable) else grid.head(5)
    print("\nTop cells:")
    print(top.to_string(index=False))

    summary = {
        "n_cells": int(len(grid)),
        "n_edge_cells": int(len(edge_rows)),
        "best_cell": {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v) for k, v in best.items()},
        "daily_eod": {k: v for k, v in daily.items() if k != "trades"},
        "daily_has_edge": daily_edge,
        "has_any_edge": any_edge,
        "verdict": verdict,
        "grid_csv": str(grid_path),
    }
    # json-safe best
    for k, v in list(summary["best_cell"].items()):
        if isinstance(v, (np.floating,)):
            summary["best_cell"][k] = float(v)
        elif isinstance(v, (np.integer,)):
            summary["best_cell"][k] = int(v)

    if daily.get("trades"):
        pd.DataFrame(daily["trades"]).to_csv(MODELS_DIR / "holdout_trades_daily_eod.csv", index=False)

    (MODELS_DIR / "barrier_grid_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\nSaved {grid_path}")
    print(f"Saved models/barrier_grid_summary.json")


if __name__ == "__main__":
    main()
