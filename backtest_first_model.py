"""
Holdout backtest for the first LightGBM model.

- Loads models/lgbm_5m_v1.txt + holdout parquet
- Enters long/short only when directional probability >= CONFIDENCE
- One position at a time (signal during an open trade is ignored)
- Mode B exits: +2 ATR target / -1 ATR stop, max HORIZON bars
- Stop-first if the same bar hits both; fees both sides (taker)
- Sweeps a few confidence thresholds and prints the best

Usage:
    .\\.venv\\Scripts\\python.exe backtest_first_model.py
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")
MODEL_PATH = MODELS_DIR / "lgbm_5m_v1.txt"

LABEL_DROP = {
    "open_time", "open", "high", "low", "close", "volume", "atr_14",
    "label", "label_name", "bars_to_hit",
}

THRESHOLDS = [0.40, 0.45, 0.50, 0.55, 0.60]


def simulate_trade(
    side: str,
    i: int,
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    horizon: int,
    pt_mult: float,
    sl_mult: float,
    fee: float,
) -> tuple[float, int, str]:
    """
    Returns (net_return_on_notional, bars_held, exit_reason).
    Return is fractional price P&L minus round-trip taker fees.
    """
    px = close[i]
    a = atr[i]
    if not np.isfinite(px) or not np.isfinite(a) or a <= 0:
        return 0.0, 0, "invalid"

    n = len(close)
    end = min(i + horizon, n - 1)

    if side == "long":
        pt = px + pt_mult * a
        sl = px - sl_mult * a
    else:
        pt = px - pt_mult * a
        sl = px + sl_mult * a

    for j in range(i + 1, end + 1):
        hit_pt = False
        hit_sl = False
        if side == "long":
            hit_pt = high[j] >= pt
            hit_sl = low[j] <= sl
        else:
            hit_pt = low[j] <= pt
            hit_sl = high[j] >= sl

        if hit_pt and hit_sl:
            # stop-first (conservative)
            exit_px = sl
            reason = "stop_same_bar"
        elif hit_sl:
            exit_px = sl
            reason = "stop"
        elif hit_pt:
            exit_px = pt
            reason = "target"
        else:
            continue

        if side == "long":
            gross = (exit_px - px) / px
        else:
            gross = (px - exit_px) / px
        net = gross - 2.0 * fee
        return net, j - i, reason

    # timeout at last close
    exit_px = close[end]
    if side == "long":
        gross = (exit_px - px) / px
    else:
        gross = (px - exit_px) / px
    net = gross - 2.0 * fee
    return net, end - i, "timeout"


def run_backtest(
    df: pd.DataFrame,
    proba: np.ndarray,
    confidence: float,
    horizon: int,
    pt_mult: float,
    sl_mult: float,
    fee: float,
) -> dict:
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    atr = df["atr_14"].to_numpy(float)
    times = df["open_time"].to_numpy()

    p_timeout = proba[:, 0]
    p_up = proba[:, 1]
    p_down = proba[:, 2]

    trades = []
    i = 0
    n = len(df)
    while i < n - 1:
        # pick direction only if confident and beats the other side + timeout
        side = None
        conf = 0.0
        if p_up[i] >= confidence and p_up[i] >= p_down[i] and p_up[i] >= p_timeout[i]:
            side, conf = "long", float(p_up[i])
        elif p_down[i] >= confidence and p_down[i] >= p_up[i] and p_down[i] >= p_timeout[i]:
            side, conf = "short", float(p_down[i])

        if side is None:
            i += 1
            continue

        net, held, reason = simulate_trade(
            side, i, close, high, low, atr, horizon, pt_mult, sl_mult, fee
        )
        if held <= 0:
            i += 1
            continue

        trades.append({
            "entry_time": str(times[i]),
            "side": side,
            "confidence": conf,
            "net_return": net,
            "bars_held": held,
            "exit_reason": reason,
            "entry_price": float(close[i]),
        })
        i += held  # no overlapping positions
        i += 1

    if not trades:
        return {
            "confidence": confidence,
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
    wins = rets[rets > 0]
    losses = rets[rets <= 0]
    gross_win = wins.sum() if len(wins) else 0.0
    gross_loss = -losses.sum() if len(losses) else 0.0
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")

    return {
        "confidence": confidence,
        "n_trades": int(len(tdf)),
        "total_return": float(equity[-1] - 1.0),
        "win_rate": float((rets > 0).mean()),
        "profit_factor": float(pf) if np.isfinite(pf) else 999.0,
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
    feat_cols = [c for c in hold.columns if c not in LABEL_DROP]
    X = hold[feat_cols].replace([np.inf, -np.inf], np.nan)

    if not MODEL_PATH.exists():
        raise SystemExit(f"Missing model: {MODEL_PATH}. Train first.")

    booster = lgb.Booster(model_file=str(MODEL_PATH))
    # Booster.predict returns class probabilities for multiclass
    proba = booster.predict(X)
    if proba.ndim == 1:
        raise SystemExit("Expected multiclass probability matrix from model.")

    print("Holdout backtest")
    print(f"  rows:     {len(hold):,}")
    print(f"  range:    {hold['open_time'].iloc[0]} -> {hold['open_time'].iloc[-1]}")
    print(f"  horizon:  {meta['horizon_bars']} bars")
    print(f"  barriers: PT={meta['pt_atr_mult']}*ATR  SL={meta['sl_atr_mult']}*ATR")
    print(f"  fee/side: {meta['taker_fee']}")
    print()

    results = []
    best = None
    for thr in THRESHOLDS:
        r = run_backtest(
            hold, proba, thr,
            horizon=int(meta["horizon_bars"]),
            pt_mult=float(meta["pt_atr_mult"]),
            sl_mult=float(meta["sl_atr_mult"]),
            fee=float(meta["taker_fee"]),
        )
        results.append({k: v for k, v in r.items() if k != "trades"})
        print(
            f"conf>={thr:.2f} | trades={r['n_trades']:4d} | "
            f"ret={r['total_return']:+.2%} | win={r['win_rate']:.1%} | "
            f"PF={r['profit_factor']:.2f} | avg={r['avg_return']:+.3%} | "
            f"maxDD={r['max_drawdown']:.1%} | "
            f"L/S={r['longs']}/{r['shorts']}"
        )
        if r["n_trades"] >= 20:
            # prefer higher total return among usable samples; tie-break PF
            score = (r["total_return"], r["profit_factor"])
            if best is None or score > best[0]:
                best = (score, r)

    if best is None:
        # fall back to whatever had the most trades
        cand = max(results, key=lambda x: x["n_trades"])
        print("\nNo threshold produced >=20 trades; showing most-active run.")
        best_run = None
        for thr in THRESHOLDS:
            r = run_backtest(
                hold, proba, thr,
                horizon=int(meta["horizon_bars"]),
                pt_mult=float(meta["pt_atr_mult"]),
                sl_mult=float(meta["sl_atr_mult"]),
                fee=float(meta["taker_fee"]),
            )
            if r["n_trades"] == cand["n_trades"]:
                best_run = r
                break
    else:
        best_run = best[1]

    print("\n" + "=" * 60)
    print(f"SELECTED threshold: {best_run['confidence']:.2f}")
    print(f"  trades:        {best_run['n_trades']}")
    print(f"  total return:  {best_run['total_return']:+.2%}")
    print(f"  win rate:      {best_run['win_rate']:.1%}")
    print(f"  profit factor: {best_run['profit_factor']:.2f}")
    print(f"  avg/trade:     {best_run['avg_return']:+.3%}")
    print(f"  max drawdown:  {best_run['max_drawdown']:.1%}")
    print(f"  longs/shorts:  {best_run['longs']}/{best_run['shorts']}")
    print(f"  exits:         {best_run['exit_reasons']}")
    print("=" * 60)

    # Save trade log for selected run
    trades_path = MODELS_DIR / "holdout_trades.csv"
    pd.DataFrame(best_run["trades"]).to_csv(trades_path, index=False)
    summary = {
        "selected": {k: v for k, v in best_run.items() if k != "trades"},
        "sweep": results,
        "note": (
            "Compounded notional returns, one position at a time, "
            "taker fees both sides, stop-first same-bar rule."
        ),
    }
    summary_path = MODELS_DIR / "holdout_backtest.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved trades  -> {trades_path}")
    print(f"Saved summary -> {summary_path}")


if __name__ == "__main__":
    main()
