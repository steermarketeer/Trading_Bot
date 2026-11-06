"""
The trader's version: from the upper band price goes sideways, touches the middle band, KEEPS ON THE UPPER SIDE of the
middle line, then a pump comes. Six coins, 4h and daily, mirrored for dumps.

Events: the 'touch holds' events of bot/study/bb_pause.py masks() (a pump close beyond the outer band, >= 3 closes above
the middle band, the first touch of the middle band, closing back above it). "Keeps on the upper side": the next N closes
(N = 1, 2, 3, 5) are all above the middle band; the decision is made at the N-th close (nothing after it is used).
Outcomes from the decision close:
  pump     a new high above every high of the 40 candles before the touch and everything up to the decision (this covers
           the pump and 20 candles before it; the same window is used for the comparison group, which has no pump)
           before a close 0.5 ATR below the middle band, within 30 candles
  fair     1.5 ATR up before 1.5 ATR down, within 30 candles (a coin flip = 50%)
Comparison: every other touch of the middle band that closes above it (not a first touch after a pump and sideways),
followed by the same number of closes above the middle band (does the trader's sequence add anything?).
Research 2020 - Oct 2025, holdout Nov 2025 on; 90% intervals from a bootstrap of calendar months (coins move together).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .bb_pause import masks
from .bb_pause_coins import COINS, month_boot, strat_boot
from .bb_pause_why import strat_test
from .defs import TF
from .indicator_learn import outcome
from .mtf import resample
from .sr2_run import _table

HOLDOUT = pd.Timestamp("2025-11-01")
WIN = 30
NS = (1, 2, 3, 5)


def scan(t: TF, side: int, y: np.ndarray, coin: str, tf: str) -> list[dict]:
    c, h, l = (t.c, t.h, t.l) if side > 0 else (-t.c, -t.l, -t.h)
    mid = t.mid if side > 0 else -t.mid
    a = t.a
    holds, _, _ = masks(t, side)
    touch = np.zeros(t.n, bool)
    for j in range(1, t.n):
        touch[j] = np.isfinite(a[j]) and np.isfinite(mid[j]) and l[j] <= mid[j] + 0.25 * a[j] and c[j] > mid[j]
    rows = []
    for q in range(30, t.n):
        if not touch[q]:
            continue
        seq = bool(holds[q])
        for N in NS:
            j = q + N
            if j + WIN >= t.n:
                break
            if not np.all(c[q + 1:j + 1] > mid[q + 1:j + 1]):
                break                                                    # did not keep on the upper side for N closes
            top = h[max(0, q - 40):j + 1].max()
            fail = mid[j] - 0.5 * a[j]
            pump = False
            for z in range(j + 1, j + 1 + WIN):
                if h[z] > top:
                    pump = True; break
                if c[z] < mid[z] - 0.5 * a[z]:
                    break
            yy = y[j]
            fair = np.nan if not np.isfinite(yy) else (yy if side > 0 else 1 - yy)
            rows.append({"coin": coin, "tf": tf, "side": side, "N": N, "seq": seq, "time": pd.Timestamp(t.ot[j]),
                         "pump": float(pump), "right": fair, "d_top": (top - c[j]) / a[j], "d_fail": (c[j] - fail) / a[j]})
    return rows


def run_bb_pause_stay(cfg: Config, out_dir: Path) -> Path:
    rows = []
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        for tf in ("4h", "1D"):
            t = TF(resample(df5u, tf))
            y = outcome(t)
            for side in (1, -1):
                rows += scan(t, side, y, sym.replace("USDT", ""), tf)
        print(sym, len(rows), flush=True)
    E = pd.DataFrame(rows)
    late = E["tf"].map({"4h": pd.Timedelta(hours=4 * WIN), "1D": pd.Timedelta(days=WIN)})
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"].dt.year >= 2020) & (E["time"] < HOLDOUT - late)
    E.to_pickle(ROOT / "results" / "bb_pause_stay.pkl")
    out = []
    f1 = lambda v: "" if v != v else f"{v:.0%}"  # noqa: E731
    for tf in ("1D", "4h"):
        for N in NS:
            for lab, sm in (("after a pump and sideways (the trader's sequence)", True), ("without the sequence", False)):
                g = E[(E["tf"] == tf) & (E["N"] == N) & (E["seq"] == sm)]
                res, hol = g[g["res"]], g[g["hold"]]
                pm, plo, phi, _ = month_boot(res, "pump")
                fr = res[res["right"].notna()]
                fm, flo, fhi, fp = month_boot(fr, "right")
                out.append({"tf": tf, "N": N, "lab": lab, "n": len(res), "pump": pm, "plo": plo, "phi": phi,
                            "dtop": res["d_top"].median(), "dfail": res["d_fail"].median(),
                            "fair": fm, "flo": flo, "fhi": fhi, "nh": len(hol),
                            "ph": hol["pump"].mean() if len(hol) else np.nan,
                            "fh": hol["right"].mean() if len(hol) else np.nan})
    L = ["# Touches the middle band, keeps on the upper side, then a pump?", "",
         "Six coins (BTC, ETH, BNB, SOL, XRP, DOGE), mirrored for dumps. Decision at the N-th close after the touch, all of "
         "them above the middle band. **pump** = a new high above everything so far before a close 0.5 ATR below the middle "
         "band (30 candles). **fair** = 1.5 ATR up before 1.5 ATR down (50% = coin flip). The pump rate depends on how far the "
         "old high and the failure level are (median distances shown, in ATR), so compare the two rows of each pair, not the "
         "pump rate with 50%. 90% intervals: bootstrap of calendar months.", "",
         _table(pd.DataFrame(out), [
             ("tf", "timeframe", str), ("N", "closes above the middle after the touch", str), ("lab", "", str),
             ("n", "cases 2020-25", str), ("pump", "pump", f1), ("plo", "90% low", f1), ("phi", "90% high", f1),
             ("dtop", "distance to the old high", lambda v: f"{v:.1f}"), ("dfail", "distance to the failure level", lambda v: f"{v:.1f}"),
             ("fair", "fair test", f1), ("flo", "90% low", f1), ("fhi", "90% high", f1),
             ("nh", "holdout cases", str), ("ph", "holdout pump", f1), ("fh", "holdout fair", f1)]), "",
         ""]
    rows = []
    X = E.rename(columns={"pump": "far", "d_top": "d_target"})
    for tf in ("1D", "4h"):
        for N in NS:
            g = X[(X["tf"] == tf) & (X["N"] == N)]
            res, hol = g[g["res"]].sort_values("time"), g[g["hold"]]
            d, p = strat_boot(res, "seq", n=200)
            dh = strat_test(hol, "seq", n_perm=0, min_n=20, min_mixed=20)[0]
            rows.append({"tf": tf, "N": N, "d": d, "p": p, "dh": dh})
    f2 = lambda v: "" if v != v else f"{v * 100:+.1f} pts"  # noqa: E731
    L += ["## Does the trader's sequence add anything at the same distances?", "",
          "Pump rate of the sequence minus ordinary middle-band holds, within groups of the same timeframe, distance to the old "
          "high and distance to the failure level (quintiles); p by a bootstrap of calendar months.", "",
          _table(pd.DataFrame(rows), [("tf", "timeframe", str), ("N", "closes above the middle", str),
                                      ("d", "sequence minus without, same distances", f2),
                                      ("p", "noise", lambda v: "" if v != v else f"{v:.3f}"), ("dh", "holdout, same distances", f2)]),
          "", "Audit: pending."]
    path = out_dir / "bb_pause_stay.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_bb_pause_stay(load_config(ROOT / "config.yaml"), ROOT / "reports"))
