"""
15m top-down entries for the v3.1 signals (Master Plan workstream 4).

The higher timeframe (2h / 4h / 1D v3.1 rules, incl. all multi-timeframe checks) decides direction, stop price and
target price (2:1 breakouts, 3:1 bounces from the signal price). The 15m chart only decides WHERE and WHEN to get in,
within an entry window of min(signal timeframe, 8h) after the signal. Methods (fixed in advance):

  M0 market   market order at the signal (the current v3.1 entry)
  M1 limit25  limit order 0.25R back toward the stop; missed if not filled in the window
  M2 limit50  limit order 0.5R back toward the stop; missed if not filled in the window
  M3 limit25+ as M1, but if not filled: market at the end of the window if the trade still has >= 1.2:1 left
  M4 15m conf wait for a 15m pullback (price trades >= 0.1R against the signal price) and then a 15m candle closing
              beyond the previous 15m candle's extreme; market entry at the next open; stop tightened to just past
              the pullback extreme (never wider than the HTF stop); taken only if >= 1.2:1 to the HTF target. If the
              HTF stop is hit before confirmation, no trade.
  M5          as M4 with v3's existing rule: stop at least 0.6% of price (not wider than the HTF stop)
Same stop and target prices for every method, so a better entry = bigger reward and smaller risk.
Fills: limit entry / target fill only if price trades 0.02% through. In the limit fill candle the stop is assumed
hit if that candle reaches it, and the target is never counted in the fill candle (conservative).
Costs: market 0.09% per side (taker + slippage), limit 0.02%; actual funding. Time limit as before (60 signal candles).
win % = profit after costs, in R of the ACTUAL risk taken. Account: risk% on the actual stop distance (max 5x).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..study.sr2_run import _pct, _table
from .targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats

FIVE = pd.Timedelta(minutes=5)
HOLDOUT = pd.Timestamp("2025-11-01")
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
METHODS = ["M0 market", "M1 limit 0.25R", "M2 limit 0.5R", "M3 limit 0.25R, else market", "M4 15m confirmation", "M5 15m confirmation, stop >= 0.6%"]


def _run(o, h, l, c, i0, e, s, tg, limit_entry, end):
    """Trade in direction-normalised prices from candle i0 (entry e). Returns (R gross in actual risk, exit idx, kind)."""
    risk = e - s
    buf = LIMIT_BUFFER * abs(e)
    if limit_entry:
        if l[i0] <= s:
            return (s - e) / risk, i0, "stop"
        j0 = i0 + 1
    else:
        j0 = i0
    for i in range(j0, end):
        if i > j0 and o[i] <= s:
            return (o[i] - e) / risk, i, "stop"
        if l[i] <= s:
            return (s - e) / risk, i, "stop"
        if h[i] >= tg + buf:
            return (tg - e) / risk, i, "target"
    return (c[end - 1] - e) / risk, end - 1, "time"


def entries(tr: pd.DataFrame, df5n: pd.DataFrame, fund) -> pd.DataFrame:
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ft, fc = fund
    rows = []
    for idx, r in tr.iterrows():
        dt, tf, d, risk0 = pd.Timestamp(r["decision_time"]), r["tf"], int(r["direction"]), float(r["risk"])
        bpt = int(pd.Timedelta(tf) / FIVE)
        st = int(np.searchsorted(t5, dt.to_datetime64()))
        if st >= len(t5) or t5[st] != dt.to_datetime64() or st + MAX_TF_BARS * bpt > len(O):
            continue
        end = st + MAX_TF_BARS * bpt
        win = st + int(min(pd.Timedelta(tf), pd.Timedelta("8h")) / FIVE)
        o, h, l, c = O[:end], H[:end], Lw[:end], C[:end]
        if d < 0:
            o, h, l, c = -o, -l, -h, -c
        e0 = o[st]
        s, tg = e0 - risk0, e0 + TGT[r["setup"]] * risk0
        buf = LIMIT_BUFFER * abs(e0)

        def book(method, i0, e, limit_entry, stop=s):
            R, xi, kind = _run(o, h, l, c, i0, e, stop, tg, limit_entry, end)
            ent_t = pd.Timestamp(t5[i0])
            x_t = pd.Timestamp(t5[xi]) + FIVE
            a = np.searchsorted(ft, ent_t.to_datetime64(), side="right")
            b = np.searchsorted(ft, x_t.to_datetime64(), side="left")
            fund_frac = (fc[b] - fc[a]) * d if b > a else 0.0
            sp = (e - stop) / abs(e)
            cost = (C_LMT if limit_entry else C_MKT) + (C_LMT if kind == "target" else C_MKT)
            rows.append({"trade": idx, "method": method, "setup": r["setup"], "tf": tf, "hold": dt >= HOLDOUT,
                         "decision_time": ent_t, "exit_time": x_t, "stop_pct": sp, "rr": (tg - e) / (e - stop),
                         "R": R, "net": R - (cost + fund_frac) / sp, "kind": kind})

        def first_fill(lim):
            m = np.flatnonzero(l[st:win] <= lim - buf)
            return st + int(m[0]) if len(m) else -1

        book(METHODS[0], st, e0, False)
        for method, k in ((METHODS[1], 0.25), (METHODS[2], 0.5)):
            i = first_fill(e0 - k * risk0)
            if i >= 0:
                book(method, i, e0 - k * risk0, True)
        i = first_fill(e0 - 0.25 * risk0)
        if i >= 0:
            book(METHODS[3], i, e0 - 0.25 * risk0, True)
        elif win < end and l[st:win].min() > s and o[win] < tg and (tg - o[win]) / (o[win] - s) >= 1.2:
            book(METHODS[3], win, o[win], False)
        # M4: 15m pullback + confirmation candle
        pulled, low = False, np.inf
        for k in range((win - st) // 3):
            a0 = st + 3 * k
            hh, ll, cc = h[a0:a0 + 3].max(), l[a0:a0 + 3].min(), c[a0 + 2]
            if ll <= s:
                break                                      # HTF stop hit before any confirmation: no trade
            low = min(low, ll)
            if ll <= e0 - 0.1 * risk0:
                pulled = True
            if k > 0 and pulled and cc > h[a0 - 3:a0].max():
                i0 = a0 + 3
                if i0 >= end:
                    break
                e = o[i0]
                stop = max(s, low - 0.05 * risk0)
                if e > stop and e < tg and (tg - e) / (e - stop) >= 1.2:
                    book(METHODS[4], i0, e, False, stop)
                stop5 = min(stop, e - 0.006 * abs(e))           # v3 rule: stop at least 0.6% of price
                if stop5 >= s and e < tg and (tg - e) / (e - stop5) >= 1.2:
                    book(METHODS[5], i0, e, False, stop5)
                break
    return pd.DataFrame(rows)


def run_entry15(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    X = pd.read_pickle(ROOT / "results" / "ml_targets.pkl")
    X.attrs = {}
    E = entries(X[["decision_time", "tf", "direction", "risk", "setup"]], df5n, _funding_cum(cfg))
    E.to_pickle(ROOT / "results" / "entry15.pkl")
    n_sig = {p: int(((X["decision_time"] >= HOLDOUT) == p).sum()) for p in (False, True)}
    weeks = {False: (HOLDOUT - pd.Timestamp("2022-01-01")).days / 7,
             True: (X["decision_time"].max() - HOLDOUT).days / 7}
    L = ["# 15m entries for the v3.1 signals", "",
         f"{len(X)} v3.1 signals (2022 - Oct 2026). The higher timeframe sets direction, stop and target; the 15m "
         "chart decides the entry. **win % = profit after all costs**, avg R in the actual risk taken.", "",
         "- M0 market at the signal (current) | M1 / M2 limit 0.25R / 0.5R back toward the stop (missed if not "
         "filled) | M3 limit 0.25R else market at window end | M4 15m pullback + confirmation candle, tighter stop", ""]
    rows = []
    for hold, per in ((False, "research 2022 - Oct 2025"), (True, "holdout Nov 2025 - Oct 2026")):
        for m in METHODS:
            g = E[(E["hold"] == hold) & (E["method"] == m)].set_index("trade")
            s_ = stats(g["net"].to_numpy())
            eq, mdd = account(g.reset_index(), "net", "exit_time", RISK) if len(g) else (math.nan, math.nan)
            rows.append({"period": per, "method": m, **s_, "fill": len(g) / n_sig[hold], "pw": len(g) / weeks[hold],
                         "rr": g["rr"].mean(), "eq": eq, "mdd": mdd})
    L += ["## Results", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("method", "entry", str), ("n", "trades", str), ("fill", "of signals", _pct),
        ("pw", "per week", lambda v: f"{v:.2f}"), ("win", "win %", _pct), ("avg", "avg R", lambda v: f"{v:+.2f}"),
        ("rr", "avg reward:risk", lambda v: f"{v:.2f}"), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    rows = []
    for hold, per in ((False, "research"), (True, "holdout")):
        for setup in TGT:
            r = {"period": per, "setup": setup}
            for k, m in enumerate(METHODS):
                g = E[(E["hold"] == hold) & (E["method"] == m) & (E["setup"] == setup)]
                s_ = stats(g["net"].to_numpy())
                r[f"n{k}"], r[f"w{k}"], r[f"a{k}"] = s_["n"], s_["win"], s_["avg"]
            rows.append(r)
    cols = [("period", "period", str), ("setup", "setup", str)]
    for k, m in enumerate(METHODS):
        cols += [(f"n{k}", f"{m.split()[0]} n", str), (f"w{k}", "win %", _pct), (f"a{k}", "avg R", lambda v: f"{v:+.2f}")]
    L += ["## By setup", "", _table(pd.DataFrame(rows), cols), ""]
    # missed trades: what did the signals that a limit order missed do?
    base = E[E["method"] == METHODS[0]].set_index("trade")
    rows = []
    for m in METHODS[1:]:
        got = set(E.loc[E["method"] == m, "trade"])
        for hold, per in ((False, "research"), (True, "holdout")):
            b = base[base["hold"] == hold]
            miss = b[~b.index.isin(got)]
            rows.append({"method": m, "period": per, "n": len(miss),
                         "win": stats(miss["net"].to_numpy())["win"], "avg": stats(miss["net"].to_numpy())["avg"]})
    L += ["## Signals each method did NOT trade (their result with a market entry)", "",
          _table(pd.DataFrame(rows), [("method", "entry", str), ("period", "period", str), ("n", "signals skipped", str),
                                      ("win", "win % at market", _pct), ("avg", "avg R at market", lambda v: f"{v:+.2f}")]), ""]
    path = out_dir / "entry15.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
