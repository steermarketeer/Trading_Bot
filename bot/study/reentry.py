"""Re-entries after stop hunts on v3 trades (breakouts 2:1 on 2h/4h/1D at 7+, 1D 4th-test bounces 3:1)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .indicators import atr
from .mtf import resample
from .smalltf import COST_TAKER
from .sr2_run import _pct, _r, _table
from .strategy_eval import replay_one
from .strategy_v2 import simulate

HOLDOUT = pd.Timestamp("2025-11-01")
WAIT = 10


def base_trades() -> pd.DataFrame:
    B = pd.read_pickle(ROOT / "results" / "more_trades_breakouts.pkl")
    B = B[(B["certainty"] >= 7) & B["tf"].isin(["2h", "4h", "1D"])].copy()
    B["T"], B["R"], B["exit"] = 2.0, B["R_2:1"], B["exit_2:1"]
    C = pd.read_pickle(ROOT / "results" / "boost_B.pkl")
    C = C[C["decision_time"] >= pd.Timestamp("2022-01-01")].copy()
    C["setup"], C["T"], C["R"], C["exit"] = "1D 4th-test bounce (3:1)", 3.0, C["R_3:1"], C["exit_3:1"]
    cols = ["decision_time", "exit", "setup", "tf", "direction", "entry", "risk", "stop_pct", "R", "T", "hold"]
    t = pd.concat([B[cols], C[cols]], ignore_index=True)
    t["net"] = t["R"] - COST_TAKER / t["stop_pct"]
    return t.sort_values("decision_time").reset_index(drop=True)


def find_reentries(t: pd.DataFrame, df5u: pd.DataFrame, df5n: pd.DataFrame, trigger: str) -> pd.DataFrame:
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    t5 = df5n["open_time"].to_numpy()
    bars = {}
    for tf in t["tf"].unique():
        b = resample(df5u, tf).reset_index(drop=True)
        b["a"] = atr(b, 14)
        b["ct"] = pd.to_datetime(b["close_time"], utc=True).dt.tz_convert(None)
        bars[tf] = b
    rows = []
    for _, r in t.iterrows():
        if not (r["R"] <= -0.999):  # only stop-outs
            continue
        b = bars[r["tf"]]
        d, e, rk = int(r["direction"]), r["entry"], r["risk"]
        stop = e - d * rk
        lvl = e if trigger == "entry" else stop
        i0 = int(np.searchsorted(b["ct"].to_numpy(), np.datetime64(r["exit"]), side="left"))  # first candle closing after the stop
        # extreme reached between the original entry and each candle close (the stop-hunt wick)
        s0 = int(np.searchsorted(t5, np.datetime64(r["decision_time"])))
        for k in range(i0, min(i0 + WAIT, len(b) - 1)):
            close_k = b["close"].iloc[k]
            if d * (close_k - lvl) > 0:
                s1 = int(np.searchsorted(t5, np.datetime64(b["ct"].iloc[k])))
                wick = Lw[s0:s1].min() if d > 0 else H[s0:s1].max()
                a = b["a"].iloc[k]
                new_stop = wick - d * 0.25 * a
                entry_time = b["ct"].iloc[k]
                i_e = int(np.searchsorted(t5, np.datetime64(entry_time)))
                if i_e >= len(t5):
                    break
                new_e = O[i_e]
                nrisk = (new_e - new_stop) * d
                if nrisk <= 0 or nrisk / new_e > 0.15:
                    break
                res = replay_one(O, H, Lw, C, t5, entry_time, r["tf"], d, nrisk, (r["T"],))
                if res is None:
                    break
                ex, px = res
                R2, xt = ex[f"{r['T']:g}:1"]
                rows.append({"decision_time": entry_time, "exit": xt, "setup": r["setup"] + " RE-ENTRY", "tf": r["tf"],
                             "direction": d, "entry": new_e, "risk": nrisk, "stop_pct": nrisk / px, "R": R2, "T": r["T"],
                             "hold": entry_time >= HOLDOUT, "net": R2 - COST_TAKER / (nrisk / px),
                             "wait": k - i0 + 1})
                break
    return pd.DataFrame(rows)


def run_reentry(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t = base_trades()
    L = ["# Re-entries after stop hunts (v3 trades)", "",
         f"A stopped-out v3 trade is re-entered ONCE if, within {WAIT} candles of its chart, a candle closes back beyond the "
         "trigger level; entry next open, stop beyond the stop-hunt wick + 0.25 ATR, target 2:1 (breakouts) / 3:1 (bounces). "
         "5m replay, market-order costs. win % = profit after costs.", ""]
    risk = {"A+ breakout (2:1)": 0.04, "breakout (2:1)": 0.02, "1D 4th-test bounce (3:1)": 0.02}
    summ = []
    for trig, label in (("entry", "close back beyond the original ENTRY"), ("stop", "close back beyond the original STOP")):
        re = find_reentries(t, df5u, df5n, trig)
        re.to_pickle(ROOT / "results" / f"reentries_{trig}.pkl")
        rows = []
        for per, pm in (("research", ~re["hold"]), ("holdout", re["hold"])) if len(re) else ():
            for st, g in list(re[pm].groupby("setup")) + [("ALL re-entries", re[pm])]:
                rows.append({"setup": st, "period": per, "n": len(g), "win": (g["net"] > 0).mean(), "avg": g["net"].mean()})
        losses = {per: int(((t["R"] <= -0.999) & (t["hold"] == (per == "holdout"))).sum()) for per in ("research", "holdout")}
        L += [f"## Trigger: {label}", "",
              f"Stop-outs available: research {losses['research']}, holdout {losses['holdout']}.", "",
              _table(pd.DataFrame(rows), [("setup", "re-entry of", str), ("period", "period", str), ("n", "re-entries", str),
                                          ("win", "win %", _pct), ("avg", "avg R after costs", _r)]) if rows else "None.", ""]
        r2 = re.copy()
        r2["setup"] = r2["setup"].str.replace(" RE-ENTRY", "")
        for per, pm in (("research", ~t["hold"]), ("holdout", t["hold"])):
            base = t[pm].reset_index(drop=True)
            both = pd.concat([base, r2[r2["hold"] == (per == "holdout")]], ignore_index=True).sort_values("decision_time").reset_index(drop=True)
            weeks = max((base["decision_time"].max() - base["decision_time"].min()).days / 7, 1)
            for name, g in (("v3 only", base), (f"v3 + re-entries ({trig})", both)):
                s = simulate(g, risk)
                summ.append({"version": name, "period": per, "n": len(g), "pw": len(g) / weeks,
                             "win": (g["net"] > 0).mean(), "avg": g["net"].mean(), "final": s["final"], "dd": s["max_dd"]})
    S = pd.DataFrame(summ).drop_duplicates(["version", "period"])
    L += ["## Whole strategy with re-entries (risk A+ 4% / others 2%, cap 5x)", "",
          _table(S, [("version", "version", str), ("period", "period", str), ("n", "trades", str),
                     ("pw", "trades/week", lambda v: f"{v:.1f}"), ("win", "win %", _pct), ("avg", "avg R", _r),
                     ("final", "account", lambda v: f"{v:,.2f}x"), ("dd", "max drawdown", lambda v: f"{v:.0%}")]), ""]
    path = out_dir / "reentry.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
