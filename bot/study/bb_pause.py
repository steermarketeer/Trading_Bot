"""
Bollinger: pump -> sideways in the upper half of the bands -> first touch of the middle band -> does the trend resume?
(The trader's reading of the daily chart, 27 Mar 2023.) Mirrored for dumps. Everything known at the touch candle's close.

Pump        a candle that CLOSES beyond the outer band (upper band for the up version), within the last 20 candles
Sideways    every close after the pump stayed above the middle band, for at least 3 candles (price held the upper half)
Touch       the first candle since the pump whose low reaches the middle band (low <= middle + 0.25 ATR)
  holds     ... and closes back above the middle band              claim: up (the trend resumes)
  breaks    ... and closes below the middle band                    claim: down (the pause turned)
Compared with every middle-band touch in an uptrend without the pump-and-sideways sequence.
Fair test (reports/indicator_learn.md): 1.5 ATR in the claimed direction before 1.5 ATR against, 30 candles; a coin flip
is 50%; noise check by moving the events to random dates (400 shifts, clustering kept).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .defs import TF
from .indicator_learn import HORIZON, event_pvalue, outcome
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")


def masks(t: TF, side: int):
    c, h, l = (t.c, t.h, t.l) if side > 0 else (-t.c, -t.l, -t.h)
    up, mid = (t.up, t.mid) if side > 0 else (-t.lo, -t.mid)
    a = t.a
    n = t.n
    holds, breaks, plain = (np.zeros(n, bool) for _ in range(3))
    last_pump, touched = -10 ** 9, True
    for j in range(25, n):
        if not np.isfinite(a[j]) or not np.isfinite(mid[j]):
            continue
        touch = l[j] <= mid[j] + 0.25 * a[j]
        # a middle-band touch while the middle band is rising (uptrend), the comparison group
        if touch and mid[j] > mid[j - 5] and not (l[j - 1] <= mid[j - 1] + 0.25 * a[j - 1]):
            plain[j] = c[j] > mid[j]
        if j - last_pump <= 20 and not touched and touch:
            held = j - last_pump - 1 >= 3 and np.all(c[last_pump + 1:j] > mid[last_pump + 1:j])
            if held:
                holds[j] = c[j] > mid[j]
                breaks[j] = c[j] <= mid[j]
            touched = True
        if c[j] > up[j]:                                                # a pump close (after using j as a touch)
            last_pump, touched = j, False
    return holds, breaks, plain & ~holds


def run_bb_pause(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    L = ["# Pump -> sideways in the upper half -> first touch of the middle band: does the trend resume?", "",
         "Fair test: 1.5 ATR in the claimed direction before 1.5 ATR against (30 candles). **A coin flip = 50%.** Up and "
         "mirrored down versions pooled. Research 2020 - Oct 2025; holdout Nov 2025 on. **chance it is noise**: events "
         "moved to random dates (400 shifts, clustering kept); below 0.01 = real.", ""]
    for tf in ("4h", "1D"):
        t = TF(resample(df5u, tf))
        y = outcome(t)
        ot = pd.to_datetime(t.ot)
        hold = np.asarray(ot >= HOLDOUT)
        late = np.asarray((ot < HOLDOUT) & (ot >= HOLDOUT - HORIZON * pd.Timedelta(tf)))
        years = np.asarray(ot.year)
        M = {s: masks(t, s) for s in (1, -1)}
        rows = []
        for name, k, claim in (("touch holds (closes back above the middle band): claim the trend resumes", 0, 1),
                               ("touch breaks (closes below the middle band): claim the pause turns", 1, -1),
                               ("any middle-band touch-and-hold in a rising band, without the pump-and-sideways", 2, 1)):
            bu, be = (M[1][k], M[-1][k]) if claim > 0 else (M[-1][k], M[1][k])
            bu, be = bu & ~late, be & ~late
            right = np.concatenate([y[bu], 1 - y[be]]); hd = np.concatenate([hold[bu], hold[be]])
            yr = np.concatenate([years[bu], years[be]])
            ok = ~np.isnan(right); right, hd, yr = right[ok], hd[ok], yr[ok]
            okr = ~hold & ~late
            pv = event_pvalue(y[okr], bu[okr], be[okr])
            gy = sum(1 for yy in range(2020, 2026) if (m := ~hd & (yr == yy)).sum() >= 5 and right[m].mean() > 0.5)
            ny = sum(1 for yy in range(2020, 2026) if (~hd & (yr == yy)).sum() >= 5)
            rs = ~hd & (yr >= 2020)                                       # research rows: 2020 - Oct 2025 (data starts Nov 2019)
            rows.append({"ev": name, "n": int(rs.sum()), "p": right[rs].mean(), "pv": pv, "yrs": f"{gy}/{ny}",
                         "nh": int(hd.sum()), "ph": right[hd].mean() if hd.sum() else np.nan})
        L += [f"## {tf}", "", _table(pd.DataFrame(rows), [
            ("ev", "event", str), ("n", "cases 2020-25", str), ("p", "right", _pct), ("pv", "chance it is noise", lambda v: f"{v:.3f}"),
            ("yrs", "years above 50%", str), ("nh", "holdout cases", str), ("ph", "holdout right", _pct)]), ""]
        # how big is the move after the touch holds? (the trader: "if it holds on the middle, the pump is huge")
        srows = []
        for name, k, conf in (("touch holds after a pump and sideways", 0, 0),
                              ("... and the next 2 closes stay above the middle band (measured from the 2nd)", 0, 2),
                              ("touch-and-hold without the sequence", 2, 0),
                              ("... without the sequence, next 2 closes above the middle band", 2, 2)):
            out = []
            for side in (1, -1):
                c_, h_, l_ = (t.c, t.h, t.l) if side > 0 else (-t.c, -t.l, -t.h)
                mid_ = t.mid if side > 0 else -t.mid
                for jt in np.nonzero(M[side][k])[0]:
                    if jt + conf + 1 >= t.n or not np.all(c_[jt + 1:jt + conf + 1] > mid_[jt + 1:jt + conf + 1]):
                        continue
                    j = jt + conf                                       # decision at the confirming close
                    if late[j]:
                        continue
                    top = h_[max(0, jt - 20):jt].max()                   # the pump's top (highest high of the 20 before the touch)
                    end = min(t.n, j + 31)
                    fail = next((q for q in range(j + 1, end) if c_[q] < l_[jt]), end)   # a close below the touch low
                    seg = h_[j + 1:fail] if fail > j + 1 else np.array([c_[j]])
                    run = seg.max() - c_[j]
                    out.append({"hold": bool(hold[j]), "yr": int(years[j]), "new_top": bool(seg.max() > top),
                                "run_atr": run / t.a[j], "run_pct": run / abs(c_[j]), "failed": fail < end})
            O_ = pd.DataFrame(out)
            for per, pm in (("2020 - Oct 2025", ~O_["hold"] & (O_["yr"] >= 2020)), ("holdout", O_["hold"])):
                g = O_[pm]
                if g.empty:
                    continue
                srows.append({"ev": name, "per": per, "n": len(g), "top": g["new_top"].mean(), "fail": g["failed"].mean(),
                              "med": g["run_atr"].median(), "q25": g["run_atr"].quantile(0.25), "q75": g["run_atr"].quantile(0.75),
                              "pct": g["run_pct"].median(), "big": (g["run_atr"] >= 3).mean()})
        L += [f"### {tf}: how big is the move after the touch?", "",
              "From the touch close, over the next 30 candles, until a close below the touch candle's low (that close = the hold "
              "failed). **new top** = price trades above the pump's top first. Run = the furthest price got, in ATR of the touch candle.", "",
              _table(pd.DataFrame(srows), [("ev", "event", str), ("per", "period", str), ("n", "cases", str),
                                           ("top", "new top before failing", _pct), ("fail", "hold failed within 30", _pct),
                                           ("q25", "run: lower quarter (ATR)", lambda v: f"{v:.1f}"), ("med", "run: median (ATR)", lambda v: f"{v:.1f}"),
                                           ("q75", "run: upper quarter (ATR)", lambda v: f"{v:.1f}"), ("pct", "median run %", lambda v: f"{v:.1%}"),
                                           ("big", "runs >= 3 ATR", _pct)]), ""]
        if tf == "1D":
            hu = np.nonzero(M[1][0])[0]
            L += ["Daily up-version events (touch holds after a pump and sideways): " +
                  ", ".join(str(ot[i].date()) for i in hu[-25:]), ""]
    path = out_dir / "bb_pause.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_bb_pause(load_config(ROOT / "config.yaml"), ROOT / "reports"))
