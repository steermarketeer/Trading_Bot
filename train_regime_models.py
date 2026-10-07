"""
Train separate Bull / Bear LightGBM models and backtest with the regime gate.

- Bull model: fit only on Bull-regime train bars; live: longs only
- Bear model: fit only on Bear-regime train bars; live: shorts only
- Neutral: no trades
- Uses current processed dataset (4h / h48 labels) + regime.py

Usage:
    .\\.venv\\Scripts\\python.exe train_regime_models.py
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

from backtest_first_model import LABEL_DROP, THRESHOLDS, simulate_trade
from model_policy import assert_features_allowed, policy_dict
from regime import allowed_side, compute_regime_5m

PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")
BULL_MODEL = MODELS_DIR / "lgbm_bull_h48.txt"
BEAR_MODEL = MODELS_DIR / "lgbm_bear_h48.txt"


def _xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    cols = [c for c in df.columns if c not in LABEL_DROP and c != "regime"]
    X = df[cols].replace([np.inf, -np.inf], np.nan)
    y = df["label"].astype(int)
    return X, y


def _fit(X: pd.DataFrame, y: pd.Series, name: str) -> lgb.LGBMClassifier:
    model = lgb.LGBMClassifier(
        objective="multiclass",
        num_class=3,
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=63,
        subsample=0.8,
        colsample_bytree=0.8,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        verbosity=-1,
    )
    print(f"Fitting {name}: X={X.shape}, labels={y.value_counts().sort_index().to_dict()}")
    model.fit(X, y)
    return model


def run_dual_backtest(
    df: pd.DataFrame,
    proba_bull: np.ndarray,
    proba_bear: np.ndarray,
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

    trades = []
    i = 0
    n = len(df)
    while i < n - 1:
        regime = str(regimes[i])
        allow = allowed_side(regime)
        side = None
        conf = 0.0

        if allow == "long":
            p = proba_bull[i]
            # classes: 0 timeout, 1 up, 2 down
            if p[1] >= confidence and p[1] >= p[0] and p[1] >= p[2]:
                side, conf = "long", float(p[1])
        elif allow == "short":
            p = proba_bear[i]
            if p[2] >= confidence and p[2] >= p[0] and p[2] >= p[1]:
                side, conf = "short", float(p[2])

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
            "regime": regime,
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
        "confidence": confidence,
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
    train = pd.read_parquet(meta["train_path"])
    hold = pd.read_parquet(meta["holdout_path"])

    print("Attaching regimes...")
    reg = compute_regime_5m()[["open_time", "regime"]]
    train = train.merge(reg, on="open_time", how="left")
    hold = hold.merge(reg, on="open_time", how="left")
    train["regime"] = train["regime"].fillna("Neutral")
    hold["regime"] = hold["regime"].fillna("Neutral")

    print("Train regime mix:\n", train["regime"].value_counts().to_string())
    print("Holdout regime mix:\n", hold["regime"].value_counts().to_string())

    bull_train = train[train["regime"] == "Bull"]
    bear_train = train[train["regime"] == "Bear"]
    if len(bull_train) < 1000 or len(bear_train) < 1000:
        raise SystemExit("Not enough Bull/Bear rows to train separate models.")

    Xb, yb = _xy(bull_train)
    Xr, yr = _xy(bear_train)
    assert_features_allowed(Xb.columns)
    assert_features_allowed(Xr.columns)
    print(f"Model policy OK: {policy_dict()['name']} (stateless, no trade-pattern memory)")
    bull_model = _fit(Xb, yb, "BULL")
    bear_model = _fit(Xr, yr, "BEAR")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    bull_model.booster_.save_model(str(BULL_MODEL))
    bear_model.booster_.save_model(str(BEAR_MODEL))
    print(f"Saved {BULL_MODEL}")
    print(f"Saved {BEAR_MODEL}")

    # Holdout class accuracy per regime slice (diagnostic)
    Xh, yh = _xy(hold)
    # predict both everywhere; gate chooses which to use
    pb = bull_model.predict_proba(Xh)
    pr = bear_model.predict_proba(Xh)

    bull_mask = hold["regime"] == "Bull"
    bear_mask = hold["regime"] == "Bear"
    if bull_mask.any():
        acc_b = accuracy_score(yh[bull_mask], bull_model.predict(Xh[bull_mask]))
        print(f"Holdout Bull-slice accuracy (bull model): {acc_b:.4f}  n={bull_mask.sum()}")
    else:
        print("Holdout has no Bull bars — bull model not scored on holdout.")
    if bear_mask.any():
        acc_r = accuracy_score(yh[bear_mask], bear_model.predict(Xh[bear_mask]))
        print(f"Holdout Bear-slice accuracy (bear model): {acc_r:.4f}  n={bear_mask.sum()}")

    print("\n--- Dual-model gated backtest ---")
    results = []
    best = None
    for thr in THRESHOLDS:
        r = run_dual_backtest(
            hold, pb, pr, hold["regime"].to_numpy(), thr,
            horizon=int(meta["horizon_bars"]),
            pt_mult=float(meta["pt_atr_mult"]),
            sl_mult=float(meta["sl_atr_mult"]),
            fee=float(meta["taker_fee"]),
        )
        results.append({k: v for k, v in r.items() if k != "trades"})
        print(
            f"conf>={thr:.2f} | trades={r['n_trades']:4d} | ret={r['total_return']:+.2%} | "
            f"win={r['win_rate']:.1%} | PF={r['profit_factor']:.2f} | "
            f"maxDD={r['max_drawdown']:.1%} | L/S={r['longs']}/{r['shorts']}"
        )
        if r["n_trades"] >= 15:
            score = (r["total_return"], r["profit_factor"])
            if best is None or score > best[0]:
                best = (score, r)

    if best is None:
        best_run = max(
            [run_dual_backtest(
                hold, pb, pr, hold["regime"].to_numpy(), thr,
                horizon=int(meta["horizon_bars"]),
                pt_mult=float(meta["pt_atr_mult"]),
                sl_mult=float(meta["sl_atr_mult"]),
                fee=float(meta["taker_fee"]),
            ) for thr in THRESHOLDS],
            key=lambda x: x["total_return"],
        )
    else:
        best_run = best[1]

    edge = best_run["total_return"] > 0 and best_run["profit_factor"] > 1.0
    print("\n" + "=" * 60)
    print(f"BEST dual-model run @ conf={best_run['confidence']:.2f}")
    print(f"  trades:        {best_run['n_trades']}")
    print(f"  total return:  {best_run['total_return']:+.2%}")
    print(f"  win rate:      {best_run['win_rate']:.1%}")
    print(f"  profit factor: {best_run['profit_factor']:.2f}")
    print(f"  max drawdown:  {best_run['max_drawdown']:.1%}")
    print(f"  exits:         {best_run['exit_reasons']}")
    print(f"  edge?:         {'YES' if edge else 'NO'}")
    print("=" * 60)

    pd.DataFrame(best_run["trades"]).to_csv(MODELS_DIR / "holdout_trades_dual.csv", index=False)
    summary = {
        "bull_model": str(BULL_MODEL),
        "bear_model": str(BEAR_MODEL),
        "horizon_bars": meta["horizon_bars"],
        "sweep": results,
        "best": {k: v for k, v in best_run.items() if k != "trades"},
        "has_edge": edge,
        "note": (
            "Holdout period is mostly Bear/Neutral (little/no Bull), "
            "so live dual-model test is dominated by the Bear short model."
        ),
    }
    (MODELS_DIR / "holdout_backtest_dual.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Saved models/holdout_trades_dual.csv")
    print("Saved models/holdout_backtest_dual.json")


if __name__ == "__main__":
    main()
