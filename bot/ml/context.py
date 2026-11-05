"""
Main-rule context for every candidate trade, read across timeframes at the decision time (no hindsight).

Only MAIN RULES go in here (structure, levels, trendline/concept events, liquidity, patterns, weekly trend,
volatility regime). Indicators belong to layer 2.

Features (all relative to the trade direction d: +1 = agrees, -1 = against, 0 = neutral):
  st_<tf>            structure state from the last 2 confirmed swing highs and lows (HH+HL up, LH+LL down)
  brk_<tf>           last close through a confirmed swing within 20 candles: +1 in trade direction, -1 against
  brk_choch_<tf>     that break was a change of character (against the prior structure)
  pat_<tf>           most recent completed chart pattern (H&S, double top/bottom, triangle) within 10 candles
  ev_<tf>_<family>   other main-rule events on that timeframe in the last 3 candles: same-direction minus opposite
  zone_ahead_atr     distance to the nearest strong zone on the target side, in ATR of the trade timeframe
  zone_behind_atr    distance to the nearest strong zone on the stop side
  zones_in_path      strong zones between entry and the 2R target
  zone_touches       swings forming the nearest zone (strength)
  at_zone            entry within 0.5 ATR of a strong zone
  liq_in_risk        confirmed swings (1h + own TF, last 100 candles) between stop and entry
  pool_near_stop     equal highs/lows within 0.5 ATR of the stop
  liq_in_path        untaken swings between entry and the 2R target
  wtrend             weekly trend (bot/study/trend rule) vs the trade
  vol_regime         ATR% percentile of the trade timeframe over the previous 365 days
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..study.concepts import Bars
from ..study.levels import _level_table, strong_levels
from ..study.mtf import resample
from ..study.patterns import detect_patterns
from ..study.trend import add_weekly_trend

STRUCT_TFS = ("1h", "2h", "4h", "12h", "1D", "1W")
PATTERN_TFS = ("4h", "1D", "1W")
EVENT_TFS = ("2h", "4h", "1D")
REVERSAL = {"zone_bounce", "tl_bounce", "liq_sweep", "choch", "level_test_bounce"}


def _rule(tf):
    return "W-MON" if tf == "1W" else tf


def structure_table(df5: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Per closed candle: structure state, and the last swing break (dir, choch flag, candle index)."""
    bars = Bars(resample(df5, _rule(tf)))
    c = bars.c
    sh, sl = bars.sh, bars.sl
    n = bars.n
    hi_i = lo_i = 0
    highs, lows = [], []
    state = np.zeros(n)
    brk_dir = np.zeros(n)
    brk_ch = np.zeros(n)
    brk_at = np.full(n, -10**9)
    last_dir, last_ch, last_at = 0.0, 0.0, -10**9
    used = set()
    for t in range(n):
        while hi_i < len(sh) and sh[hi_i][2] <= t:
            highs.append((sh[hi_i][0], sh[hi_i][1]))
            hi_i += 1
        while lo_i < len(sl) and sl[lo_i][2] <= t:
            lows.append((sl[lo_i][0], sl[lo_i][1]))
            lo_i += 1
        s = 0
        if len(highs) >= 2 and len(lows) >= 2:
            if highs[-1][1] > highs[-2][1] and lows[-1][1] > lows[-2][1]:
                s = 1
            elif highs[-1][1] < highs[-2][1] and lows[-1][1] < lows[-2][1]:
                s = -1
        state[t] = s
        if t > 0 and highs and c[t] > highs[-1][1] >= c[t - 1] and ("H", highs[-1][0]) not in used:
            used.add(("H", highs[-1][0]))
            last_dir, last_ch, last_at = 1.0, float(s == -1), t
        if t > 0 and lows and c[t] < lows[-1][1] <= c[t - 1] and ("L", lows[-1][0]) not in used:
            used.add(("L", lows[-1][0]))
            last_dir, last_ch, last_at = -1.0, float(s == 1), t
        brk_dir[t], brk_ch[t], brk_at[t] = last_dir, last_ch, last_at
    age = np.arange(n) - brk_at
    return pd.DataFrame({"close_time": bars.ct.dt.tz_convert(None).dt.as_unit("ns"), "state": state,
                         "brk_dir": np.where(age <= 20, brk_dir, 0.0), "brk_ch": np.where(age <= 20, brk_ch, 0.0),
                         "atr_pct": bars.a / bars.c})


def pattern_table(df5: pd.DataFrame, tf: str) -> pd.DataFrame:
    b = resample(df5, _rule(tf)).reset_index(drop=True)
    b["day"] = b["open_time"].astype(str)
    ev = detect_patterns(b)
    if ev.empty:
        return pd.DataFrame(columns=["known", "direction"])
    ct = b.set_index("day")["close_time"]
    return pd.DataFrame({"known": pd.to_datetime(ev["day"].map(ct), utc=True).dt.tz_convert(None).dt.as_unit("ns"),
                         "direction": ev["direction"].to_numpy(float)}).sort_values("known")


class RMQ:
    """Sparse-table range max / min over an array (for 'has this swing been taken out since?')."""

    def __init__(self, a: np.ndarray, op):
        self.op = op
        self.t = [a.astype(float)]
        k = 1
        while (1 << k) <= len(a):
            p = self.t[-1]
            self.t.append(op(p[:-(1 << (k - 1))], p[(1 << (k - 1)):]))
            k += 1

    def q(self, i, j):  # inclusive i..j-1
        if j <= i:
            return np.nan
        k = int(np.log2(j - i))
        return float(self.op(self.t[k][i], self.t[k][j - (1 << k)]))


def build_context(cand: pd.DataFrame, df5: pd.DataFrame, all_events: pd.DataFrame) -> pd.DataFrame:
    """cand: decision_time (UTC-naive), tf, direction, entry, risk, atr (trade TF ATR, price units), event."""
    t = cand.copy()
    t["_r"] = np.arange(len(t))
    t["_t"] = pd.to_datetime(t["decision_time"]).dt.as_unit("ns")
    d = t["direction"].to_numpy(float)
    out = pd.DataFrame(index=t.index)
    ts = t.sort_values("_t")
    # structure per timeframe
    for tf in STRUCT_TFS:
        st = structure_table(df5, tf)
        m = pd.merge_asof(ts[["_t", "_r"]], st, left_on="_t", right_on="close_time", direction="backward").sort_values("_r")
        out[f"st_{tf}"] = m["state"].fillna(0).to_numpy() * d
        out[f"brk_{tf}"] = m["brk_dir"].fillna(0).to_numpy() * d
        out[f"brk_choch_{tf}"] = m["brk_ch"].fillna(0).to_numpy()
    # patterns
    for tf in PATTERN_TFS:
        pt = pattern_table(df5, tf)
        bar = pd.Timedelta("7D") if tf == "1W" else pd.Timedelta(tf)
        if pt.empty:
            out[f"pat_{tf}"] = 0.0
            continue
        kn = pt["known"].to_numpy()
        dr = pt["direction"].to_numpy()
        vals = np.zeros(len(t))
        for n_, (tt, dd) in enumerate(zip(t["_t"].to_numpy(), d)):
            i = np.searchsorted(kn, tt, side="right") - 1
            if i >= 0 and tt - kn[i] <= np.timedelta64(int((10 * bar).value), "ns"):
                vals[n_] = dr[i] * dd
        out[f"pat_{tf}"] = vals
    # other main-rule events, other timeframes, last 3 candles
    ae = all_events.copy()
    ae["_t"] = pd.to_datetime(ae["decision_time"]).dt.as_unit("ns")
    ae["fam"] = np.where(ae["event"].isin(REVERSAL), "rev", "brk")
    for tf in EVENT_TFS:
        bar = np.timedelta64(int((3 * pd.Timedelta(tf)).value), "ns")
        for fam in ("brk", "rev"):
            g = ae[(ae["tf"] == tf) & (ae["fam"] == fam)].sort_values("_t")
            tk, dk = g["_t"].to_numpy(), g["direction"].to_numpy(float)
            cs = np.r_[0, np.cumsum(dk)]
            cnt = np.r_[0, np.cumsum(np.ones_like(dk))]
            tt = t["_t"].to_numpy()
            hi = np.searchsorted(tk, tt, side="right")
            lo = np.searchsorted(tk, tt - bar, side="right")
            s = (cs[hi] - cs[lo]) * d
            # remove the candidate itself when it belongs to this group
            own = ((t["tf"].to_numpy() == tf) & (np.where(t["event"].isin(REVERSAL), "rev", "brk") == fam))
            out[f"ev_{tf}_{fam}"] = s - own.astype(float)
    # zones
    table = _level_table(df5)
    e, rk, a = t["entry"].to_numpy(float), t["risk"].to_numpy(float), t["atr"].to_numpy(float)
    za, zb, zp, zt, az = (np.full(len(t), np.nan) for _ in range(5))
    for n_, tt in enumerate(t["_t"]):
        tu = pd.Timestamp(tt).tz_localize("UTC")
        z = strong_levels(table, tu)
        if not len(z) or not np.isfinite(e[n_]) or a[n_] <= 0:
            continue
        rel = (z - e[n_]) * d[n_]
        ahead, behind = rel[rel > 0], -rel[rel < 0]
        za[n_] = ahead.min() / a[n_] if len(ahead) else 20.0
        zb[n_] = behind.min() / a[n_] if len(behind) else 20.0
        zp[n_] = float(((rel > 0) & (rel < 2 * rk[n_])).sum())
        near = z[np.argmin(np.abs(z - e[n_]))]
        known = table[(table["known"] <= tu) & (table["formed"] >= tu - table["lookback"])]  # no future swings
        zt[n_] = float(((known["price"] - near).abs() / near < 0.01).sum())
        az[n_] = float(np.abs(z - e[n_]).min() <= 0.5 * a[n_])
    out["zone_ahead_atr"], out["zone_behind_atr"], out["zones_in_path"] = za, zb, zp
    out["zone_touches"], out["at_zone"] = zt, az
    # liquidity (1h swings + own TF swings), fast
    b1 = Bars(resample(df5, "1h"))
    h1t = b1.ot.dt.tz_convert(None).to_numpy()
    rmax, rmin = RMQ(b1.h, np.maximum), RMQ(b1.l, np.minimum)
    sw = {}
    for tf in ("1h", "2h", "4h", "1D"):
        bb = b1 if tf == "1h" else Bars(resample(df5, tf))
        ct = bb.ct.dt.tz_convert(None).to_numpy()
        ot = bb.ot.dt.tz_convert(None).to_numpy()
        sw[tf] = {k: (np.array([ot[i] for i, _, _ in pts]), np.array([p for _, p, _ in pts]),
                      np.array([ct[cf] for _, _, cf in pts]))
                  for k, pts in (("H", bb.sh), ("L", bb.sl))}
    lir, pns, lip = np.zeros(len(t)), np.zeros(len(t)), np.zeros(len(t))
    for n_, (tt, tf, dd) in enumerate(zip(t["_t"].to_numpy(), t["tf"], d)):
        if not np.isfinite(e[n_]) or rk[n_] <= 0:
            continue
        stop, tgt = e[n_] - dd * rk[n_], e[n_] + dd * 2 * rk[n_]
        own_side, tgt_side = ("L", "H") if dd > 0 else ("H", "L")
        prices_own, path = [], []
        for tfx in ("1h", tf):
            bar = np.timedelta64(int((100 * pd.Timedelta(tfx)).value), "ns")
            f, p, k = sw[tfx][own_side]
            m = (k <= tt) & (f >= tt - bar)
            prices_own.append(p[m])
            f2, p2, k2 = sw[tfx][tgt_side]
            m2 = (k2 <= tt) & (f2 >= tt - bar)
            i_now = np.searchsorted(h1t, tt)
            for ff, pp in zip(f2[m2], p2[m2]):
                i0 = np.searchsorted(h1t, ff) + 1
                ext = rmax.q(i0, i_now) if dd > 0 else rmin.q(i0, i_now)
                taken = (ext > pp) if dd > 0 else (ext < pp)
                if not (ext == ext and taken):
                    path.append(pp)
        po = np.unique(np.concatenate(prices_own)) if prices_own else np.array([])
        lo_, hi_ = sorted((stop, e[n_]))
        lir[n_] = float(((po > lo_) & (po < hi_)).sum())
        srt = np.sort(po)
        pools = (srt[1:] + srt[:-1]) / 2 if len(srt) > 1 else np.array([])
        pools = pools[np.diff(srt) <= 0.25 * a[n_]] if len(srt) > 1 else pools
        pns[n_] = float((np.abs(pools - stop) <= 0.5 * a[n_]).any()) if len(pools) else 0.0
        pa = np.array(path)
        a2, b2 = sorted((e[n_], tgt))
        lip[n_] = float(((pa > a2) & (pa < b2)).sum()) if len(pa) else 0.0
    out["liq_in_risk"], out["pool_near_stop"], out["liq_in_path"] = lir, pns, lip
    # weekly trend
    dd_ = resample(df5, "1D").rename(columns={"open_time": "ts"})
    dd_["day"] = dd_["ts"].dt.strftime("%Y-%m-%d")
    wt = add_weekly_trend(dd_)[["close_time", "weekly_trend"]]
    wt["close_time"] = pd.to_datetime(wt["close_time"], utc=True).dt.tz_convert(None).dt.as_unit("ns")
    m = pd.merge_asof(ts[["_t", "_r"]], wt.sort_values("close_time"), left_on="_t", right_on="close_time",
                      direction="backward").sort_values("_r")
    out["wtrend"] = m["weekly_trend"].map({"Up": 1.0, "Down": -1.0}).fillna(0).to_numpy() * d
    # volatility regime: ATR% percentile vs trailing year, per timeframe
    vr = np.full(len(t), np.nan)
    for tf in t["tf"].unique():
        st = structure_table(df5, tf)[["close_time", "atr_pct"]].dropna()
        win = {"2h": 4380, "4h": 2190, "1D": 365}.get(tf, 365)
        st["pct"] = st["atr_pct"].rolling(win, min_periods=win // 4).apply(lambda x: (x[-1] >= x).mean(), raw=True)
        g = ts[ts["tf"] == tf][["_t", "_r"]]
        m = pd.merge_asof(g, st[["close_time", "pct"]], left_on="_t", right_on="close_time", direction="backward")
        vr[m["_r"].to_numpy()] = m["pct"].to_numpy()
    out["vol_regime"] = vr
    return out
