"""
v3.1 on more coins: the ETH rules and the ETH-trained certainty models, FROZEN and unchanged (bot/live/v3.py),
applied to BTC / SOL / BNB / XRP / DOGE. Nothing was fitted on these coins, so every one of their trades is
out-of-sample (for ETH only the holdout is).
v3.1 = v3 + skip 1D bounces whose confirmation-candle volume is < 0.8x the touch candle's.
Replay on 5m candles with each coin's own funding; costs as bot/ml/targets.py (market entry, limit target that must
trade 0.02% through, market stop / time exit). Fixed targets: 2:1 breakouts, 3:1 bounces.
"""
from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..live.v3 import generate_signals
from ..ml.targets import account, label_paths, _funding_cum, stats
from .mtf import resample
from .sr2_run import _pct, _table

COINS = ["ETHUSDT", "BTCUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
HOLDOUT = pd.Timestamp("2025-11-01")
START = pd.Timestamp("2022-01-01")
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}


def bounce_volume_ratio(sig: pd.DataFrame, df5u: pd.DataFrame) -> pd.Series:
    """Volume of the confirmation candle (the 1D candle before entry) / volume of the touch candle (one before)."""
    d1 = resample(df5u, "1D")
    d1["day"] = pd.to_datetime(d1["open_time"], utc=True).dt.tz_convert(None)
    v = d1.set_index("day")["volume"]
    conf = sig["entry_time"].dt.floor("D") - pd.Timedelta(days=1)
    return pd.Series(v.reindex(conf).to_numpy() / v.reindex(conf - pd.Timedelta(days=1)).to_numpy(), index=sig.index)


def coin_trades(cfg: Config, sym: str) -> pd.DataFrame:
    c = replace(cfg, symbol=sym)
    sig = generate_signals(c)
    sig = sig[~sig["pending_entry"].astype(bool) & sig["setup"].isin(list(TGT))].copy()
    sig["entry_time"] = pd.to_datetime(sig["entry_time"])
    df5u, _ = load_klines_5m(c.data_dir, sym)
    b = sig["setup"] == "1D bounce"
    sig["bounce_vol_ratio"] = np.nan
    sig.loc[b, "bounce_vol_ratio"] = bounce_volume_ratio(sig[b], df5u)
    sig = sig[~(b & (sig["bounce_vol_ratio"] < 0.8))]
    sig = sig[sig["entry_time"] >= START].reset_index(drop=True)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    lab = label_paths(sig.assign(decision_time=sig["entry_time"]), df5n, _funding_cum(c))
    sig = pd.concat([sig, lab.drop(columns=["stop_pct"])], axis=1)
    sig = sig[sig["ok"].astype(bool)].copy()
    T = sig["setup"].map(TGT)
    sig["net"] = [r[f"net_{t:g}"] for (_, r), t in zip(sig.iterrows(), T)]
    sig["exit_time"] = [r[f"exit_{t:g}"] for (_, r), t in zip(sig.iterrows(), T)]
    sig["decision_time"] = sig["entry_time"]
    sig["stop_pct"] = sig["risk"] / sig["px"]
    sig["coin"] = sym.replace("USDT", "")
    sig["hold"] = sig["entry_time"] >= HOLDOUT
    return sig


def run_coins(cfg: Config, out_dir: Path, coins=COINS) -> Path:
    parts = []
    for s in coins:
        print("coin", s, flush=True)
        parts.append(coin_trades(cfg, s))
    A = pd.concat(parts, ignore_index=True)
    A.to_pickle(ROOT / "results" / "coins_v31.pkl")
    wk = {False: (HOLDOUT - START).days / 7, True: (A["entry_time"].max() - HOLDOUT).days / 7}
    L = ["# v3.1 on more coins (ETH rules frozen, nothing fitted on the other coins)", "",
         "**win % = profit after all costs** (each coin's own funding). For ETH the research period is in-sample "
         "(the rules were built on it); for every other coin ALL periods are out-of-sample.", ""]
    rows = []
    for coin, g in A.groupby("coin", sort=False):
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout Nov 2025 - Oct 2026")):
            x = g[g["hold"] == hold]
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x.reset_index(drop=True), "net", "exit_time", RISK) if len(x) else (math.nan, math.nan)
            rows.append({"coin": coin, "period": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd})
    for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout Nov 2025 - Oct 2026")):
        x = A[(A["hold"] == hold) & (A["coin"] != "ETH")]
        s_ = stats(x["net"].to_numpy())
        rows.append({"coin": "ALL 5 NEW COINS", "period": per, **s_, "pw": s_["n"] / wk[hold], "eq": math.nan, "mdd": math.nan})
    fmt = [("coin", "coin", str), ("period", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
           ("win", "win %", _pct), ("avg", "avg R", lambda v: f"{v:+.2f}"), ("pf", "profit factor", lambda v: f"{v:.2f}"),
           ("eq", "account (this coin alone)", lambda v: "" if v != v else f"{v:.2f}x"),
           ("mdd", "worst drop", lambda v: "" if v != v else f"-{v:.0%}")]
    L += ["## Per coin", "", _table(pd.DataFrame(rows), fmt), ""]
    rows = []
    for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
        for setup in TGT:
            r = {"period": per, "setup": setup}
            for coin in A["coin"].unique():
                x = A[(A["hold"] == hold) & (A["setup"] == setup) & (A["coin"] == coin)]
                s_ = stats(x["net"].to_numpy())
                r[f"{coin}"] = f"{s_['win']:.0%} ({s_['n']})" if s_["n"] else "-"
            x = A[(A["hold"] == hold) & (A["setup"] == setup) & (A["coin"] != "ETH")]
            s_ = stats(x["net"].to_numpy())
            r["new coins"] = f"{s_['win']:.0%} ({s_['n']}), {s_['avg']:+.2f}R" if s_["n"] else "-"
            rows.append(r)
    cols = [("period", "period", str), ("setup", "setup", str)] + [(c, c, str) for c in A["coin"].unique()] + \
           [("new coins", "5 new coins: win % (n), avg R", str)]
    L += ["## Win % per setup (trades)", "", _table(pd.DataFrame(rows), cols), ""]
    rows = []
    for name, sel in (("ETH only", A["coin"] == "ETH"), ("all 6 coins together", A["coin"].notna())):
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
            x = A[sel & (A["hold"] == hold)].reset_index(drop=True)
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x, "net", "exit_time", RISK)
            rows.append({"coin": name, "period": per, **s_, "pw": s_["n"] / wk[hold == True], "eq": eq, "mdd": mdd})  # noqa: E712
    L += ["## One account trading the coins together (A+ 4%, others 2%, max 5x, overlapping positions)", "",
          _table(pd.DataFrame(rows), [("coin", "portfolio", str)] + fmt[1:]), ""]
    yr = A.assign(year=A["entry_time"].dt.year.where(~A["hold"], 0)).groupby(["year", "coin"])["net"] \
        .apply(lambda s: f"{(s > 0).mean():.0%} ({len(s)})").unstack()
    yr.index = ["holdout" if y == 0 else str(y) for y in yr.index]
    yr = yr.reset_index().rename(columns={"index": "year"})
    L += ["## Win % by year (trades)", "", _table(yr.fillna("-"), [(c, c, str) for c in yr.columns]), ""]
    path = out_dir / "coins_v31.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
