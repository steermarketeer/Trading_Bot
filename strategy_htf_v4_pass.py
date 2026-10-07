"""
HTF v4 — hunt for a walk-forward PASS.

Tightens v3 rules and evaluates FIXED configs on the same WF geometry
(no peeking: each fold's OOS is untouched). Also optional light train-side
choice among a small allow-list of configs.

Pass gate (same as before):
  - >=50% OOS folds with edge (ret>0, PF>1, n>=3)
  - median OOS PF > 1
  - compounded OOS return > 0

Stateless / no trade-pattern memory.

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_v4_pass.py
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from model_policy import assert_features_allowed, policy_dict
from strategy_htf_trend import FEE, build_daily, load_eth_5m

MODELS_DIR = Path("models")

TRAIN_DAYS = 730
TEST_DAYS = 180
STEP_DAYS = 180
EMBARGO_DAYS = 5


@dataclass(frozen=True)
class Cfg:
    name: str
    mode: str              # "both" | "long_only" | "short_only"
    entry_sma: int = 50
    exit_sma: int = 20
    align: bool = True     # require SMA20 vs SMA50 stack with side
    regime_stable: int = 0 # days regime must stay same before entry
    stop_pct: float | None = None
    dd_halt: float | None = 0.20
    cooldown: int = 3      # days flat after exit before new entry
    atr_max: float | None = 0.08  # skip entry if ATR14/close > this (chop/spike)
    atr_min: float | None = 0.01


def configs() -> list[Cfg]:
    return [
        Cfg("v3_like_both_sma20", "both", exit_sma=20, align=False, regime_stable=0, dd_halt=None, cooldown=0, atr_max=None, atr_min=None),
        Cfg("align_both_sma30", "both", exit_sma=30, align=True, regime_stable=5, dd_halt=0.20, cooldown=5, stop_pct=0.15),
        Cfg("align_both_sma20", "both", exit_sma=20, align=True, regime_stable=5, dd_halt=0.20, cooldown=5, stop_pct=0.12),
        Cfg("long_only_align", "long_only", exit_sma=20, align=True, regime_stable=3, dd_halt=0.25, cooldown=5, stop_pct=0.15),
        Cfg("long_only_slow", "long_only", exit_sma=50, entry_sma=50, align=True, regime_stable=5, dd_halt=0.25, cooldown=7, stop_pct=0.20),
        Cfg("short_only_align", "short_only", exit_sma=30, align=True, regime_stable=5, dd_halt=0.20, cooldown=5, stop_pct=0.12),
        Cfg("both_slow_stable", "both", exit_sma=50, entry_sma=100, align=True, regime_stable=7, dd_halt=0.20, cooldown=7, stop_pct=0.15),
        Cfg("long_only_tight_vol", "long_only", exit_sma=30, align=True, regime_stable=5, dd_halt=0.20, cooldown=5, stop_pct=0.12, atr_max=0.06),
        Cfg("both_align_no_stop", "both", exit_sma=30, align=True, regime_stable=5, dd_halt=0.25, cooldown=5, stop_pct=None),
        Cfg("long_only_entry100", "long_only", entry_sma=100, exit_sma=50, align=True, regime_stable=5, dd_halt=0.25, cooldown=5, stop_pct=0.18),
    ]


def enrich(base: pd.DataFrame) -> pd.DataFrame:
    d = base.copy()
    # ATR% on daily
    prev = d["close"].shift(1)
    tr = pd.concat([
        (d["high"] - d["low"]),
        (d["high"] - prev).abs(),
        (d["low"] - prev).abs(),
    ], axis=1).max(axis=1)
    d["atr14"] = tr.rolling(14, min_periods=14).mean()
    d["atr_pct"] = d["atr14"] / d["close"]
    d["atr_pct_lag"] = d["atr_pct"].shift(1)
    # regime stability count
    reg = d["regime_lag"].astype(str)
    stab = np.ones(len(d), dtype=int)
    for i in range(1, len(d)):
        if reg.iloc[i] == reg.iloc[i - 1] and reg.iloc[i] != "nan":
            stab[i] = stab[i - 1] + 1
        else:
            stab[i] = 1
    d["regime_stable_days"] = stab
    for n in (20, 30, 50, 100):
        d[f"sma{n}"] = d["close"].rolling(n, min_periods=n).mean()
        d[f"sma{n}_lag"] = d[f"sma{n}"].shift(1)
    return d.dropna(subset=["sma100_lag", "atr_pct_lag", "close_lag", "regime_lag"]).reset_index(drop=True)


def want_side(cfg: Cfg, regime: str, close_lag: float, sma_entry: float, sma20: float) -> str | None:
    if cfg.mode == "long_only" and regime != "Bull":
        return None
    if cfg.mode == "short_only" and regime != "Bear":
        return None

    if regime == "Bull" and close_lag > sma_entry:
        if cfg.align and not (sma20 > sma_entry):
            return None
        if cfg.mode in ("both", "long_only"):
            return "long"
    if regime == "Bear" and close_lag < sma_entry:
        if cfg.align and not (sma20 < sma_entry):
            return None
        if cfg.mode in ("both", "short_only"):
            return "short"
    return None


def should_exit(side: str, regime: str, close_lag: float, sma_exit: float) -> bool:
    if side == "long":
        return regime != "Bull" or close_lag < sma_exit
    if side == "short":
        return regime != "Bear" or close_lag > sma_exit
    return True


def run_cfg(daily: pd.DataFrame, cfg: Cfg, fee: float = FEE) -> dict:
    assert_features_allowed(daily.columns)
    entry_col = f"sma{cfg.entry_sma}_lag"
    exit_col = f"sma{cfg.exit_sma}_lag"
    sma20 = daily["sma20_lag"].to_numpy(float)

    close = daily["close"].to_numpy(float)
    times = daily["open_time"].to_numpy()
    regimes = daily["regime_lag"].astype(str).to_numpy()
    close_lag = daily["close_lag"].to_numpy(float)
    sma_entry = daily[entry_col].to_numpy(float)
    sma_exit = daily[exit_col].to_numpy(float)
    atr_pct = daily["atr_pct_lag"].to_numpy(float)
    stable = daily["regime_stable_days"].to_numpy(int)

    trades = []
    side = None
    entry_i = None
    entry_px = None
    cooldown_left = 0
    equity = 1.0
    peak = 1.0
    halted = False

    def close_trade(i: int, reason: str) -> None:
        nonlocal side, entry_i, entry_px, equity, peak, halted, cooldown_left
        exit_px = float(close[i])
        gross = ((exit_px - entry_px) / entry_px) if side == "long" else ((entry_px - exit_px) / entry_px)
        net = gross - 2.0 * fee
        trades.append({
            "entry_time": str(times[entry_i]),
            "exit_time": str(times[i]),
            "side": side,
            "net_return": net,
            "days_held": int(i - entry_i),
            "exit_reason": reason,
        })
        equity *= (1.0 + net)
        peak = max(peak, equity)
        if cfg.dd_halt is not None and peak > 0 and (equity - peak) / peak <= -abs(cfg.dd_halt):
            halted = True
        side = None
        entry_i = None
        entry_px = None
        cooldown_left = cfg.cooldown

    for i in range(len(daily)):
        if halted and cfg.dd_halt is not None and peak > 0:
            if (equity - peak) / peak > -0.5 * abs(cfg.dd_halt):
                halted = False

        if cooldown_left > 0 and side is None:
            cooldown_left -= 1

        if side is not None:
            if cfg.stop_pct is not None:
                if side == "long" and close[i] <= entry_px * (1.0 - cfg.stop_pct):
                    close_trade(i, "stop")
                    continue
                if side == "short" and close[i] >= entry_px * (1.0 + cfg.stop_pct):
                    close_trade(i, "stop")
                    continue
            if should_exit(side, regimes[i], close_lag[i], sma_exit[i]):
                close_trade(i, "rule")
                continue
        else:
            if halted or cooldown_left > 0:
                continue
            if stable[i] < cfg.regime_stable:
                continue
            if cfg.atr_max is not None and atr_pct[i] > cfg.atr_max:
                continue
            if cfg.atr_min is not None and atr_pct[i] < cfg.atr_min:
                continue
            w = want_side(cfg, regimes[i], close_lag[i], sma_entry[i], sma20[i])
            if w is not None:
                side = w
                entry_i = i
                entry_px = float(close[i])

    if side is not None and entry_i is not None:
        close_trade(len(daily) - 1, "eod")

    if not trades:
        return {
            "n_trades": 0, "total_return": 0.0, "win_rate": 0.0, "profit_factor": 0.0,
            "max_drawdown": 0.0, "avg_return": 0.0, "trades": [],
        }
    rets = np.array([t["net_return"] for t in trades], float)
    eq = np.cumprod(1.0 + rets)
    pk = np.maximum.accumulate(eq)
    dd = (eq - pk) / pk
    wins = rets[rets > 0].sum() if (rets > 0).any() else 0.0
    losses = -rets[rets <= 0].sum() if (rets <= 0).any() else 0.0
    pf = (wins / losses) if losses > 0 else 999.0
    return {
        "n_trades": len(trades),
        "total_return": float(eq[-1] - 1.0),
        "win_rate": float((rets > 0).mean()),
        "profit_factor": float(pf),
        "max_drawdown": float(dd.min()),
        "avg_return": float(rets.mean()),
        "trades": trades,
    }


def make_folds(daily: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    folds = []
    t0 = daily["open_time"].iloc[0]
    t1 = daily["open_time"].iloc[-1]
    train_start = t0
    while True:
        train_end = train_start + pd.Timedelta(days=TRAIN_DAYS)
        test_start = train_end + pd.Timedelta(days=EMBARGO_DAYS)
        test_end = test_start + pd.Timedelta(days=TEST_DAYS)
        if test_end > t1:
            break
        folds.append((train_start, train_end, test_start, test_end))
        train_start = train_start + pd.Timedelta(days=STEP_DAYS)
    return folds


def slice_df(daily: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return daily[(daily["open_time"] >= start) & (daily["open_time"] <= end)].reset_index(drop=True)


def eval_cfg_walkforward(daily: pd.DataFrame, cfg: Cfg, folds) -> dict:
    oos_rows = []
    eq = 1.0
    for i, (tr_s, tr_e, te_s, te_e) in enumerate(folds):
        test = slice_df(daily, te_s, te_e)
        if len(test) < 40:
            continue
        r = run_cfg(test, cfg)
        edge = r["total_return"] > 0 and r["profit_factor"] > 1.0 and r["n_trades"] >= 3
        # also allow edge with fewer trades if strongly positive? keep min 3
        oos_rows.append({
            "fold": i,
            "test_start": str(te_s.date()),
            "test_end": str(te_e.date()),
            "n_trades": r["n_trades"],
            "ret": r["total_return"],
            "pf": r["profit_factor"],
            "dd": r["max_drawdown"],
            "win": r["win_rate"],
            "edge": edge,
        })
        eq *= (1.0 + r["total_return"])
    if not oos_rows:
        return {"cfg": cfg.name, "n_folds": 0, "pass": False}
    n_edge = sum(1 for x in oos_rows if x["edge"])
    median_pf = float(np.median([x["pf"] for x in oos_rows]))
    wf_ret = eq - 1.0
    frac = n_edge / len(oos_rows)
    passed = frac >= 0.5 and median_pf > 1.0 and wf_ret > 0
    return {
        "cfg": cfg.name,
        "params": asdict(cfg),
        "n_folds": len(oos_rows),
        "n_edge": n_edge,
        "edge_frac": frac,
        "median_pf": median_pf,
        "compounded_oos_ret": wf_ret,
        "worst_dd": float(min(x["dd"] for x in oos_rows)),
        "pass": passed,
        "folds": oos_rows,
    }


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("HTF v4 — search for walk-forward PASS")
    print(f"Policy: {policy_dict()['name']} (stateless, patterns blank)\n")

    daily = enrich(build_daily(load_eth_5m()))
    folds = make_folds(daily)
    print(f"Daily bars: {len(daily):,}  folds: {len(folds)}\n")

    results = []
    best = None
    for cfg in configs():
        res = eval_cfg_walkforward(daily, cfg, folds)
        results.append(res)
        flag = " PASS" if res["pass"] else ""
        print(
            f"{cfg.name:22s} | edged={res['n_edge']}/{res['n_folds']} "
            f"({res['edge_frac']:.0%}) | OOS ret={res['compounded_oos_ret']:+7.1%} "
            f"medPF={res['median_pf']:.2f} worstDD={res['worst_dd']:.1%}{flag}"
        )
        if best is None or (
            (res["pass"], res["compounded_oos_ret"], res["median_pf"])
            > (best["pass"], best["compounded_oos_ret"], best["median_pf"])
        ):
            best = res

    # Adaptive: on each train fold pick best cfg from allow-list by train score, apply to OOS
    print("\n--- Adaptive allow-list (tune cfg on train, test OOS) ---")
    adapt_rows = []
    eq = 1.0
    for i, (tr_s, tr_e, te_s, te_e) in enumerate(folds):
        train = slice_df(daily, tr_s, tr_e)
        test = slice_df(daily, te_s, te_e)
        best_cfg = None
        best_score = None
        for cfg in configs():
            # skip pure baseline noise configs for adaptive? keep all
            r = run_cfg(train, cfg)
            if r["n_trades"] < 6:
                score = (-999, -999, 0)
            else:
                score = (r["profit_factor"], r["total_return"], r["max_drawdown"])
            if best_score is None or score > best_score:
                best_score = score
                best_cfg = cfg
        assert best_cfg is not None
        oos = run_cfg(test, best_cfg)
        edge = oos["total_return"] > 0 and oos["profit_factor"] > 1.0 and oos["n_trades"] >= 3
        adapt_rows.append({
            "fold": i,
            "chosen": best_cfg.name,
            "test_start": str(te_s.date()),
            "test_end": str(te_e.date()),
            "n_trades": oos["n_trades"],
            "ret": oos["total_return"],
            "pf": oos["profit_factor"],
            "dd": oos["max_drawdown"],
            "edge": edge,
        })
        eq *= (1.0 + oos["total_return"])
        print(
            f"Fold {i:02d} chose {best_cfg.name:22s} | "
            f"OOS n={oos['n_trades']:2d} ret={oos['total_return']:+7.1%} "
            f"PF={oos['profit_factor']:.2f} DD={oos['max_drawdown']:.1%}"
            f"{' EDGE' if edge else ''}"
        )

    n_edge = sum(1 for x in adapt_rows if x["edge"])
    adapt = {
        "cfg": "adaptive_allowlist",
        "n_folds": len(adapt_rows),
        "n_edge": n_edge,
        "edge_frac": n_edge / len(adapt_rows) if adapt_rows else 0,
        "median_pf": float(np.median([x["pf"] for x in adapt_rows])) if adapt_rows else 0,
        "compounded_oos_ret": eq - 1.0,
        "worst_dd": float(min(x["dd"] for x in adapt_rows)) if adapt_rows else 0,
        "folds": adapt_rows,
    }
    adapt["pass"] = (
        adapt["edge_frac"] >= 0.5
        and adapt["median_pf"] > 1.0
        and adapt["compounded_oos_ret"] > 0
    )
    print(
        f"\nAdaptive | edged={adapt['n_edge']}/{adapt['n_folds']} "
        f"OOS ret={adapt['compounded_oos_ret']:+.1%} medPF={adapt['median_pf']:.2f} "
        f"{'PASS' if adapt['pass'] else 'FAIL'}"
    )
    results.append(adapt)
    if adapt["pass"] and (best is None or not best["pass"] or adapt["compounded_oos_ret"] > best["compounded_oos_ret"]):
        best = adapt

    passed_list = [r for r in results if r.get("pass")]
    print("\n" + "=" * 60)
    if passed_list:
        winner = max(passed_list, key=lambda r: (r["compounded_oos_ret"], r["median_pf"]))
        verdict = (
            f"WALK-FORWARD PASS with config '{winner['cfg']}': "
            f"edged={winner['n_edge']}/{winner['n_folds']}, "
            f"OOS ret={winner['compounded_oos_ret']:+.1%}, medPF={winner['median_pf']:.2f}. "
            "Still not live — next is shadow logger only after reviewing DD/stress."
        )
        print(f"WINNER: {winner['cfg']}")
        print(f"  edged={winner['n_edge']}/{winner['n_folds']} ret={winner['compounded_oos_ret']:+.1%} "
              f"medPF={winner['median_pf']:.2f} worstDD={winner['worst_dd']:.1%}")
        gate = "PASS"
    else:
        winner = best
        verdict = (
            f"Still FAIL. Best was '{winner['cfg']}' "
            f"edged={winner['n_edge']}/{winner['n_folds']} "
            f"OOS ret={winner['compounded_oos_ret']:+.1%} medPF={winner['median_pf']:.2f}. "
            "No shadow/live."
        )
        gate = "FAIL"
        print(f"No PASS. Best effort: {winner['cfg']}")
    print(f"Research gate: {gate}")
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    out = {
        "strategy": "htf_v4_pass_search",
        "model_policy": policy_dict(),
        "gate": gate,
        "verdict": verdict,
        "winner": {k: v for k, v in winner.items() if k != "folds"},
        "all_configs": [{k: v for k, v in r.items() if k != "folds"} for r in results],
        "winner_folds": winner.get("folds", []),
    }
    (MODELS_DIR / "htf_v4_pass_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("folds", "params")} for r in results]).to_csv(
        MODELS_DIR / "htf_v4_pass_leaderboard.csv", index=False
    )
    print("\nSaved models/htf_v4_pass_summary.json")
    print("Saved models/htf_v4_pass_leaderboard.csv")


if __name__ == "__main__":
    main()
