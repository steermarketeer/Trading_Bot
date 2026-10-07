"""
Holdout backtest with optional Bull/Bear/Neutral regime gate.

Compares:
  A) No gate (original)
  B) Gate on: Bull->longs only, Bear->shorts only, Neutral->flat

Usage:
    .\\.venv\\Scripts\\python.exe backtest_with_regime.py
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from backtest_first_model import LABEL_DROP, THRESHOLDS, run_backtest, simulate_trade
from regime import allowed_side, compute_regime_5m

PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")
MODEL_PATH = MODELS_DIR / "lgbm_5m_h48_v2.txt"


def run_backtest_gated(
    df: pd.DataFrame,
    proba: np.ndarray,
    regimes: np.ndarray,
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
    blocked = 0
    i = 0
    n = len(df)
    while i < n - 1:
        allow = allowed_side(str(regimes[i]))
        side = None
        conf = 0.0

        if allow == "long":
            if p_up[i] >= confidence and p_up[i] >= p_down[i] and p_up[i] >= p_timeout[i]:
                side, conf = "long", float(p_up[i])
            elif p_down[i] >= confidence:
                blocked += 1  # short signal killed by Bull gate
        elif allow == "short":
            if p_down[i] >= confidence and p_down[i] >= p_up[i] and p_down[i] >= p_timeout[i]:
                side, conf = "short", float(p_down[i])
            elif p_up[i] >= confidence:
                blocked += 1
        else:
            # Neutral: any directional fire is blocked
            if p_up[i] >= confidence or p_down[i] >= confidence:
                blocked += 1

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
            "regime": str(regimes[i]),
            "confidence": conf,
            "net_return": net,
            "bars_held": held,
            "exit_reason": reason,
            "entry_price": float(close[i]),
        })
        i += held + 1

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
            "blocked_signals": blocked,
            "exit_reasons": {},
            "regime_counts": {},
            "trades": [],
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
        "blocked_signals": blocked,
        "exit_reasons": tdf["exit_reason"].value_counts().to_dict(),
        "regime_counts": tdf["regime"].value_counts().to_dict(),
        "trades": trades,
    }


def _print_row(tag: str, r: dict) -> None:
    print(
        f"{tag} conf>={r['confidence']:.2f} | trades={r['n_trades']:4d} | "
        f"ret={r['total_return']:+.2%} | win={r['win_rate']:.1%} | "
        f"PF={r['profit_factor']:.2f} | maxDD={r['max_drawdown']:.1%} | "
        f"L/S={r['longs']}/{r['shorts']}"
        + (f" | blocked={r.get('blocked_signals', 0)}" if "blocked_signals" in r else "")
    )


def main() -> None:
    meta = json.loads((PROCESSED / "dataset_meta.json").read_text(encoding="utf-8"))
    hold = pd.read_parquet(meta["holdout_path"])
    feat_cols = [c for c in hold.columns if c not in LABEL_DROP]
    X = hold[feat_cols].replace([np.inf, -np.inf], np.nan)

    print("Computing regime series...")
    regime_df = compute_regime_5m()
    hold = hold.merge(regime_df[["open_time", "regime"]], on="open_time", how="left")
    hold["regime"] = hold["regime"].fillna("Neutral")
    print("Holdout regime mix:")
    print(hold["regime"].value_counts().to_string())
    print()

    booster = lgb.Booster(model_file=str(MODEL_PATH))
    proba = booster.predict(X)
    regimes = hold["regime"].to_numpy()

    horizon = int(meta["horizon_bars"])
    pt = float(meta["pt_atr_mult"])
    sl = float(meta["sl_atr_mult"])
    fee = float(meta["taker_fee"])

    print("--- A) NO regime gate ---")
    no_gate = []
    for thr in THRESHOLDS:
        r = run_backtest(hold, proba, thr, horizon, pt, sl, fee)
        no_gate.append({k: v for k, v in r.items() if k != "trades"})
        _print_row("A", r)

    print("\n--- B) WITH regime gate ---")
    gated = []
    best_gated = None
    for thr in THRESHOLDS:
        r = run_backtest_gated(hold, proba, regimes, thr, horizon, pt, sl, fee)
        gated.append({k: v for k, v in r.items() if k != "trades"})
        _print_row("B", r)
        if r["n_trades"] >= 15:
            score = (r["total_return"], r["profit_factor"])
            if best_gated is None or score > best_gated[0]:
                best_gated = (score, r)

    if best_gated is None:
        # pick least-bad by total return among all
        full = []
        for thr in THRESHOLDS:
            full.append(run_backtest_gated(hold, proba, regimes, thr, horizon, pt, sl, fee))
        best_run = max(full, key=lambda x: x["total_return"])
    else:
        best_run = best_gated[1]

    print("\n" + "=" * 60)
    print(f"BEST gated run @ conf={best_run['confidence']:.2f}")
    print(f"  trades:        {best_run['n_trades']}")
    print(f"  total return:  {best_run['total_return']:+.2%}")
    print(f"  win rate:      {best_run['win_rate']:.1%}")
    print(f"  profit factor: {best_run['profit_factor']:.2f}")
    print(f"  max drawdown:  {best_run['max_drawdown']:.1%}")
    print(f"  blocked:       {best_run['blocked_signals']}")
    print(f"  regimes used:  {best_run.get('regime_counts', {})}")
    print(f"  exits:         {best_run['exit_reasons']}")
    edge = best_run["total_return"] > 0 and best_run["profit_factor"] > 1.0
    print(f"  edge?:         {'YES' if edge else 'NO — proceed to longer horizon'}")
    print("=" * 60)

    pd.DataFrame(best_run["trades"]).to_csv(MODELS_DIR / "holdout_trades_gated.csv", index=False)
    summary = {
        "no_gate": no_gate,
        "gated": gated,
        "best_gated": {k: v for k, v in best_run.items() if k != "trades"},
        "has_edge": edge,
        "next_step": "done" if edge else "longer_horizon_retrain",
    }
    (MODELS_DIR / "holdout_backtest_gated.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\nSaved models/holdout_trades_gated.csv")
    print(f"Saved models/holdout_backtest_gated.json")


if __name__ == "__main__":
    main()
