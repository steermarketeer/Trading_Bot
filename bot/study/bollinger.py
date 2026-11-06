"""
Bollinger bands in detail: when price reaches the upper band, what separates "goes higher" from "fails back"?
(Mirrored for the lower band.) Every candle that reaches the outer band is one event, decided at its close.

Outcome, from the next candle on (that timeframe's candles; a candle that does both is counted as a failure):
  continue  price travels as far beyond the event close as the close is from the middle band (symmetric, so a coin
            flip = 50%), before it trades back to the event's middle band
  fail      price trades back to the event's middle band first (or within 30 candles nothing happens: excluded)
Conditions (John Bollinger's rules, all known at the event's close):
  close outside        the close is beyond the band (a tag = only the wick reaches it). Bollinger: closes outside are
                       continuation, not reversal signals; tags are not signals at all
  walk                 3+ of the last 5 closes at / beyond the band (walking the band)
  squeeze breakout     BandWidth in the lowest 20% of the last 120 candles, 5 candles before (a squeeze), now expanding
  bulge                BandWidth in the highest 20% of the last 120 candles
  bands expanding      BandWidth higher than 3 candles ago
  opposite band turned the opposite (lower) band rising over the last 3 candles while price is at the upper band
                       (Bollinger: when the opposite band turns back after a big expansion, the move is ending)
  %b non-confirmation  a new high above the previous upper-band push of the last 20 candles, but a lower %b (M-top shape)
  volume high          volume >= 1.5x its 20-candle average
  RSI > 75             RSI(14) above 75
  upper wick           the close is in the lower half of the candle
  higher TF at band    the next higher timeframe's last closed candle is also at / beyond its outer band
  higher TF trend      the higher timeframe's close is above its EMA 50 (for the upper band)
Research = 2020 - Oct 2025; holdout = Nov 2025 on, shown separately.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..study.indicators import ema, rsi
from .defs import TF
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
HORIZON = 30
HTF = {"1h": "4h", "4h": "1D", "1D": "1W"}
RULE = {"1h": "1h", "4h": "4h", "1D": "1D", "1W": "1W"}


def events(t: TF, ht: TF, side: int) -> pd.DataFrame:
    """side +1 = upper band, -1 = lower band (mirrored so 'beyond' always means the trend direction)."""
    o, h, l, c = (t.o, t.h, t.l, t.c) if side > 0 else (-t.o, -t.l, -t.h, -t.c)
    up, lo, mid = (t.up, t.lo, t.mid) if side > 0 else (-t.lo, -t.up, -t.mid)
    a = t.a
    bw = (t.up - t.lo) / t.mid
    bw_s = pd.Series(bw)
    rank = bw_s.rolling(120, min_periods=60).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True).to_numpy()
    pb = (c - lo) / (up - lo)
    r = rsi(pd.Series(t.c)).to_numpy(float)
    r = r if side > 0 else 100 - r
    v20 = pd.Series(t.v).shift(1).rolling(20).mean().to_numpy()
    hc = ht.c if side > 0 else -ht.c
    hh = ht.h if side > 0 else -ht.l
    hup = ht.up if side > 0 else -ht.lo
    he50 = ema(pd.Series(ht.c), 50).to_numpy(float)
    he50 = he50 if side > 0 else -he50
    rows = []
    for j in range(130, t.n - 1):
        if not (h[j] >= up[j]) or not np.isfinite(a[j]):
            continue
        # outcome
        res = None
        dist = c[j] - mid[j]                                         # symmetric: as far beyond as back to the middle
        if not dist > 0:
            continue
        tgt, back = c[j] + dist, mid[j]
        for k in range(j + 1, min(t.n, j + 1 + HORIZON)):
            if l[k] <= back:
                res = 0; break
            if h[k] >= tgt:
                res = 1; break
        if res is None:
            continue
        prev = [k for k in range(j - 20, j) if h[k] >= up[k]]
        kmax = max(prev, key=lambda k: h[k]) if prev else None
        hj = ht.closed_before(t.ct[j]) - 1
        rows.append({
            "time": pd.Timestamp(t.ot[j]), "cont": res,
            "close outside": c[j] > up[j],
            "walk": sum(c[k] >= up[k] for k in range(j - 4, j + 1)) >= 3,
            "squeeze breakout": rank[j - 5] <= 0.2 and bw[j] > bw[j - 5] if np.isfinite(rank[j - 5]) else False,
            "bulge": rank[j] >= 0.8 if np.isfinite(rank[j]) else False,
            "bands expanding": bw[j] > bw[j - 3],
            "opposite band turned": lo[j] > lo[j - 3],
            "%b non-confirmation": kmax is not None and h[j] > h[kmax] and pb[j] < pb[kmax],
            "volume high": t.v[j] >= 1.5 * v20[j],
            "RSI > 75": r[j] > 75,
            "upper wick": (c[j] - l[j]) < 0.5 * (h[j] - l[j]),
            "higher TF at band": hj >= 0 and hh[hj] >= hup[hj],
            "higher TF trend": (hc[hj] > he50[hj]) if hj >= 0 and np.isfinite(he50[hj]) else None,
        })
    return pd.DataFrame(rows)


def run_bollinger(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    tfs = {k: TF(resample(df5u, RULE[k])) for k in ("1h", "4h", "1D", "1W")}
    conds = ["close outside", "walk", "squeeze breakout", "bulge", "bands expanding", "opposite band turned",
             "%b non-confirmation", "volume high", "RSI > 75", "upper wick", "higher TF at band", "higher TF trend"]
    L = ["# Bollinger bands in detail: when price reaches the outer band, does it go further or fail back?", "",
         "Every candle that reaches the upper band (and, mirrored, the lower band) on ETH. **go further** = price moves "
         "as far beyond that close as the close is from the middle band, before it comes back to the middle band (a fair, "
         "symmetric test: a coin flip would be 50%). **fail** = it comes back to the middle band first. Research 2020 - Oct 2025; the holdout (Nov 2025 on) is shown to check the pattern holds.", ""]
    allE = {}
    for tf in ("1h", "4h", "1D"):
        E = pd.concat([events(tfs[tf], tfs[HTF[tf]], s).assign(band="upper" if s > 0 else "lower") for s in (1, -1)])
        allE[tf] = E
        late_t = HOLDOUT - HORIZON * pd.Timedelta(RULE[tf])            # outcomes that would use holdout prices
        res, hol = E[E["time"] < late_t], E[E["time"] >= HOLDOUT]
        rows = []
        for cn in conds:
            for val in (True, False):
                a_, b_ = res[res[cn] == val], hol[hol[cn] == val]
                rows.append({"cond": cn if val else f"not {cn}", "n": len(a_), "p": a_["cont"].mean(), "nh": len(b_),
                             "ph": b_["cont"].mean() if len(b_) else np.nan})
        base = res["cont"].mean()
        L += [f"## {tf} ({len(res):,} band reaches 2020 - Oct 2025; price went further {base:.0%} of the time)", "",
              _table(pd.DataFrame(rows), [("cond", "at the band", str), ("n", "cases", lambda v: f"{v:,}"),
                                          ("p", "went further", _pct), ("nh", "holdout cases", str), ("ph", "holdout went further", _pct)]), ""]
        # the best and worst combinations of two conditions (>= 150 cases, holdout shown)
        combo = []
        for i, c1 in enumerate(conds):
            for c2 in conds[i + 1:]:
                for v1 in (True, False):
                    for v2 in (True, False):
                        m = (res[c1] == v1) & (res[c2] == v2)                       # None (unknown) matches neither
                        if m.sum() < 150:
                            continue
                        mh = (hol[c1] == v1) & (hol[c2] == v2)
                        combo.append({"cond": f"{'' if v1 else 'not '}{c1} + {'' if v2 else 'not '}{c2}", "n": int(m.sum()),
                                      "p": res.loc[m, "cont"].mean(), "nh": int(mh.sum()),
                                      "ph": hol.loc[mh, "cont"].mean() if mh.sum() else np.nan})
        C = pd.DataFrame(combo).sort_values("p")
        L += [f"### {tf}: the two-condition mixes where price failed most and went further most (>= 150 cases)", "",
              _table(pd.concat([C.head(6), C.tail(6)]), [("cond", "at the band", str), ("n", "cases", lambda v: f"{v:,}"),
                                                         ("p", "went further", _pct), ("nh", "holdout cases", str),
                                                         ("ph", "holdout went further", _pct)]), ""]
    pd.to_pickle(allE, ROOT / "results" / "bollinger_events.pkl")
    path = out_dir / "bollinger.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_bollinger(load_config(ROOT / "config.yaml"), ROOT / "reports"))
