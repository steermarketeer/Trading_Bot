"""
HTF daily trend — walk-forward validation + risk rules + stress windows.

Stateless policy: no trade-pattern memory (model_policy.py).

Walk-forward:
  - Train window: pick (exit_sma, stop_pct, use_dd_halt) by train PF
  - Test window: apply chosen params only (no peeking)
  - Roll forward

Risk options tuned on train only:
  - stop_pct: hard daily close stop vs entry (e.g. 0.08 = -8%)
  - dd_halt: pause new entries if equity DD from peak exceeds threshold

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_walkforward.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from model_policy import assert_features_allowed, policy_dict
from strategy_htf_trend import FEE, build_daily, desired_side, load_eth_5m

MODELS_DIR = Path("models")

# Walk-forward geometry (days)
TRAIN_DAYS = 730   # ~2 years
TEST_DAYS = 180    # ~6 months
STEP_DAYS = 180
EMBARGO_DAYS = 5   # gap between train end and test start

EXIT_SMA_GRID = [10, 20, 30]
STOP_PCT_GRID = [None, 0.08, 0.12, 0.15]  # None = no hard stop
DD_HALT_GRID = [None, 0.25]  # pause entries if DD worse than this

STRESS = [
    ("covid_2020", "2020-02-15", "2020-04-30"),
    ("bear_2022_h1", "2022-01-01", "2022-06-30"),
    ("ftx_2022", "2022-11-01", "2022-12-15"),
    ("chop_2024", "2024-01-01", "2024-06-30"),
    ("holdout_2026", "2026-03-26", "2026-09-22"),
]


def prepare_daily(base: pd.DataFrame, exit_sma: int, entry_sma: int = 50) -> pd.DataFrame:
    d = base.copy()
    d["sma_entry"] = d["close"].rolling(entry_sma, min_periods=entry_sma).mean()
    d["sma_exit"] = d["close"].rolling(exit_sma, min_periods=exit_sma).mean()
    d["sma_entry_lag"] = d["sma_entry"].shift(1)
    d["sma_exit_lag"] = d["sma_exit"].shift(1)
    # keep regime_lag / close_lag from build_daily
    return d.dropna(subset=["sma_entry_lag", "sma_exit_lag", "regime_lag", "close_lag"]).reset_index(drop=True)


def run_htf_risk(
    daily: pd.DataFrame,
    *,
    fee: float = FEE,
    stop_pct: float | None = None,
    dd_halt: float | None = None,
) -> dict:
    """
    Same HTF rules but entry uses sma_entry_lag, exit uses sma_exit_lag,
    optional hard stop and DD halt on new entries.
    """
    assert_features_allowed(daily.columns)
    close = daily["close"].to_numpy(float)
    times = daily["open_time"].to_numpy()
    regimes = daily["regime_lag"].astype(str).to_numpy()
    sma_entry = daily["sma_entry_lag"].to_numpy(float)
    sma_exit = daily["sma_exit_lag"].to_numpy(float)
    close_lag = daily["close_lag"].to_numpy(float)

    trades = []
    side = None
    entry_i = None
    entry_px = None

    equity = 1.0
    peak = 1.0
    halted = False

    def maybe_exit(i: int, reason: str) -> None:
        nonlocal side, entry_i, entry_px, equity, peak, halted
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
            "exit_reason": reason,
        })
        equity *= (1.0 + net)
        peak = max(peak, equity)
        if dd_halt is not None and peak > 0:
            dd = (equity - peak) / peak
            if dd <= -abs(dd_halt):
                halted = True
        side = None
        entry_i = None
        entry_px = None

    for i in range(len(daily)):
        # resume halt if equity recovered halfway to peak
        if halted and dd_halt is not None and peak > 0:
            dd = (equity - peak) / peak
            if dd > -0.5 * abs(dd_halt):
                halted = False

        if side is not None:
            # hard stop on close
            if stop_pct is not None:
                if side == "long" and close[i] <= entry_px * (1.0 - stop_pct):
                    maybe_exit(i, "stop")
                    continue
                if side == "short" and close[i] >= entry_px * (1.0 + stop_pct):
                    maybe_exit(i, "stop")
                    continue
            # rule exit
            reg = regimes[i]
            if side == "long" and (reg != "Bull" or close_lag[i] < sma_exit[i]):
                maybe_exit(i, "rule")
                continue
            if side == "short" and (reg != "Bear" or close_lag[i] > sma_exit[i]):
                maybe_exit(i, "rule")
                continue
        else:
            if halted:
                continue
            want = desired_side(regimes[i], close_lag[i], sma_entry[i])
            if want is not None:
                side = want
                entry_i = i
                entry_px = float(close[i])

    if side is not None and entry_i is not None:
        maybe_exit(len(daily) - 1, "eod")

    if not trades:
        return {
            "n_trades": 0, "total_return": 0.0, "win_rate": 0.0,
            "profit_factor": 0.0, "avg_return": 0.0, "max_drawdown": 0.0,
            "longs": 0, "shorts": 0, "avg_days_held": 0.0, "trades": [],
            "final_equity": 1.0,
        }

    tdf = pd.DataFrame(trades)
    rets = tdf["net_return"].to_numpy()
    eq = np.cumprod(1.0 + rets)
    pk = np.maximum.accumulate(eq)
    dd = (eq - pk) / pk
    wins = rets[rets > 0].sum() if (rets > 0).any() else 0.0
    losses = -rets[rets <= 0].sum() if (rets <= 0).any() else 0.0
    pf = (wins / losses) if losses > 0 else 999.0
    return {
        "n_trades": int(len(tdf)),
        "total_return": float(eq[-1] - 1.0),
        "win_rate": float((rets > 0).mean()),
        "profit_factor": float(pf),
        "avg_return": float(rets.mean()),
        "max_drawdown": float(dd.min()),
        "longs": int((tdf["side"] == "long").sum()),
        "shorts": int((tdf["side"] == "short").sum()),
        "avg_days_held": float(tdf["days_held"].mean()),
        "final_equity": float(eq[-1]),
        "trades": trades,
    }


def score_train(r: dict) -> tuple:
    """Higher is better. Require enough trades."""
    if r["n_trades"] < 8:
        return (-999.0, -999.0, 0.0)
    # Prefer PF, then return, then milder DD
    return (r["profit_factor"], r["total_return"], r["max_drawdown"])


def tune_on_train(base_daily: pd.DataFrame, train: pd.DataFrame) -> dict:
    best = None
    best_params = None
    for exit_sma in EXIT_SMA_GRID:
        prepared = prepare_daily(base_daily, exit_sma=exit_sma)
        # align train dates
        tr = prepared[
            (prepared["open_time"] >= train["open_time"].iloc[0]) &
            (prepared["open_time"] <= train["open_time"].iloc[-1])
        ].reset_index(drop=True)
        if len(tr) < 100:
            continue
        for stop in STOP_PCT_GRID:
            for dd_h in DD_HALT_GRID:
                r = run_htf_risk(tr, stop_pct=stop, dd_halt=dd_h)
                sc = score_train(r)
                if best is None or sc > best:
                    best = sc
                    best_params = {
                        "exit_sma": exit_sma,
                        "entry_sma": 50,
                        "stop_pct": stop,
                        "dd_halt": dd_h,
                        "train_pf": r["profit_factor"],
                        "train_ret": r["total_return"],
                        "train_dd": r["max_drawdown"],
                        "train_trades": r["n_trades"],
                    }
    return best_params or {
        "exit_sma": 20, "entry_sma": 50, "stop_pct": None, "dd_halt": None,
        "train_pf": 0.0, "train_ret": 0.0, "train_dd": 0.0, "train_trades": 0,
    }


def eval_params(base_daily: pd.DataFrame, window: pd.DataFrame, params: dict) -> dict:
    prepared = prepare_daily(base_daily, exit_sma=int(params["exit_sma"]))
    part = prepared[
        (prepared["open_time"] >= window["open_time"].iloc[0]) &
        (prepared["open_time"] <= window["open_time"].iloc[-1])
    ].reset_index(drop=True)
    return run_htf_risk(
        part,
        stop_pct=params.get("stop_pct"),
        dd_halt=params.get("dd_halt"),
    )


def walk_forward(base_daily: pd.DataFrame) -> list[dict]:
    folds = []
    t0 = base_daily["open_time"].iloc[0]
    t1 = base_daily["open_time"].iloc[-1]
    train_start = t0
    fold_id = 0
    while True:
        train_end = train_start + pd.Timedelta(days=TRAIN_DAYS)
        test_start = train_end + pd.Timedelta(days=EMBARGO_DAYS)
        test_end = test_start + pd.Timedelta(days=TEST_DAYS)
        if test_end > t1:
            break
        train = base_daily[
            (base_daily["open_time"] >= train_start) & (base_daily["open_time"] <= train_end)
        ].reset_index(drop=True)
        test = base_daily[
            (base_daily["open_time"] >= test_start) & (base_daily["open_time"] <= test_end)
        ].reset_index(drop=True)
        if len(train) < 200 or len(test) < 60:
            train_start = train_start + pd.Timedelta(days=STEP_DAYS)
            continue

        params = tune_on_train(base_daily, train)
        oos = eval_params(base_daily, test, params)
        edge = oos["total_return"] > 0 and oos["profit_factor"] > 1.0 and oos["n_trades"] >= 3
        fold = {
            "fold": fold_id,
            "train_start": str(train_start.date()),
            "train_end": str(train_end.date()),
            "test_start": str(test_start.date()),
            "test_end": str(test_end.date()),
            "params": params,
            "oos_n_trades": oos["n_trades"],
            "oos_return": oos["total_return"],
            "oos_win_rate": oos["win_rate"],
            "oos_pf": oos["profit_factor"],
            "oos_max_dd": oos["max_drawdown"],
            "oos_longs": oos["longs"],
            "oos_shorts": oos["shorts"],
            "oos_has_edge": edge,
        }
        folds.append(fold)
        flag = " EDGE" if edge else ""
        print(
            f"Fold {fold_id:02d} test {fold['test_start']}->{fold['test_end']} | "
            f"params exitSMA={params['exit_sma']} stop={params['stop_pct']} ddHalt={params['dd_halt']} | "
            f"OOS n={oos['n_trades']:2d} ret={oos['total_return']:+7.1%} "
            f"PF={oos['profit_factor']:.2f} DD={oos['max_drawdown']:.1%}{flag}"
        )
        fold_id += 1
        train_start = train_start + pd.Timedelta(days=STEP_DAYS)
    return folds


def stress_fixed(base_daily: pd.DataFrame, params: dict) -> list[dict]:
    rows = []
    for name, start, end in STRESS:
        win = base_daily[
            (base_daily["open_time"] >= pd.Timestamp(start, tz="UTC")) &
            (base_daily["open_time"] <= pd.Timestamp(end, tz="UTC"))
        ].reset_index(drop=True)
        if len(win) < 20:
            continue
        r = eval_params(base_daily, win, params)
        rows.append({
            "stress": name,
            "start": start,
            "end": end,
            "n_trades": r["n_trades"],
            "total_return": r["total_return"],
            "profit_factor": r["profit_factor"],
            "max_drawdown": r["max_drawdown"],
            "win_rate": r["win_rate"],
        })
        print(
            f"Stress {name:14s} | n={r['n_trades']:2d} ret={r['total_return']:+7.1%} "
            f"PF={r['profit_factor']:.2f} DD={r['max_drawdown']:.1%}"
        )
    return rows


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("HTF walk-forward + risk tuning")
    print(f"Policy: {policy_dict()['name']} (stateless, patterns blank)")
    print(f"Train={TRAIN_DAYS}d  Test={TEST_DAYS}d  Step={STEP_DAYS}d  Embargo={EMBARGO_DAYS}d\n")

    eth = load_eth_5m()
    base = build_daily(eth)
    print(f"Daily bars: {len(base):,}  {base['open_time'].iloc[0].date()} -> {base['open_time'].iloc[-1].date()}\n")

    print("--- Walk-forward folds ---")
    folds = walk_forward(base)
    if not folds:
        raise SystemExit("No walk-forward folds produced.")

    n_edge = sum(1 for f in folds if f["oos_has_edge"])
    # Compound OOS fold returns sequentially (approximate WF equity)
    eq = 1.0
    for f in folds:
        eq *= (1.0 + f["oos_return"])
    wf_ret = eq - 1.0
    median_pf = float(np.median([f["oos_pf"] for f in folds]))
    worst_dd = float(min(f["oos_max_dd"] for f in folds))

    print("\n--- Baseline params (exitSMA=20, no stop) on stress ---")
    baseline = {"exit_sma": 20, "entry_sma": 50, "stop_pct": None, "dd_halt": None}
    stress_base = stress_fixed(base, baseline)

    # Most common OOS-chosen params
    from collections import Counter
    key = Counter(
        (f["params"]["exit_sma"], f["params"]["stop_pct"], f["params"]["dd_halt"])
        for f in folds
    ).most_common(1)[0][0]
    common = {"exit_sma": key[0], "entry_sma": 50, "stop_pct": key[1], "dd_halt": key[2]}
    print(f"\n--- Most common train-chosen params {common} on stress ---")
    stress_common = stress_fixed(base, common)

    # Pass criteria (research gate for shadow)
    pass_frac = n_edge / len(folds)
    passed = (
        pass_frac >= 0.5
        and median_pf > 1.0
        and wf_ret > 0
    )

    if passed:
        verdict = (
            f"WALK-FORWARD PASS-ISH: {n_edge}/{len(folds)} folds edged, "
            f"median OOS PF={median_pf:.2f}, compounded OOS ret={wf_ret:+.1%}. "
            "Still high risk — review DD/stress before shadow. No live."
        )
    else:
        verdict = (
            f"WALK-FORWARD FAIL: {n_edge}/{len(folds)} folds edged, "
            f"median OOS PF={median_pf:.2f}, compounded OOS ret={wf_ret:+.1%}. "
            "Do not start shadow/live. Tighten rules or revise hypothesis."
        )

    print("\n" + "=" * 60)
    print(f"Folds: {len(folds)} | edged: {n_edge} ({pass_frac:.0%})")
    print(f"Compounded OOS return: {wf_ret:+.1%}")
    print(f"Median OOS PF: {median_pf:.2f}")
    print(f"Worst fold DD: {worst_dd:.1%}")
    print(f"Research gate: {'PASS' if passed else 'FAIL'}")
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    summary = {
        "strategy": "htf_daily_trend_walkforward",
        "model_policy": policy_dict(),
        "geometry": {
            "train_days": TRAIN_DAYS,
            "test_days": TEST_DAYS,
            "step_days": STEP_DAYS,
            "embargo_days": EMBARGO_DAYS,
        },
        "grids": {
            "exit_sma": EXIT_SMA_GRID,
            "stop_pct": STOP_PCT_GRID,
            "dd_halt": DD_HALT_GRID,
        },
        "folds": folds,
        "n_folds": len(folds),
        "n_edge_folds": n_edge,
        "edge_fraction": pass_frac,
        "compounded_oos_return": wf_ret,
        "median_oos_pf": median_pf,
        "worst_fold_dd": worst_dd,
        "research_gate_passed": passed,
        "most_common_params": common,
        "stress_baseline": stress_base,
        "stress_common_params": stress_common,
        "verdict": verdict,
    }
    (MODELS_DIR / "htf_walkforward_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    pd.DataFrame([
        {k: v for k, v in f.items() if k != "params"} | {
            "exit_sma": f["params"]["exit_sma"],
            "stop_pct": f["params"]["stop_pct"],
            "dd_halt": f["params"]["dd_halt"],
        }
        for f in folds
    ]).to_csv(MODELS_DIR / "htf_walkforward_folds.csv", index=False)
    print(f"\nSaved models/htf_walkforward_summary.json")
    print(f"Saved models/htf_walkforward_folds.csv")


if __name__ == "__main__":
    main()
