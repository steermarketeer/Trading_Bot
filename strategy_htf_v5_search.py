"""
HTF v5 — find the NEXT walk-forward PASS strategy (not the v4 winner).

Same gate as v4:
  - >=50% OOS folds edged (ret>0, PF>1, n>=3)
  - median OOS PF > 1
  - compounded OOS return > 0

New candidates: long-only family, BTC confirmation, both-side variants
distinct from frozen `both_align_no_stop`.

Stateless / no trade-pattern memory.

Usage:
    .\\.venv\\Scripts\\python.exe strategy_htf_v5_search.py
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from model_policy import assert_features_allowed, policy_dict
from regime import compute_regime_5m
from strategy_htf_trend import FEE, build_daily, load_eth_5m
from strategy_htf_v4_pass import (
    EMBARGO_DAYS,
    STEP_DAYS,
    TEST_DAYS,
    TRAIN_DAYS,
    enrich,
    eval_cfg_walkforward,
    make_folds,
    should_exit,
)

MODELS_DIR = Path("models")
EXISTING_WINNER = "both_align_no_stop"


@dataclass(frozen=True)
class Cfg5:
    name: str
    mode: str  # both | long_only | short_only
    entry_sma: int = 50
    exit_sma: int = 30
    align: bool = True
    regime_stable: int = 5
    stop_pct: float | None = None
    dd_halt: float | None = 0.25
    cooldown: int = 5
    atr_max: float | None = 0.08
    atr_min: float | None = 0.01
    btc_confirm: bool = False  # require BTC trend agree with side


def configs_v5() -> list[Cfg5]:
    return [
        # Known near-misses / variants (re-check)
        Cfg5("align_both_sma30_nostop", "both", exit_sma=30, stop_pct=None, dd_halt=0.20),
        Cfg5("align_both_sma30_stop15", "both", exit_sma=30, stop_pct=0.15, dd_halt=0.20),
        # Long-only family (seek 2nd strategy)
        Cfg5("long_only_sma30_nostop", "long_only", exit_sma=30, stop_pct=None, dd_halt=0.25, cooldown=5),
        Cfg5("long_only_sma30_dd20", "long_only", exit_sma=30, stop_pct=None, dd_halt=0.20, cooldown=5),
        Cfg5("long_only_sma20_nostop", "long_only", exit_sma=20, stop_pct=None, dd_halt=0.25, regime_stable=3),
        Cfg5("long_only_sma50_exit", "long_only", entry_sma=50, exit_sma=50, stop_pct=None, dd_halt=0.25, cooldown=7),
        Cfg5("long_only_vol06", "long_only", exit_sma=30, stop_pct=None, atr_max=0.06, dd_halt=0.25),
        Cfg5("long_only_vol055", "long_only", exit_sma=30, stop_pct=0.15, atr_max=0.055, dd_halt=0.20),
        Cfg5("long_only_stable7", "long_only", exit_sma=30, regime_stable=7, stop_pct=None, dd_halt=0.25),
        # BTC confirmation
        Cfg5("long_btc_confirm", "long_only", exit_sma=30, stop_pct=None, btc_confirm=True, dd_halt=0.25),
        Cfg5("both_btc_confirm", "both", exit_sma=30, stop_pct=None, btc_confirm=True, dd_halt=0.25),
        Cfg5("long_btc_sma20", "long_only", exit_sma=20, stop_pct=None, btc_confirm=True, dd_halt=0.20, regime_stable=3),
        # Short-only strict
        Cfg5("short_only_sma30_nostop", "short_only", exit_sma=30, stop_pct=None, dd_halt=0.20),
        Cfg5("short_btc_confirm", "short_only", exit_sma=30, stop_pct=None, btc_confirm=True, dd_halt=0.20),
        # Both with different risk
        Cfg5("both_sma40_nostop", "both", exit_sma=40, stop_pct=None, dd_halt=0.25, cooldown=7),
        Cfg5("both_cool7_stable7", "both", exit_sma=30, regime_stable=7, cooldown=7, stop_pct=None, dd_halt=0.25),
    ]


def load_btc_5m() -> pd.DataFrame:
    path = Path("data/klines/BTCUSDT_5m.csv")
    df = pd.read_csv(path)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df


def enrich_with_btc(eth_daily: pd.DataFrame) -> pd.DataFrame:
    """Add BTC daily SMA50 lag + BTC regime lag onto ETH daily bars."""
    btc_5m = load_btc_5m()
    btc_d = btc_5m.set_index("open_time").resample("1D", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["close"]).reset_index()
    btc_d["btc_sma50"] = btc_d["close"].rolling(50, min_periods=50).mean()
    btc_d["btc_sma50_lag"] = btc_d["btc_sma50"].shift(1)
    btc_d["btc_close_lag"] = btc_d["close"].shift(1)
    btc_d["day"] = btc_d["open_time"].dt.floor("D")

    # BTC weekly-ish regime via same compute_regime on BTC, mapped to daily
    reg = compute_regime_5m(btc_5m, btc_5m)[["open_time", "regime"]].rename(columns={"regime": "btc_regime"})
    reg["day"] = reg["open_time"].dt.floor("D")
    day_reg = reg.groupby("day", as_index=False).agg(btc_regime=("btc_regime", "last"))
    day_reg["btc_regime_lag"] = day_reg["btc_regime"].shift(1)

    out = eth_daily.copy()
    out["day"] = out["open_time"].dt.floor("D")
    out = out.merge(
        btc_d[["day", "btc_sma50_lag", "btc_close_lag"]],
        on="day",
        how="left",
    )
    out = out.merge(day_reg[["day", "btc_regime_lag"]], on="day", how="left")
    out["btc_regime_lag"] = out["btc_regime_lag"].fillna("Neutral")
    out = out.dropna(subset=["btc_sma50_lag", "btc_close_lag"]).reset_index(drop=True)
    return out


def want_side5(
    cfg: Cfg5,
    regime: str,
    close_lag: float,
    sma_entry: float,
    sma20: float,
    btc_regime: str,
    btc_close_lag: float,
    btc_sma50_lag: float,
) -> str | None:
    if cfg.mode == "long_only" and regime != "Bull":
        return None
    if cfg.mode == "short_only" and regime != "Bear":
        return None

    side = None
    if regime == "Bull" and close_lag > sma_entry:
        if cfg.align and not (sma20 > sma_entry):
            return None
        if cfg.mode in ("both", "long_only"):
            side = "long"
    elif regime == "Bear" and close_lag < sma_entry:
        if cfg.align and not (sma20 < sma_entry):
            return None
        if cfg.mode in ("both", "short_only"):
            side = "short"
    if side is None:
        return None

    if cfg.btc_confirm:
        if side == "long":
            if btc_regime != "Bull" and not (btc_close_lag > btc_sma50_lag):
                return None
            # soft: need at least BTC above SMA50
            if not (btc_close_lag > btc_sma50_lag):
                return None
        if side == "short":
            if not (btc_close_lag < btc_sma50_lag):
                return None
    return side


def run_cfg5(daily: pd.DataFrame, cfg: Cfg5, fee: float = FEE) -> dict:
    assert_features_allowed(daily.columns)
    # Map Cfg5 -> reuse loop (inline, supports BTC)
    entry_col = f"sma{cfg.entry_sma}_lag"
    exit_col = f"sma{cfg.exit_sma}_lag"
    # exit_sma 40 needs column — ensure present
    if exit_col not in daily.columns:
        d = daily.copy()
        d[f"sma{cfg.exit_sma}"] = d["close"].rolling(cfg.exit_sma, min_periods=cfg.exit_sma).mean()
        d[exit_col] = d[f"sma{cfg.exit_sma}"].shift(1)
        daily = d.dropna(subset=[exit_col]).reset_index(drop=True)

    close = daily["close"].to_numpy(float)
    times = daily["open_time"].to_numpy()
    regimes = daily["regime_lag"].astype(str).to_numpy()
    close_lag = daily["close_lag"].to_numpy(float)
    sma_entry = daily[entry_col].to_numpy(float)
    sma_exit = daily[exit_col].to_numpy(float)
    sma20 = daily["sma20_lag"].to_numpy(float)
    atr_pct = daily["atr_pct_lag"].to_numpy(float)
    stable = daily["regime_stable_days"].to_numpy(int)
    btc_reg = daily["btc_regime_lag"].astype(str).to_numpy() if "btc_regime_lag" in daily.columns else np.array(["Neutral"] * len(daily))
    btc_cl = daily["btc_close_lag"].to_numpy(float) if "btc_close_lag" in daily.columns else close_lag
    btc_sma = daily["btc_sma50_lag"].to_numpy(float) if "btc_sma50_lag" in daily.columns else sma_entry

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
            w = want_side5(
                cfg, regimes[i], close_lag[i], sma_entry[i], sma20[i],
                btc_reg[i], btc_cl[i], btc_sma[i],
            )
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


def eval_wf(daily: pd.DataFrame, cfg: Cfg5, folds) -> dict:
    oos_rows = []
    eq = 1.0
    for i, (tr_s, tr_e, te_s, te_e) in enumerate(folds):
        test = daily[(daily["open_time"] >= te_s) & (daily["open_time"] <= te_e)].reset_index(drop=True)
        if len(test) < 40:
            continue
        r = run_cfg5(test, cfg)
        edge = r["total_return"] > 0 and r["profit_factor"] > 1.0 and r["n_trades"] >= 3
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
        return {"cfg": cfg.name, "n_folds": 0, "pass": False, "edge_frac": 0, "compounded_oos_ret": 0, "median_pf": 0, "n_edge": 0, "worst_dd": 0}
    n_edge = sum(1 for x in oos_rows if x["edge"])
    median_pf = float(np.median([x["pf"] for x in oos_rows]))
    wf_ret = eq - 1.0
    frac = n_edge / len(oos_rows)
    return {
        "cfg": cfg.name,
        "params": asdict(cfg),
        "n_folds": len(oos_rows),
        "n_edge": n_edge,
        "edge_frac": frac,
        "median_pf": median_pf,
        "compounded_oos_ret": wf_ret,
        "worst_dd": float(min(x["dd"] for x in oos_rows)),
        "pass": frac >= 0.5 and median_pf > 1.0 and wf_ret > 0,
        "folds": oos_rows,
    }


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("HTF v5 — search NEXT walk-forward PASS (exclude existing winner)")
    print(f"Existing winner to beat/complement: {EXISTING_WINNER}")
    print(f"Policy: {policy_dict()['name']}\n")

    eth = enrich(build_daily(load_eth_5m()))
    daily = enrich_with_btc(eth)
    # ensure sma40 for one config
    if "sma40_lag" not in daily.columns:
        daily["sma40"] = daily["close"].rolling(40, min_periods=40).mean()
        daily["sma40_lag"] = daily["sma40"].shift(1)
        daily = daily.dropna(subset=["sma40_lag"]).reset_index(drop=True)

    folds = make_folds(daily)
    print(f"Daily bars: {len(daily):,}  folds: {len(folds)}\n")

    results = []
    for cfg in configs_v5():
        res = eval_wf(daily, cfg, folds)
        results.append(res)
        flag = " PASS" if res["pass"] else ""
        print(
            f"{cfg.name:28s} | edged={res['n_edge']}/{res['n_folds']} "
            f"({res['edge_frac']:.0%}) | OOS ret={res['compounded_oos_ret']:+7.1%} "
            f"medPF={res['median_pf']:.2f} worstDD={res['worst_dd']:.1%}{flag}"
        )

    # New PASSes only (name != existing winner; winner wasn't in this list anyway)
    passed = [r for r in results if r.get("pass")]
    print("\n" + "=" * 60)
    if passed:
        winner = max(passed, key=lambda r: (r["compounded_oos_ret"], r["median_pf"], r["edge_frac"]))
        print(f"NEW PASS WINNER: {winner['cfg']}")
        print(
            f"  edged={winner['n_edge']}/{winner['n_folds']} "
            f"OOS={winner['compounded_oos_ret']:+.1%} medPF={winner['median_pf']:.2f} "
            f"worstDD={winner['worst_dd']:.1%}"
        )
        verdict = (
            f"Found next WF-PASS strategy '{winner['cfg']}'. "
            "Keep shadow on v4 for now; optionally add this as strategy #2 later."
        )
        gate = "PASS"
        # freeze
        freeze = {
            "status": "WALK_FORWARD_PASS",
            "role": "strategy_2_candidate",
            "complements": EXISTING_WINNER,
            "winner": winner["params"],
            "walkforward": {
                "edged": f"{winner['n_edge']}/{winner['n_folds']}",
                "compounded_oos_ret": winner["compounded_oos_ret"],
                "median_pf": winner["median_pf"],
                "worst_dd": winner["worst_dd"],
            },
            "folds": winner["folds"],
            "model_policy": policy_dict(),
            "note": "Second PASS strategy. Stateless. Not wired into shadow yet.",
        }
        (MODELS_DIR / "htf_v5_winner.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
        print(f"Frozen -> models/htf_v5_winner.json")
    else:
        best = max(results, key=lambda r: (r.get("pass", False), r["compounded_oos_ret"], r["median_pf"], r["edge_frac"]))
        winner = best
        gate = "FAIL"
        verdict = (
            f"No new PASS. Best effort '{best['cfg']}' "
            f"edged={best['n_edge']}/{best['n_folds']} OOS={best['compounded_oos_ret']:+.1%} "
            f"medPF={best['median_pf']:.2f}."
        )
        print(verdict)

    print(f"Research gate: {gate}")
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    out = {
        "strategy": "htf_v5_next_pass_search",
        "existing_winner": EXISTING_WINNER,
        "gate": gate,
        "verdict": verdict,
        "winner": {k: v for k, v in winner.items() if k != "folds"},
        "all": [{k: v for k, v in r.items() if k != "folds"} for r in results],
        "n_pass": len(passed),
    }
    (MODELS_DIR / "htf_v5_search_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("folds", "params")} for r in results]).to_csv(
        MODELS_DIR / "htf_v5_leaderboard.csv", index=False
    )
    print("Saved models/htf_v5_search_summary.json")
    print("Saved models/htf_v5_leaderboard.csv")


if __name__ == "__main__":
    main()
