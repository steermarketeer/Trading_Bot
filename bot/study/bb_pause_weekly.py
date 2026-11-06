"""
The middle-band hold after a pump, split by the WEEKLY chart (the trader: "check the weekly graph, were they bullish or
bearish?"). Events from results/bb_pause_coins.pkl (six coins, 4h and daily; see bot/study/bb_pause_coins.py).

At each touch, the last weekly candle closed by the touch candle's close (no lookahead), seen in the pump's direction
(for a dump-side event "bullish" means bearish):
  W1  weekly close above the weekly middle band (SMA 20) and that band rising (vs 4 weeks before)
  W2  weekly close above the weekly EMA 50
  W3  weekly structure up: the last two confirmed weekly swing highs and lows both rising (HH + HL)
  The trader's explanation ("the weekly has not yet attained its highest value, so the daily consolidates, hits the
  middle, then pumps again"), fixed before looking:
  W4  the last closed weekly candle's high stayed below the weekly upper band (the weekly is not stretched)
  W5  an older weekly high, 5 - 52 weeks back, is still above the current weekly close (the weekly has not reached its
      highest value: there is a higher target / liquidity above)
  W6  weekly RSI below 70
Outcomes as before: the fair 1.5 ATR test (right) and the trader's far target (far). Holds claim the pump's direction,
failures claim the other way. Calendar-month bootstrap for the intervals; the same-distance test for the far target.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .bb_pause_coins import COINS, month_boot
from .bb_pause_why import strat_test
from .defs import TF
from .indicators import ema, rsi
from .mtf import resample
from .sr2_run import _table

TFD = {"4h": pd.Timedelta(hours=4), "1D": pd.Timedelta(days=1)}


def weekly_flags(w: TF, t_close, side: int) -> dict:
    j = w.closed_before(t_close) - 1
    out = {"W1": None, "W2": None, "W3": None, "W4": None, "W5": None, "W6": None}
    if j < 25:
        return out
    c = w.c if side > 0 else -w.c
    mid = w.mid if side > 0 else -w.mid
    e50 = ema(pd.Series(w.c), 50).to_numpy(float)
    e50 = e50 if side > 0 else -e50
    if np.isfinite(mid[j]) and np.isfinite(mid[j - 4]):
        out["W1"] = bool(c[j] > mid[j] and mid[j] > mid[j - 4])
    if np.isfinite(e50[j]):
        out["W2"] = bool(c[j] > e50[j])
    hi = w.h if side > 0 else -w.l
    upb = w.up if side > 0 else -w.lo
    if np.isfinite(upb[j]):
        out["W4"] = bool(hi[j] < upb[j])                                # the weekly has not reached its upper band
    if j >= 52:
        out["W5"] = bool(hi[j - 52:j - 4].max() > c[j])                 # an older high (5 - 52 weeks back) still above
    r = rsi(pd.Series(w.c)).to_numpy(float)
    r = r if side > 0 else 100 - r
    if np.isfinite(r[j]):
        out["W6"] = bool(r[j] < 70)
    sh = [p for i, p, cf in w.sh if cf <= j][-2:]
    sl = [p for i, p, cf in w.sl if cf <= j][-2:]
    if len(sh) == 2 and len(sl) == 2:
        if side > 0:
            out["W3"] = bool(sh[1] > sh[0] and sl[1] > sl[0])
        else:
            out["W3"] = bool(sh[1] < sh[0] and sl[1] < sl[0])
    return out


def run_bb_pause_weekly(cfg: Config, out_dir: Path) -> Path:
    E = pd.read_pickle(ROOT / "results" / "bb_pause_coins.pkl")
    W = {}
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        W[sym.replace("USDT", "")] = TF(resample(df5u, "1W"))
    fl = [weekly_flags(W[r.coin], r.time + TFD[r.tf], int(r.side)) for r in E.itertuples()]
    E = pd.concat([E.reset_index(drop=True), pd.DataFrame(fl)], axis=1)
    E.to_pickle(ROOT / "results" / "bb_pause_weekly.pkl")
    names = {"W1": "weekly above its rising middle band", "W2": "weekly above its EMA 50", "W3": "weekly structure HH + HL",
             "W4": "weekly has NOT reached its upper band", "W5": "an older weekly high (5-52 weeks back) still above price",
             "W6": "weekly RSI below 70"}
    L = ["# The middle-band hold, split by the weekly chart (six coins)", "",
         "Each weekly reading is seen in the pump's direction; \"yes\" = the reading is true. W1 - W3 = the weekly points the same way as the pump (bullish weekly for a pump up, bearish for a "
         "pump down). **right** = the fair test (1.5 ATR either way; 50% = coin flip); **far** = the trader's target (hold: a "
         "new high above everything so far; fail: the sideways low). 90% intervals by a bootstrap of calendar months. "
         "Research 2020 - Oct 2025, holdout Nov 2025 on.", ""]
    rows = []
    f1 = lambda v: "" if v != v else f"{v:.0%}"  # noqa: E731
    for tf in ("1D", "4h"):
        for kind, hm in (("hold -> pump again", True), ("fail -> dump", False)):
            for w in ("W1", "W2", "W3", "W4", "W5", "W6"):
                for val, lab in ((True, "yes"), (False, "no")):
                    g = E[(E["tf"] == tf) & (E["held"] == hm) & (E[w] == val)]
                    res, hol = g[g["res"]], g[g["hold"]]
                    mu, lo, hi, p = month_boot(res, "right")
                    rows.append({"tf": tf, "kind": kind, "w": names[w], "lab": lab, "n": len(res), "right": mu, "lo": lo,
                                 "hi": hi, "far": res["far"].mean() if len(res) else np.nan, "nh": len(hol),
                                 "rh": hol["right"].mean() if len(hol) else np.nan,
                                 "fh": hol["far"].mean() if len(hol) else np.nan})
    L += [_table(pd.DataFrame(rows), [("tf", "timeframe", str), ("kind", "event", str), ("w", "weekly reading", str),
                                      ("lab", "", str), ("n", "cases 2020-25", str), ("right", "right (fair)", f1),
                                      ("lo", "90% low", f1), ("hi", "90% high", f1), ("far", "far target", f1),
                                      ("nh", "holdout cases", str), ("rh", "holdout right", f1), ("fh", "holdout far", f1)]), ""]
    # with vs against at the same distances (far target), and the fair-test difference
    rows = []
    for tf in ("1D", "4h"):
        for kind, hm in (("hold -> pump again", True), ("fail -> dump", False)):
            g = E[(E["tf"] == tf) & (E["held"] == hm)].copy()
            g["tf"] = g["tf_c"]
            res, hol = g[g["res"]].sort_values("time"), g[g["hold"]]
            for w in ("W1", "W2", "W3", "W4", "W5", "W6"):
                a_, a0 = res[res[w] == True], res[res[w] == False]  # noqa: E712
                if len(a_) < 15 or len(a0) < 15:
                    continue
                d, pv = strat_test(res, w)
                rows.append({"tf": tf, "kind": kind, "w": names[w], "fair": a_["right"].mean() - a0["right"].mean(),
                             "raw": a_["far"].mean() - a0["far"].mean(), "d": d, "pv": pv,
                             "dh": strat_test(hol, w, n_perm=0, min_n=20, min_mixed=20)[0]})
    f2 = lambda v: "" if v != v else f"{v * 100:+.0f} pts"  # noqa: E731
    L += ["## Reading true minus false", "",
          "Six tests per row group; the weekly readings overlap (they mostly agree), so they are not independent tests.", "",
          _table(pd.DataFrame(rows), [("tf", "timeframe", str), ("kind", "event", str), ("w", "weekly reading", str),
                                      ("fair", "fair test: difference", f2), ("raw", "far: raw difference", f2),
                                      ("d", "far: same distances", f2), ("pv", "noise", lambda v: "" if v != v else f"{v:.3f}"),
                                      ("dh", "holdout, same distances", f2)]), ""]
    path = out_dir / "bb_pause_weekly.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_bb_pause_weekly(load_config(ROOT / "config.yaml"), ROOT / "reports"))
