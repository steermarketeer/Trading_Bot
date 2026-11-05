"""
Per-coin rule search: each coin gets ITS OWN best combination of the main rules (not ETH's settings).

Candidates per coin (same main-rule detectors as v3; only which filters / thresholds / target are used is searched):
  breakouts: every main-rule breakout on 2h / 4h / 1D with certainty >= 6 (ETH-trained certainty model)
  bounces:   every 1D strong-zone bounce with a confirmation candle, level tested >= 3 times
Options searched (every combination):
  breakouts  timeframes {2h+4h+1D, 4h+1D, 2h+4h} x min certainty {6,7,8} x min stop {0.4,0.6,0.8}% x
             drop the coin's quietest {0,20,40}% (ATR% per timeframe, pre-holdout data) x BTC 4h agrees {any, yes} x
             6h MACD agrees {any, yes} x weekly trend agrees {any, yes} x clean risk zone {any, yes} x
             target {1.5, 2, 2.5, 3}R                                                        = 5,184 combinations
  bounces    level tests >= {3,4,5} x bounce volume >= {0, 0.8, 1.0}x the touch x BTC 4h agrees {any, yes} x
             target {2, 2.5, 3, 4}R                                                          = 72 combinations
Selection (fixed in advance, research = trades 2022-01-01 .. ending before 2025-11-01 only):
  at least 60 trades (breakouts) / 30 (bounces); average R after costs > 0 in at least 3 of the 4 research years;
  then the highest t-score of R after costs (mean / standard error: rewards edge AND sample size).
  If nothing qualifies, that setup is not traded on that coin.
The holdout (Nov 2025 - Oct 2026) is used once, after the choice. Costs / fills / funding as bot/ml/targets.py.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..live.v3 import generate_signals
from ..ml.targets import account, label_paths, _funding_cum, stats
from .coins import COINS, bounce_volume_ratio
from .failure_liquidity import liquidity_features, swing_tables
from .indicators import ema
from .level_tests import tests_for
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
START = pd.Timestamp("2022-01-01")
RES_YEARS = [2022, 2023, 2024, 2025]
B_OPTS = dict(tfs=[("2h", "4h", "1D"), ("4h", "1D"), ("2h", "4h")], cert=[6, 7, 8], stop=[0.004, 0.006, 0.008],
              quiet=[0.0, 0.2, 0.4], btc=[False, True], macd=[False, True], wtrend=[False, True],
              clean=[False, True], T=[1.5, 2.0, 2.5, 3.0])
S_OPTS = dict(tests=[3, 4, 5], vol=[0.0, 0.8, 1.0], btc=[False, True], T=[2.0, 2.5, 3.0, 4.0])
MIN_N = {"breakout": 60, "bounce": 30}
RISK_PCT = {"breakout": 0.03, "bounce": 0.02}


def _btc_side(cfg: Config, times: pd.Series, direction: pd.Series) -> np.ndarray:
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    b4 = resample(btc5, "4h")
    b4["side"] = np.sign(b4["close"] - ema(b4["close"], 20))
    b4["close_time"] = pd.to_datetime(b4["close_time"], utc=True).dt.tz_convert(None).dt.as_unit("ns")
    q = pd.DataFrame({"t": pd.to_datetime(times).dt.as_unit("ns").to_numpy(), "_r": np.arange(len(times))}).sort_values("t")
    m = pd.merge_asof(q, b4[["close_time", "side"]], left_on="t", right_on="close_time", direction="backward").sort_values("_r")
    return m["side"].to_numpy() * direction.to_numpy()


def candidates(cfg: Config, sym: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = replace(cfg, symbol=sym)
    df5u, _ = load_klines_5m(c.data_dir, sym)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    fund = _funding_cum(c)
    # breakouts
    br = generate_signals(c, params_override={"min_certainty": 6}, return_stage="breakouts")
    br = br[br["entry"].notna() & (br["risk"] > 0)].copy()
    br["entry_time"] = pd.to_datetime(br["entry_time"])
    pre = br["entry_time"] < HOLDOUT
    for q in B_OPTS["quiet"]:
        cut = br[pre].groupby("tf")["atr_pct"].quantile(q) if q > 0 else br.groupby("tf")["atr_pct"].min() * 0
        br[f"pass_q{int(q * 100)}"] = br["atr_pct"] >= br["tf"].map(cut)
    br = br[br["entry_time"] >= START].reset_index(drop=True)
    br["decision_time"], br["T"], br["atr_px"] = br["entry_time"], 2.0, br["f_atr_pct"] * br["entry"]
    lq = liquidity_features(br, swing_tables(df5u), df5n)
    br["clean"] = ((lq["liq_in_risk"] == 0) & (lq["pool_near_stop"] == 0)).to_numpy()
    br["wtrend_ok"] = br.get("m_1W_trend", pd.Series(0, index=br.index)) > 0
    lab = label_paths(br, df5n, fund)
    br = pd.concat([br.drop(columns=["stop_pct"]), lab], axis=1)
    br = br[br["ok"].astype(bool)].reset_index(drop=True)
    # bounces
    lt = tests_for(df5u, "1D", live=True)
    lt = lt[lt["stop"].notna() & (lt["test_n"] >= 3)].copy()
    lt["entry_time"] = (pd.to_datetime(lt["time"], utc=True) + pd.Timedelta(days=1)).dt.tz_convert(None)
    lt = lt[lt["entry"].notna()].copy()
    lt["risk"] = (lt["entry"] - lt["stop"]) * lt["direction"]
    lt = lt[(lt["risk"] > 0) & (lt["entry_time"] >= START)].reset_index(drop=True)
    lt["tf"], lt["decision_time"] = "1D", lt["entry_time"]
    lt["vol_ratio"] = bounce_volume_ratio(lt, df5u).to_numpy()
    lt["btc_4h"] = _btc_side(cfg, lt["entry_time"], lt["direction"])
    lab = label_paths(lt, df5n, fund)
    lt = pd.concat([lt.drop(columns=[x for x in lab.columns if x in lt.columns]), lab], axis=1)
    lt = lt[lt["ok"].astype(bool)].reset_index(drop=True)
    for d in (br, lt):
        d["coin"] = sym.replace("USDT", "")
        d["hold"] = d["entry_time"] >= HOLDOUT
        d["year"] = d["entry_time"].dt.year
    return br, lt


def _masks_breakout(b: pd.DataFrame):
    for tfs, cert, stop, q, btc, macd, wt, cl, T in itertools.product(*B_OPTS.values()):
        m = b["tf"].isin(tfs) & (b["certainty"] >= cert) & (b["risk"] / b["px"] >= stop) & b[f"pass_q{int(q * 100)}"]
        if btc:
            m &= b["btc_4h"] > 0
        if macd:
            m &= b["m_6h_macd"] > 0
        if wt:
            m &= b["wtrend_ok"]
        if cl:
            m &= b["clean"]
        name = (f"{'+'.join(tfs)}, certainty>={cert}, stop>={stop:.1%}, drop quietest {q:.0%}"
                + (", BTC 4h agrees" if btc else "") + (", 6h MACD agrees" if macd else "")
                + (", weekly trend agrees" if wt else "") + (", clean risk zone" if cl else "") + f", target {T:g}R")
        yield name, m, T


def _masks_bounce(s: pd.DataFrame):
    for tests, vol, btc, T in itertools.product(*S_OPTS.values()):
        m = (s["test_n"] >= tests) & (s["vol_ratio"].fillna(0) >= vol)
        if btc:
            m &= s["btc_4h"] > 0
        name = (f"level tested >= {tests}x, bounce volume >= {vol:g}x touch" + (", BTC 4h agrees" if btc else "")
                + f", target {T:g}R")
        yield name, m, T


def search(df: pd.DataFrame, kind: str) -> tuple[pd.DataFrame, dict | None]:
    gen = _masks_breakout(df) if kind == "breakout" else _masks_bounce(df)
    rows = []
    for name, m, T in gen:
        net = df[f"net_{T:g}"]
        res = (~df["hold"]) & (df[f"exit_{T:g}"] < HOLDOUT)  # research trades must END before the holdout
        r = net[m & res]
        if len(r) < MIN_N[kind]:
            continue
        yrs = [net[m & res & (df["year"] == y)].mean() for y in RES_YEARS]
        good_years = sum(1 for v in yrs if v == v and v > 0)
        t = r.mean() / (r.std(ddof=1) / math.sqrt(len(r))) if r.std(ddof=1) > 0 else 0.0
        rows.append({"rule": name, "T": T, "n": len(r), "win": float((r > 0).mean()), "avg": float(r.mean()),
                     "t": t, "good_years": good_years, "mask": m})
    R = pd.DataFrame(rows)
    if R.empty:
        return R, None
    ok = R[R["good_years"] >= 3].sort_values("t", ascending=False)
    return R.sort_values("t", ascending=False), (ok.iloc[0].to_dict() if len(ok) else None)


def run_coin_search(cfg: Config, out_dir: Path, coins=COINS) -> Path:
    chosen, cand_store, top_store = [], {}, {}
    for sym in coins:
        print("coin", sym, flush=True)
        br, lt = candidates(cfg, sym)
        cand_store[sym] = (br, lt)
        for kind, df in (("breakout", br), ("bounce", lt)):
            R, best = search(df, kind)
            top_store[(sym, kind)] = R.head(5).drop(columns=["mask"]) if len(R) else R
            if best is None:
                continue
            m, T = best["mask"], best["T"]
            g = df[m].copy()
            g["net"], g["exit_time"] = g[f"net_{T:g}"], g[f"exit_{T:g}"]
            g["setup"], g["rule"] = kind, best["rule"]
            g["stop_pct"] = g["risk"] / g["px"]
            chosen.append(g[["coin", "setup", "rule", "entry_time", "decision_time", "exit_time", "net", "stop_pct",
                             "hold", "year"]].assign(res_t=best["t"], res_avg=best["avg"], res_win=best["win"]))
    C = pd.concat(chosen, ignore_index=True)
    C.to_pickle(ROOT / "results" / "coin_search_trades.pkl")
    pd.to_pickle(top_store, ROOT / "results" / "coin_search_top.pkl")
    wk = {False: (HOLDOUT - START).days / 7, True: (C["entry_time"].max() - HOLDOUT).days / 7}
    risk = {"breakout": RISK_PCT["breakout"], "bounce": RISK_PCT["bounce"]}
    L = ["# Each coin's own best rule combination (searched on 2022 - Oct 2025, tested on the holdout)", "",
         "5,184 breakout and 72 bounce combinations per coin, built only from the main-rule detectors. Chosen by a rule "
         "fixed in advance (enough trades, profitable in >= 3 of 4 research years, best t-score). "
         "**win % = profit after all costs.** The holdout (Nov 2025 - Oct 2026) was not used to choose anything, so "
         "it is the honest result; the research numbers are flattered by the search.", ""]
    rows = []
    for (coin, setup), g in C.groupby(["coin", "setup"], sort=False):
        r = {"coin": coin, "setup": setup, "rule": g["rule"].iloc[0]}
        for hold, k in ((False, "r"), (True, "h")):
            x = g[g["hold"] == hold]
            s_ = stats(x["net"].to_numpy())
            r[f"n_{k}"], r[f"w_{k}"], r[f"a_{k}"] = s_["n"], s_["win"], s_["avg"]
        rows.append(r)
    f2 = lambda v: f"{v:+.2f}"  # noqa: E731
    L += ["## The rule chosen for each coin and setup", "", _table(pd.DataFrame(rows), [
        ("coin", "coin", str), ("setup", "setup", str), ("rule", "chosen combination", str),
        ("n_r", "trades 2022-25", str), ("w_r", "win %", _pct), ("a_r", "avg R", f2),
        ("n_h", "trades holdout", str), ("w_h", "win % holdout", _pct), ("a_h", "avg R holdout", f2)]), ""]
    missing = [f"{s.replace('USDT', '')} {k}" for s in coins for k in ("breakout", "bounce")
               if not ((C["coin"] == s.replace("USDT", "")) & (C["setup"] == k)).any()]
    if missing:
        L += [f"No combination qualified (not traded): {', '.join(missing)}.", ""]
    rows = []
    for coin, g in C.groupby("coin", sort=False):
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
            x = g[g["hold"] == hold].reset_index(drop=True)
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x, "net", "exit_time", risk) if len(x) else (math.nan, math.nan)
            rows.append({"coin": coin, "period": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd})
    for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
        x = C[C["hold"] == hold].reset_index(drop=True)
        s_ = stats(x["net"].to_numpy())
        eq, mdd = account(x, "net", "exit_time", risk)
        rows.append({"coin": "ALL COINS, one account", "period": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd})
    L += ["## Win % per coin (both setups; breakouts 3% risk, bounces 2%, max 5x)", "", _table(pd.DataFrame(rows), [
        ("coin", "coin", str), ("period", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: "" if v != v else f"{v:.2f}x"),
        ("mdd", "worst drop", lambda v: "" if v != v else f"-{v:.0%}")]), ""]
    L += ["## How much the search flatters (top 5 combinations per coin and setup, research only)", ""]
    for (sym, kind), T in top_store.items():
        if len(T):
            L += [f"**{sym.replace('USDT', '')} {kind}**", "", _table(T, [
                ("rule", "combination", str), ("n", "trades", str), ("win", "win %", _pct), ("avg", "avg R", f2),
                ("t", "t-score", lambda v: f"{v:.2f}"), ("good_years", "profitable years (of 4)", str)]), ""]
    path = out_dir / "coin_search.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
