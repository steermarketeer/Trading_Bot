"""
When a trendline breaks, how often does price come back and retest it? And what happens at the retest?
Six coins; 1h, 4h, 1D; rising lines (broken down) and falling lines (broken up, mirrored).

Line      through the last two confirmed swing lows with the second higher (rising; mirrored: two falling swing highs),
          fixed at the break and extended; touches = swings of the last 6 within 0.25 ATR of it
Break     the first close beyond the line by >= 0.25 ATR (the close before was not), everything from closed candles
Retest    a later candle that comes back to the line: high >= line - 0.25 ATR (for a broken rising line), within 5 / 10 / 20
          candles; before it, how far price ran away from the line (in ATR). Stricter: a retest only after price first
          moved >= 1 ATR away from the line (so a next-candle wiggle does not count)
At the retest (the first one):
  rejected  the retest candle closes back below the line (the old support acts as resistance)
  reclaimed the retest candle closes above the line + 0.25 ATR (the break failed)
After a rejected retest: does price move 1.5 ATR further away (down) before 1.5 ATR back up (the fair test)?
Research 2020 - Oct 2025, holdout Nov 2025 on.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .bb_pause_coins import COINS, month_boot
from .defs import TF
from .indicator_learn import outcome
from .mtf import resample
from .sr2_run import _table

HOLDOUT = pd.Timestamp("2025-11-01")
WIN = 20


def breaks(t: TF, side: int, y: np.ndarray, coin: str, tf: str) -> list[dict]:
    """side +1: rising lines through swing lows broken DOWN; side -1: mirrored (falling lines broken UP)."""
    if side > 0:
        h, l, c, pts = t.h, t.l, t.c, t.sl
    else:
        h, l, c, pts = -t.l, -t.h, -t.c, [(i, -p, cf) for i, p, cf in t.sh]
    arr = np.array(pts, float).reshape(-1, 3)
    a = t.a
    rows, used = [], set()
    for j in range(30, t.n - WIN - 1):
        if not np.isfinite(a[j]):
            continue
        k1 = int(np.searchsorted(arr[:, 2], j - 1, side="right"))      # swings confirmed by the candle before j
        if k1 < 2:
            continue
        (i1, p1, _), (i2, p2, _) = arr[k1 - 2], arr[k1 - 1]
        if not p2 > p1 or (i1, i2) in used:
            continue
        sl_ = (p2 - p1) / (i2 - i1)
        line = lambda x: p1 + sl_ * (x - i1)  # noqa: E731
        if not (c[j] < line(j) - 0.25 * a[j] and c[j - 1] >= line(j - 1) - 0.25 * a[j - 1]):
            continue
        if np.any(c[int(i2) + 1:j - 1] < np.array([line(x) for x in range(int(i2) + 1, j - 1)]) - 0.25 * a[int(i2) + 1:j - 1]):
            used.add((i1, i2)); continue                                # the line was already broken earlier
        used.add((i1, i2))
        touches = sum(1 for ii, pp, _ in arr[max(0, k1 - 6):k1] if abs(pp - line(ii)) <= 0.25 * a[int(ii)])
        run = (line(j) - l[j]) / a[j]                                  # the break candle counts
        rt, run_bt, rt_far, away = None, np.nan, None, run >= 1.0
        for k in range(j + 1, j + 1 + WIN):
            touch = h[k] >= line(k) - 0.25 * a[k]
            if touch and rt is None:
                rt, run_bt = k, run                                     # the first retest; the run strictly before it
            if touch and away:
                rt_far = k                                              # a retest AFTER price first moved >= 1 ATR away
                break
            run = max(run, (line(k) - l[k]) / a[j])
            if run >= 1.0:
                away = True
        run = run_bt
        yb = y[j]
        rec = {"coin": coin, "tf": tf, "side": side, "time": pd.Timestamp(t.ot[j]), "touches": touches,
               "bdist": (line(j) - c[j]) / a[j], "next": rt is not None and rt == j + 1,
               "at_break": np.nan if not np.isfinite(yb) else (1 - yb if side > 0 else yb),
               "steep": sl_ / a[j] > 0.15, "retest": rt is not None, "wait": (rt - j) if rt is not None else np.nan,
               "run": run, "result": "", "after": np.nan, "retest_far": rt_far is not None,
               "wait_far": (rt_far - j) if rt_far is not None else np.nan}
        if rt is not None:
            if c[rt] < line(rt):
                rec["result"] = "rejected"
                yy = y[rt]
                rec["after"] = np.nan if not np.isfinite(yy) else (1 - yy if side > 0 else yy)   # claim: away from the line
            elif c[rt] > line(rt) + 0.25 * a[rt]:
                rec["result"] = "reclaimed"
            else:
                rec["result"] = "closed on the line"
        rows.append(rec)
    return rows


def run_trendline_retest(cfg: Config, out_dir: Path) -> Path:
    rows = []
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        for tf in ("1h", "4h", "1D"):
            t = TF(resample(df5u, tf))
            y = outcome(t)
            for side in (1, -1):
                rows += breaks(t, side, y, sym.replace("USDT", ""), tf)
        print(sym, len(rows), flush=True)
    E = pd.DataFrame(rows)
    late = E["tf"].map({"1h": pd.Timedelta(hours=60), "4h": pd.Timedelta(hours=240), "1D": pd.Timedelta(days=60)})
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"].dt.year >= 2020) & (E["time"] < HOLDOUT - late)
    E.to_pickle(ROOT / "results" / "trendline_retest.pkl")
    f1 = lambda v: "" if v != v else f"{v:.0%}"  # noqa: E731
    out = []
    for tf in ("4h", "1h", "1D"):
        for lab, m in (("all breaks", None), ("lines with 3+ touches", "t3"), ("2-touch lines", "t2"), ("steep lines", "st")):
            g = E[E["tf"] == tf]
            if m == "t3":
                g = g[g["touches"] >= 3]
            elif m == "t2":
                g = g[g["touches"] < 3]
            elif m == "st":
                g = g[g["steep"]]
            for per, pm in (("2020 - Oct 2025", g["res"]), ("holdout", g["hold"])):
                x = g[pm]
                if x.empty:
                    continue
                r = x[x["retest"]]
                rej = r[r["result"] == "rejected"]
                fr = rej[rej["after"].notna()]
                fm, flo, fhi, _ = month_boot(fr.assign(right=fr["after"]), "right") if len(fr) else (np.nan,) * 4
                xb = x[x["at_break"].notna()]
                bm = month_boot(xb.assign(right=xb["at_break"]), "right")[0] if len(xb) else np.nan
                out.append({"tf": tf, "lab": lab, "per": per, "n": len(x),
                            "r5": (x["wait"] <= 5).mean(), "r10": (x["wait"] <= 10).mean(), "r20": x["retest"].mean(),
                            "wait": r["wait"].median() if len(r) else np.nan, "run": r["run"].median() if len(r) else np.nan,
                            "rej": (r["result"] == "rejected").mean() if len(r) else np.nan,
                            "rec": (r["result"] == "reclaimed").mean() if len(r) else np.nan,
                            "on": (r["result"] == "closed on the line").mean() if len(r) else np.nan, "after": fm,
                            "alo": flo, "ahi": fhi, "brk": bm, "nxt": x["next"].mean(),
                            "far": x["retest_far"].mean()})
    L = ["# Trendline breaks: how often does price come back to retest the line?", "",
         "Six coins (BTC, ETH, BNB, SOL, XRP, DOGE). A break = the first close beyond the line by >= 0.25 ATR; a retest = "
         "price comes back within 0.25 ATR of the extended line. Rising lines broken down and falling lines broken up "
         "(mirrored) pooled. **After a rejected retest**: right = price then moves 1.5 ATR further away from the line before "
         "1.5 ATR back (50% = coin flip).", "",
         _table(pd.DataFrame(out), [("tf", "timeframe", str), ("lab", "lines", str), ("per", "period", str), ("n", "breaks", str),
                                    ("r5", "retest within 5 candles", f1), ("r10", "within 10", f1), ("r20", "within 20", f1),
                                    ("wait", "median candles to the retest", lambda v: "" if v != v else f"{v:.0f}"),
                                    ("run", "median run away before it (ATR)", lambda v: "" if v != v else f"{v:.1f}"),
                                    ("rej", "retest rejected (closes back on the broken side)", f1),
                                    ("rec", "line reclaimed (break failed)", f1), ("on", "closed on the line", f1),
                                    ("after", "after a rejected retest: right", f1), ("alo", "90% low", f1),
                                    ("ahi", "90% high", f1), ("brk", "same test taken at the break itself", f1),
                                    ("nxt", "retested on the very next candle", f1),
                                    ("far", "retest after first moving >= 1 ATR away (within 20)", f1)]), "",
         "**Most quick retests are mechanical.** A break only has to close 0.25 ATR beyond the line, and a retest is a wick "
         "back within 0.25 ATR: when the break closes close to the line, the very next candle reaches it about as often as any "
         "ordinary candle reaches the same distance (round 18 audit: 40 - 44% observed vs 42 - 43% for ordinary candles), and "
         "it closes back on the broken side about as often as an ordinary candle at that level does. The meaningful number is "
         "the strict retest (price first moves >= 1 ATR away, then comes back). Below, by how far the break closed beyond the "
         "line:", ""]
    rows = []
    for tf in ("4h", "1h", "1D"):
        g = E[(E["tf"] == tf) & E["res"]]
        for lab, lo_, hi_ in (("0.25 - 0.5 ATR", 0.25, 0.5), ("0.5 - 1 ATR", 0.5, 1.0), ("1 ATR or more", 1.0, 99)):
            x = g[(g["bdist"] >= lo_) & (g["bdist"] < hi_)]
            rows.append({"tf": tf, "lab": lab, "n": len(x), "nxt": x["next"].mean(), "r20": x["retest"].mean(),
                         "far": x["retest_far"].mean()})
    L += [_table(pd.DataFrame(rows), [("tf", "timeframe", str), ("lab", "break close beyond the line", str), ("n", "breaks 2020-25", str),
                                      ("nxt", "retested on the next candle", f1), ("r20", "retested within 20", f1),
                                      ("far", "strict retest", f1)]), "", "Audit: round 18 (findings applied), round 19 pending."]
    path = out_dir / "trendline_retest.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_trendline_retest(load_config(ROOT / "config.yaml"), ROOT / "reports"))
