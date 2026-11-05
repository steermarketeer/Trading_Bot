"""
The trader's three-step rule (from h015): close the long, wait for confirmation, then short.

For every v3.1 ETH long breakout / bounce (one position per move; shorts mirrored):
  STEP 1  close: after entry, a 4h candle pokes ABOVE the 4h upper Bollinger band and closes back inside it, and later a
          4h close BELOW the 4h middle band (before the stop / target) -> close the long at the next 4h open.
          Variant 1b: the same, only when the daily close is below the daily EMA 200 (bearish trend).
  STEP 2  confirm: within the next 12 4h candles (2 days), price comes back up to the middle band (high >= middle) and the 4h candle
          closes back below it (a failed retest = lower high), daily below the daily EMA 200.
  STEP 3  short at the next 4h open; stop just above the top that failed (highest high since entry, +0.1%); target = the nearest untaken 1h / 4h low or
          the daily lower Bollinger band, whichever is farther, but at least 1.2 : 1 (otherwise no short).
Only candles closed at each decision. Costs: market 0.09% per side, limit target 0.02%, funding.
The idea came from reviewing holdout trades, so 2022 - Oct 2025 is the clean test.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats
from .concepts import Bars
from .indicators import bollinger, ema
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02, "short (confirmed)": 0.02}
PRIORITY = {"A+ breakout": 0, "breakout": 1, "1D bounce": 2}
CONFIRM_BARS = 12
STOP_AT = "failed top"   # "retest" = above the retest candle high; "failed top" = above the highest high since entry


def run_bandfail(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ft, fc = _funding_cum(cfg)
    b4 = resample(df5u, "4h")
    t4 = pd.to_datetime(b4["open_time"], utc=True).dt.tz_convert(None).to_numpy()
    mid4, up4, lo4 = (x.to_numpy(float) for x in bollinger(b4["close"]))
    H4, L4, C4 = (b4[x].to_numpy(float) for x in ("high", "low", "close"))
    d1 = resample(df5u, "1D")
    d1t = pd.to_datetime(d1["close_time"], utc=True).dt.tz_convert(None).to_numpy()
    e200 = ema(d1["close"], 200).to_numpy(float)
    _, dup, dlo = (x.to_numpy(float) for x in bollinger(d1["close"]))
    D1c = d1["close"].to_numpy(float)
    sw = {}
    for tf, rule in (("1h", "1h"), ("4h", "4h")):
        b = Bars(resample(df5u, rule))
        sw[tf] = (b, b.ct.dt.tz_convert(None).to_numpy())

    def untaken(tf, t, side, lookback=150):
        b, ct = sw[tf]
        n = int(np.searchsorted(ct, np.datetime64(t), side="right"))
        out = []
        for i, p, cf in (b.sl if side == "L" else b.sh):
            if cf < n and i >= n - lookback:
                seg = b.l[i + 1:n] if side == "L" else b.h[i + 1:n]
                if not len(seg) or (seg.min() >= p if side == "L" else seg.max() <= p):
                    out.append(p)
        return out

    def daily_at(t):
        k = int(np.searchsorted(d1t, np.datetime64(t), side="right")) - 1
        return k

    def fund(i0, i1, d):
        a = np.searchsorted(ft, t5[i0], side="right")
        b_ = np.searchsorted(ft, (pd.Timestamp(t5[i1]) + FIVE).to_datetime64(), side="left")
        return (fc[b_] - fc[a]) * d if b_ > a else 0.0

    def run_5m(i0, end, d, e, s, tg):
        """direction-normalised replay from 5m index i0 (market entry at o[i0])."""
        o, h, l, c = (O, H, Lw, C) if d > 0 else (-O, -Lw, -H, -C)
        risk = e - s
        buf = LIMIT_BUFFER * abs(e)
        for i in range(i0, end):
            if i > i0 and o[i] <= s:
                return (o[i] - e) / risk, i, "stop"
            if l[i] <= s:
                return (s - e) / risk, i, "stop"
            if h[i] >= tg + buf:
                return (tg - e) / risk, i, "target"
        return (c[end - 1] - e) / risk, end - 1, "time"

    A = pd.read_pickle(ROOT / "results" / "coins_v31.pkl")
    S = A[A["coin"] == "ETH"].copy()
    S["prio"] = S["setup"].map(PRIORITY)
    S = S.sort_values(["entry_time", "direction", "prio"]).drop_duplicates(["entry_time", "direction"]).reset_index(drop=True)
    rows, shorts = [], []
    for k, r in S.iterrows():
        d, risk = int(r["direction"]), float(r["risk"])
        sg = 1.0 if d > 0 else -1.0
        st = int(np.searchsorted(t5, pd.Timestamp(r["entry_time"]).to_datetime64()))
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        end = min(len(O), st + MAX_TF_BARS * bpt)
        e = O[st]
        s, tg = e - d * risk, e + d * TGT[r["setup"]] * risk
        # base outcome
        Rb, xb, kb = run_5m(st, end, d, sg * e, sg * s, sg * tg)
        # scan 4h candles after entry for step 1, stopping at the base exit
        j0 = int(np.searchsorted(t4, t5[st]))
        poked, close_at, close_j = False, None, None
        j = j0
        while j < len(t4) - 1:
            j_end5 = int(np.searchsorted(t5, t4[j] + np.timedelta64(4, "h")))   # 5m index where this 4h candle ends
            if j_end5 - 1 >= xb:
                break                                     # the trade ended inside this candle
            hh, cc = (H4[j], C4[j]) if d > 0 else (-L4[j], -C4[j])
            upb, md = (up4[j], mid4[j]) if d > 0 else (-lo4[j], -mid4[j])
            if hh > upb and cc <= upb:
                poked = True
            if poked and cc < md:
                close_at, close_j = j_end5, j
                break
            j += 1
        kd = daily_at(r["entry_time"])
        bear = (D1c[kd] - e200[kd]) * d < 0                # daily on the wrong side of its EMA 200 for this trade
        row = {"sig": k, "setup": r["setup"], "hold": bool(r["entry_time"] >= HOLDOUT), "bear": bool(bear),
               "net_base": Rb - (C_MKT + (C_LMT if kb == "target" else C_MKT) + fund(st, xb, d)) / (risk / abs(e)),
               "exit_base": pd.Timestamp(t5[xb]) + FIVE, "stop_pct": risk / abs(e), "entry_time": r["entry_time"],
               "decision_time": r["entry_time"], "closed_early": close_at is not None}
        if close_at is not None and close_at < len(O):
            R1 = (O[close_at] - e) * d / risk
            row["net_close"] = R1 - (2 * C_MKT + fund(st, close_at, d)) / (risk / abs(e))
            row["exit_close"] = pd.Timestamp(t5[close_at])
            # step 2: failed retest of the middle band within CONFIRM_BARS 4h candles (only in a bearish trend)
            if bear:
                for jj in range(close_j + 1, min(len(t4) - 1, close_j + 1 + CONFIRM_BARS)):
                    hh, cc = (H4[jj], C4[jj]) if d > 0 else (-L4[jj], -C4[jj])
                    md = mid4[jj] if d > 0 else -mid4[jj]
                    if hh >= md and cc < md:
                        i0 = int(np.searchsorted(t5, t4[jj] + np.timedelta64(4, "h")))
                        if i0 >= len(O) - 1:
                            break
                        ent = O[i0]
                        if STOP_AT == "retest":
                            stop = (H4[jj] * 1.001) if d > 0 else (L4[jj] * 0.999)
                        else:                                                              # above the top that failed
                            stop = (H4[j0:jj + 1].max() * 1.001) if d > 0 else (L4[j0:jj + 1].min() * 0.999)
                        t_now = pd.Timestamp(t5[i0])
                        side = "L" if d > 0 else "H"
                        liq = np.array(untaken("1h", t_now, side) + untaken("4h", t_now, side))
                        k2 = daily_at(t_now)
                        dband = dlo[k2] if d > 0 else dup[k2]
                        if d > 0:      # the short of a long: targets below the entry, take the farther one
                            below = liq[liq < ent * 0.999]
                            cands = ([below.max()] if len(below) else []) + ([dband] if dband < ent * 0.999 else [])
                            tgt2 = min(cands) if cands else np.nan
                        else:          # the long of a short: targets above the entry
                            above = liq[liq > ent * 1.001]
                            cands = ([above.min()] if len(above) else []) + ([dband] if dband > ent * 1.001 else [])
                            tgt2 = max(cands) if cands else np.nan
                        r2 = (stop - ent) * d                                            # short risk (positive)
                        if not (np.isfinite(tgt2) and r2 > 0):
                            break
                        rr = (ent - tgt2) * d / r2
                        if rr < 1.2:
                            break
                        end2 = min(len(O), i0 + 60 * 48)                                 # 60 4h candles at most
                        R2, x2, k2s = run_5m(i0, end2, -d, -sg * ent, -sg * stop, -sg * tgt2)
                        sp2 = r2 / abs(ent)
                        net2 = R2 - (C_MKT + (C_LMT if k2s == "target" else C_MKT) + fund(i0, x2, -d)) / sp2
                        shorts.append({"sig": k, "setup": "short (confirmed)", "hold": row["hold"], "net": net2, "rr": rr,
                                       "stop_pct": sp2, "decision_time": t_now, "exit_time": pd.Timestamp(t5[x2]) + FIVE,
                                       "kind": k2s})
                        break
        else:
            row["net_close"], row["exit_close"] = row["net_base"], row["exit_base"]
        rows.append(row)
    X = pd.DataFrame(rows)
    Sh = pd.DataFrame(shorts)
    X.to_pickle(ROOT / "results" / "bandfail.pkl")
    Sh.to_pickle(ROOT / "results" / "bandfail_shorts.pkl")
    X["net_close_bear"] = np.where(X["bear"], X["net_close"], X["net_base"])
    X["exit_close_bear"] = np.where(X["bear"], X["exit_close"], X["exit_base"])
    wk = {False: (HOLDOUT - pd.Timestamp("2022-01-01")).days / 7, True: (X["entry_time"].max() - HOLDOUT).days / 7}
    f2 = lambda v: f"{v:+.2f}"  # noqa: E731
    L = ["# Close the long, confirm, then short: tested on every v3.1 ETH trade", "",
         "One position per move. **win % = profit after all costs.** The idea came from holdout trades, so "
         "**2022 - Oct 2025 is the clean test**.", ""]
    rows = []
    variants = [("v3.1 now", "net_base", "exit_base", None), ("step 1: close on a 4h band failure (any trend)", "net_close", "exit_close", None),
                ("step 1b: close on a band failure only in a bearish trend", "net_close_bear", "exit_close_bear", None),
                ("step 1b + confirmed shorts (steps 2-3)", "net_close_bear", "exit_close_bear", "shorts")]
    for name, nc, xc, add in variants:
        for hold, per in ((False, "2022 - Oct 2025 (clean test)"), (True, "holdout")):
            x = X[X["hold"] == hold][["setup", "decision_time", "stop_pct", nc, xc]].rename(columns={nc: "net", xc: "exit_time"})
            if add and len(Sh):
                x = pd.concat([x, Sh[Sh["hold"] == hold][["setup", "decision_time", "stop_pct", "net", "exit_time"]]])
            x = x.reset_index(drop=True)
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x, "net", "exit_time", RISK) if len(x) else (math.nan, math.nan)
            rows.append({"v": name, "per": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd})
    L += ["## Results", "", _table(pd.DataFrame(rows), [
        ("v", "strategy", str), ("per", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    rows = []
    for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
        for trend in (True, False):
            x = X[(X["hold"] == hold) & (X["bear"] == trend) & X["closed_early"]]
            rows.append({"per": per, "trend": "bearish (below daily EMA 200)" if trend else "bullish", "n": len(x),
                         "lost": int((x["net_base"] <= 0).sum()), "won": int((x["net_base"] > 0).sum()),
                         "dR": float((x["net_close"] - x["net_base"]).sum())})
    L += ["## Step 1 in detail: longs the band failure would close early", "", _table(pd.DataFrame(rows), [
        ("per", "period", str), ("trend", "daily trend", str), ("n", "closed early", str), ("lost", "would have lost anyway", str),
        ("won", "would have won", str), ("dR", "R saved (+) / given up (−)", f2)]), ""]
    if len(Sh):
        rows = []
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
            x = Sh[Sh["hold"] == hold]
            s_ = stats(x["net"].to_numpy())
            rows.append({"per": per, **s_, "rr": x["rr"].mean() if len(x) else math.nan})
        L += ["## Steps 2-3: the confirmed shorts", "", _table(pd.DataFrame(rows), [
            ("per", "period", str), ("n", "shorts", str), ("win", "win %", _pct), ("avg", "avg R", f2),
            ("pf", "profit factor", lambda v: f"{v:.2f}"), ("rr", "avg reward:risk", lambda v: f"{v:.2f}")]), ""]
    path = out_dir / "bandfail.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
