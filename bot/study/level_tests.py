"""
Multiple tests of a level: after a support/resistance zone has held several times, does it break or reverse hard?

Zones: strong zones known before each candle (levels.py). A TEST = a candle reaches the zone (within 0.25 ATR)
from one side; tests of the same zone (within 1%) are counted over the last 300 candles (one per 6 candles).
At each test we record:
  test_n          how many times this zone was tested before (incl. this one)
  failed_breaks   earlier tests of this zone that CLOSED beyond it but came back within 3 candles
  held            the test candle closed back on the zone's side
Forward outcome (up to 40 candles), whichever comes first:
  break      a close beyond the level by >= 0.5 ATR
  reversal   price moves >= 3 ATR away from the level in the bounce direction ("massive reversal")
  neither
Trade: bounce-confirmed reversal (next candle closes in the bounce direction), entry the candle after,
stop beyond the zone and the wicks + 0.25 ATR, targets 1R / 1.5R / 2R / 3R, on the same candles.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data import load_klines_5m
from .indicators import atr
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import COST_FRAC, _pct, _r, _table

BAND = 0.25
MEMORY = 300
COOLDOWN = 6
FWD = 40
REV_ATR = 3.0
BREAK_ATR = 0.5
RRS = (1.0, 1.5, 2.0, 3.0)
HOLDOUT = pd.Timestamp("2025-11-01", tz="UTC")


def _trade(o, h, l, c, i, d, stop, max_bars=60):
    n = len(o)
    if i >= n:
        return None
    e = o[i]
    risk = (e - stop) * d
    if risk <= 0:
        return None
    last = min(n - 1, i + max_bars - 1)
    if last - i + 1 < max_bars:
        return None
    out = {"entry": e, "risk": risk}
    for rr in RRS:
        tg = e + d * rr * risk
        res = None
        for k in range(i, last + 1):
            if k > i and d * (o[k] - stop) <= 0:
                res = d * (o[k] - e) / risk
                break
            if k > i and d * (o[k] - tg) >= 0:
                res = d * (o[k] - e) / risk
                break
            if (l[k] <= stop) if d > 0 else (h[k] >= stop):
                res = -1.0
                break
            if (h[k] >= tg) if d > 0 else (l[k] <= tg):
                res = rr
                break
        out[f"r_{rr:g}"] = res if res is not None else d * (c[last] - e) / risk
    return out


def tests_for(df5: pd.DataFrame, rule: str) -> pd.DataFrame:
    b = resample(df5, rule).reset_index(drop=True)
    table = _level_table(df5)
    a = atr(b, 14).to_numpy(float)
    o, h, l, c = (b[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ot = pd.to_datetime(b["open_time"], utc=True)
    ct = pd.to_datetime(b["close_time"], utc=True)
    history: list = []   # (j, level, kind, held, failed_break)
    last_test: dict = {}
    zk, zones = None, np.array([])
    rows = []
    for j in range(60, len(b) - 2):
        if not np.isfinite(a[j]) or a[j] <= 0:
            continue
        key = (int((table["known"] <= ot.iloc[j]).sum()), ot.iloc[j].normalize())
        if key != zk:
            zones = strong_levels(table, ot.iloc[j])
            zk = key
        if not len(zones):
            continue
        band = BAND * a[j]
        for kind, cand, d in (("support", zones[(zones < c[j - 1]) & (l[j] <= zones + band)], 1),
                              ("resistance", zones[(zones > c[j - 1]) & (h[j] >= zones - band)], -1)):
            if not len(cand):
                continue
            L = cand.max() if d > 0 else cand.min()
            zkey = (kind, round(L, 2))
            if j - last_test.get(zkey, -10**9) < COOLDOWN:
                continue
            last_test[zkey] = j
            prior = [x for x in history if abs(x[1] - L) / L < 0.01 and 0 < j - x[0] <= MEMORY]
            held = (c[j] > L) if d > 0 else (c[j] < L)
            # failed break: closed beyond the level but back on the zone's side within 3 candles (known at j+3)
            fb = False
            if not held:
                nxt = c[j + 1:j + 4]
                fb = bool(((nxt > L) if d > 0 else (nxt < L)).any())
            history.append((j, L, kind, held, fb))
            prev_failed = sum(1 for x in prior if x[4] and j - x[0] > 3)  # only failures already confirmed
            # forward outcome
            outcome, k_end = "neither", min(len(b) - 1, j + FWD)
            for k in range(j + 1, k_end + 1):
                if d * (c[k] - L) <= -BREAK_ATR * a[j]:
                    outcome = "break"
                    break
                far = (h[k] - L) if d > 0 else (L - l[k])
                if far >= REV_ATR * a[j]:
                    outcome = "reversal"
                    break
            row = {"time": ct.iloc[j], "j": j, "kind": kind, "direction": d, "level": L, "atr": a[j],
                   "test_n": len(prior) + 1, "prev_failed_breaks": prev_failed, "held": held,
                   "outcome": outcome, "complete": j + FWD < len(b)}
            # bounce-confirmed reversal trade
            k = j + 1
            if held and k + 1 < len(b) and d * (c[k] - o[k]) > 0 and d * (c[k] - c[j]) > 0 and \
                    ((c[k] > L) if d > 0 else (c[k] < L)):
                stop = (min(l[j], l[k], L) - 0.25 * a[j]) if d > 0 else (max(h[j], h[k], L) + 0.25 * a[j])
                tr = _trade(o, h, l, c, k + 1, d, stop)
                if tr:
                    row.update({"traded": True, **tr})
            rows.append(row)
    return pd.DataFrame(rows)


def run_level_tests(cfg: Config, out_dir: Path, timeframes=("2h", "4h", "1D")) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    L = ["# Repeated tests of support / resistance: break or massive reversal?", "",
         f"*Break* = a close beyond the level by >= {BREAK_ATR} ATR. *Massive reversal* = price moves >= {REV_ATR:g} ATR "
         f"away from the level in the bounce direction first. Looked at up to {FWD} candles ahead. Tests of the same zone "
         f"are counted over the previous {MEMORY} candles.", ""]
    for tf in timeframes:
        t = tests_for(df5, tf)
        t = t[t["complete"]]
        bar = pd.Timedelta(tf)
        res = t[t["time"] < HOLDOUT - bar * 62]
        hold = t[t["time"] >= HOLDOUT]
        L += [f"## {tf} chart", "", "### What happens at the Nth test of a level", ""]
        rows = []
        for n_lab, m in (("1st", res["test_n"] == 1), ("2nd", res["test_n"] == 2), ("3rd", res["test_n"] == 3),
                         ("4th", res["test_n"] == 4), ("5th", res["test_n"] == 5), ("6th-7th", res["test_n"].between(6, 7)),
                         ("8th+", res["test_n"] >= 8)):
            g = res[m]
            if not len(g):
                continue
            gh = g[g["held"]]
            rows.append({"n": n_lab, "tests": len(g), "held": g["held"].mean(), "brk": (g["outcome"] == "break").mean(),
                         "rev": (g["outcome"] == "reversal").mean(),
                         "h_brk": (gh["outcome"] == "break").mean() if len(gh) else math.nan,
                         "h_rev": (gh["outcome"] == "reversal").mean() if len(gh) else math.nan})
        L += [_table(pd.DataFrame(rows), [("n", "test of the level", str), ("tests", "tests", str),
                                          ("held", "held at close", _pct), ("brk", "all: then BROKE", _pct),
                                          ("rev", "all: then MASSIVE REVERSAL", _pct),
                                          ("h_brk", "if held: then BROKE", _pct),
                                          ("h_rev", "if held: then MASSIVE REVERSAL", _pct)]), ""]
        rows = []
        for lab, m in (("0", res["prev_failed_breaks"] == 0), ("1", res["prev_failed_breaks"] == 1),
                       ("2", res["prev_failed_breaks"] == 2), ("3+", res["prev_failed_breaks"] >= 3)):
            g = res[m]
            if len(g):
                rows.append({"fb": lab, "tests": len(g), "brk": (g["outcome"] == "break").mean(),
                             "rev": (g["outcome"] == "reversal").mean()})
        L += ["### After failed breakouts (closed through, then back within 3 candles)", "",
              _table(pd.DataFrame(rows), [("fb", "earlier failed breaks of this level", str), ("tests", "tests", str),
                                          ("brk", "then BROKE", _pct), ("rev", "then MASSIVE REVERSAL", _pct)]), ""]
        # trades
        rows = []
        for lab, m in (("1st-3rd test", lambda x: x["test_n"] <= 3), ("4th+ test", lambda x: x["test_n"] >= 4),
                       ("4th+ test, after >= 1 failed break", lambda x: (x["test_n"] >= 4) & (x["prev_failed_breaks"] >= 1)),
                       ("any test, after >= 2 failed breaks", lambda x: x["prev_failed_breaks"] >= 2)):
            for per, g in (("research", res), ("holdout", hold)):
                gg = g[m(g) & g.get("traded", pd.Series(False, index=g.index)).fillna(False).astype(bool)]
                if not len(gg):
                    continue
                cost = COST_FRAC * gg["entry"] / gg["risk"]
                row = {"what": lab, "period": per, "n": len(gg)}
                for rr in RRS:
                    net = gg[f"r_{rr:g}"] - cost
                    row[f"w{rr:g}"], row[f"a{rr:g}"] = (net > 0).mean(), net.mean()
                rows.append(row)
        L += ["### Trading the bounce (confirmed by the next candle)", "",
              "Win % = profit after costs; avg R after costs.", "",
              _table(pd.DataFrame(rows), [("what", "trades", str), ("period", "period", str), ("n", "n", str),
                                          *[(f"w{rr:g}", f"win {rr:g}:1", _pct) for rr in RRS],
                                          *[(f"a{rr:g}", f"avg R {rr:g}:1", _r) for rr in RRS]]), ""]
    path = out_dir / "level_tests.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
