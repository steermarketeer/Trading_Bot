"""
New strategy hypothesis (v3): higher-timeframe daily trend hold.

Why: 5m ATR scalp + regime failed across 2019-2026.
Hypothesis: trade WITH weekly regime on the DAILY chart, hold for days,
exit on daily SMA cross or regime flip — few trades, no 5m barrier scalp.

Rules (no ML, no trade-pattern memory):
  Entry (once flat, at daily close):
    - Bull regime + daily close > SMA50  -> long
    - Bear regime + daily close < SMA50  -> short
    - else flat
  Exit:
    - Regime flips to Neutral or opposite, OR
    - Long: daily close < SMA20
    - Short: daily close > SMA20
  Costs: taker fee both sides (no ATR stop in this diagnostic)
  Policy: Stateless — no past-trade features (model_policy.py)

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_trend.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from model_policy import assert_features_allowed, policy_dict
from regime import compute_regime_5m

DATA_DIR = Path("data")
MODELS_DIR = Path("models")
FEE = 0.0004


def load_eth_5m() -> pd.DataFrame:
    path = DATA_DIR / "klines" / "ETHUSDT_5m.csv"
    df = pd.read_csv(path)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df


def build_daily(eth_5m: pd.DataFrame) -> pd.DataFrame:
    x = eth_5m.set_index("open_time")
    d = x.resample("1D", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["close"])
    d = d.reset_index()
    # Use only completed days: drop last incomplete if needed is handled by data end
    d["sma20"] = d["close"].rolling(20, min_periods=20).mean()
    d["sma50"] = d["close"].rolling(50, min_periods=50).mean()
    # Regime from 5m series mapped to daily open (completed HTF already shifted in regime.py)
    reg = compute_regime_5m(eth_5m)[["open_time", "regime"]]
    # take last regime observation of each calendar day
    reg = reg.copy()
    reg["day"] = reg["open_time"].dt.floor("D")
    day_reg = reg.groupby("day", as_index=False).agg(regime=("regime", "last"))
    d["day"] = d["open_time"].dt.floor("D")
    d = d.merge(day_reg, on="day", how="left")
    d["regime"] = d["regime"].fillna("Neutral")
    # Decision uses yesterday's completed SMAs already in row; shift regime by 1 day
    # so we only act on regime known at prior day's close (extra safety)
    d["regime_lag"] = d["regime"].shift(1)
    d["sma20_lag"] = d["sma20"].shift(1)
    d["sma50_lag"] = d["sma50"].shift(1)
    d["close_lag"] = d["close"].shift(1)
    return d.dropna(subset=["sma50_lag", "sma20_lag", "regime_lag"]).reset_index(drop=True)


def desired_side(regime: str, close_lag: float, sma50_lag: float) -> str | None:
    if regime == "Bull" and close_lag > sma50_lag:
        return "long"
    if regime == "Bear" and close_lag < sma50_lag:
        return "short"
    return None


def should_exit(side: str, regime: str, close_lag: float, sma20_lag: float) -> bool:
    if side == "long":
        if regime != "Bull":
            return True
        if close_lag < sma20_lag:
            return True
    if side == "short":
        if regime != "Bear":
            return True
        if close_lag > sma20_lag:
            return True
    return False


def run_htf_backtest(daily: pd.DataFrame, fee: float = FEE) -> dict:
    # Stateless: features are only market columns — assert policy
    assert_features_allowed(daily.columns)

    close = daily["close"].to_numpy(float)
    times = daily["open_time"].to_numpy()
    regimes = daily["regime_lag"].astype(str).to_numpy()
    sma20 = daily["sma20_lag"].to_numpy(float)
    sma50 = daily["sma50_lag"].to_numpy(float)
    close_lag = daily["close_lag"].to_numpy(float)

    trades = []
    side = None
    entry_i = None
    entry_px = None

    for i in range(len(daily)):
        if side is None:
            want = desired_side(regimes[i], close_lag[i], sma50[i])
            if want is not None:
                side = want
                entry_i = i
                entry_px = float(close[i])  # enter at today's close after signal from lag
        else:
            if should_exit(side, regimes[i], close_lag[i], sma20[i]):
                exit_px = float(close[i])
                if side == "long":
                    gross = (exit_px - entry_px) / entry_px
                else:
                    gross = (entry_px - exit_px) / entry_px
                net = gross - 2.0 * fee
                trades.append({
                    "entry_time": str(times[entry_i]),
                    "exit_time": str(times[i]),
                    "side": side,
                    "regime_at_entry": str(regimes[entry_i]),
                    "entry_price": entry_px,
                    "exit_price": exit_px,
                    "days_held": int(i - entry_i),
                    "net_return": net,
                    # Explicitly no pattern/memory fields
                })
                side = None
                entry_i = None
                entry_px = None

    # Force flat at end
    if side is not None and entry_i is not None:
        i = len(daily) - 1
        exit_px = float(close[i])
        if side == "long":
            gross = (exit_px - entry_px) / entry_px
        else:
            gross = (entry_px - exit_px) / entry_px
        net = gross - 2.0 * fee
        trades.append({
            "entry_time": str(times[entry_i]),
            "exit_time": str(times[i]),
            "side": side,
            "regime_at_entry": str(regimes[entry_i]),
            "entry_price": entry_px,
            "exit_price": exit_px,
            "days_held": int(i - entry_i),
            "net_return": net,
        })

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
            "avg_days_held": 0.0,
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
        "avg_days_held": float(tdf["days_held"].mean()),
        "trades": trades,
    }


def slice_period(daily: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    return daily[(daily["open_time"] >= start) & (daily["open_time"] <= end)].reset_index(drop=True)


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("HTF daily trend hypothesis (v3)")
    print(f"Model policy: {policy_dict()['name']} v{policy_dict()['version']}")
    print("  Stateless=True | trade_pattern_memory=False | patterns blank\n")

    eth = load_eth_5m()
    daily = build_daily(eth)
    print(f"Daily bars: {len(daily):,}  {daily['open_time'].iloc[0]} -> {daily['open_time'].iloc[-1]}")

    periods = [
        ("full", str(daily["open_time"].iloc[0].date()), str(daily["open_time"].iloc[-1].date())),
        ("2019-2020", "2019-11-27", "2020-12-31"),
        ("2021", "2021-01-01", "2021-12-31"),
        ("2022", "2022-01-01", "2022-12-31"),
        ("2023", "2023-01-01", "2023-12-31"),
        ("2024", "2024-01-01", "2024-12-31"),
        ("2025", "2025-01-01", "2025-12-31"),
        ("holdout_2026", "2026-03-26", "2026-09-22"),
    ]

    rows = []
    holdout_trades = None
    for name, start, end in periods:
        part = slice_period(daily, start, end + (" 23:59:59+00:00" if "T" not in end else ""))
        # simpler date filter
        part = daily[(daily["open_time"] >= pd.Timestamp(start, tz="UTC")) &
                     (daily["open_time"] <= pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))].reset_index(drop=True)
        if len(part) < 60:
            print(f"{name:14s} | SKIP n={len(part)}")
            continue
        r = run_htf_backtest(part)
        edge = r["total_return"] > 0 and r["profit_factor"] > 1.0 and r["n_trades"] >= 5
        rows.append({
            "period": name,
            "n_days": len(part),
            "n_trades": r["n_trades"],
            "total_return": r["total_return"],
            "win_rate": r["win_rate"],
            "profit_factor": r["profit_factor"],
            "max_drawdown": r["max_drawdown"],
            "avg_days_held": r["avg_days_held"],
            "longs": r["longs"],
            "shorts": r["shorts"],
            "has_edge": edge,
        })
        flag = " EDGE" if edge else ""
        print(
            f"{name:14s} | days={len(part):4d} trades={r['n_trades']:3d} "
            f"ret={r['total_return']:+8.1%} win={r['win_rate']:.1%} "
            f"PF={r['profit_factor']:.2f} DD={r['max_drawdown']:.1%} "
            f"avgHold={r['avg_days_held']:.1f}d L/S={r['longs']}/{r['shorts']}{flag}"
        )
        if name == "holdout_2026":
            holdout_trades = r["trades"]

    edges = [r for r in rows if r["has_edge"]]
    print("\n" + "=" * 60)
    print(f"Periods with edge: {len(edges)} / {len(rows)}")
    if edges:
        verdict = (
            "HTF daily trend shows edge in some windows. "
            "Next: walk-forward + stress years; still no live. ML only later as a filter."
        )
    else:
        verdict = (
            "HTF daily trend also lacks consistent edge under this rule. "
            "Keep searching hypotheses; do not add trade-pattern memory or more ML yet."
        )
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    if holdout_trades is not None:
        pd.DataFrame(holdout_trades).to_csv(MODELS_DIR / "htf_holdout_trades.csv", index=False)

    summary = {
        "strategy": "htf_daily_trend_v3",
        "model_policy": policy_dict(),
        "rules": {
            "entry": "Bull+close>SMA50 long; Bear+close<SMA50 short (lagged daily)",
            "exit": "regime flip/neutral or close vs SMA20 against position",
            "fee_rt": 2 * FEE,
        },
        "periods": rows,
        "n_edge_periods": len(edges),
        "verdict": verdict,
    }
    (MODELS_DIR / "htf_trend_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(MODELS_DIR / "htf_trend_periods.csv", index=False)
    print(f"\nSaved models/htf_trend_summary.json")
    print(f"Saved models/htf_trend_periods.csv")


if __name__ == "__main__":
    main()
