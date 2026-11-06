"""
Every indicator in detail (the Bollinger study, done for all of them): for each indicator's key situation, which
conditions make it work and which make it fail. Mirrored for the other direction; everything known at the event close.

Fair outcome (same as reports/indicator_learn.md): from the event close, does price move 1.5 ATR the way the event
claims before 1.5 ATR against (30 candles max)? A coin flip = 50%.

Events (the claim is "up" for the bullish version):
  RSI enters 70        RSI(14) crosses above 70 (momentum reading)
  RSI leaves 70        RSI crosses back below 70 after being above (the "overbought is over" reading: claim = down)
  MACD bull cross      MACD line crosses above its signal
  EMA 20 pullback      EMA 20 > EMA 50, the low reaches the EMA 20 and the candle closes above it
  EMA 50 pullback      EMA 50 > EMA 200, the low reaches the EMA 50 and the candle closes above it
  Volume breakout      a close above the highest high of the previous 20 candles
  Fib pullback         in an up-leg (confirmed swing low -> highest high since, >= 3 ATR), the first candle whose low
                       reaches a retracement (0.382 / 0.5 / 0.618 / 0.786, within 0.25 ATR) and closes back above it
  Trendline rejection  the line through the last two confirmed swing lows (rising): the low touches it (within 0.25 ATR)
                       and the candle closes above it
  Trendline break      the same line: a close below it by >= 0.25 ATR (claim = down)
Conditions: the indicator's own details (divergence, zero line, slope, volume on the pullback, which Fib level,
confluence, touches, ...) and the shared context (daily EMA 200 trend, 4h / daily structure, Bollinger bulge, RSI,
volume, liquidity close ahead).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.manager import context_table
from .defs import TF
from .indicator_learn import outcome
from .indicators import ema, ichimoku, macd, rsi
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
HTF = {"1h": "4h", "4h": "1D", "1D": "1W"}


class Oriented:
    """Arrays of one timeframe seen from one side (side -1 = mirrored, so 'up' is always the claim)."""

    def __init__(self, t: TF, side: int, cx: dict):
        self.t, self.s = t, side
        if side > 0:
            self.o, self.h, self.l, self.c = t.o, t.h, t.l, t.c
            self.up, self.lo, self.mid = t.up, t.lo, t.mid
            self.sl, self.sh = t.sl, t.sh
        else:
            self.o, self.h, self.l, self.c = -t.o, -t.l, -t.h, -t.c
            self.up, self.lo, self.mid = -t.lo, -t.up, -t.mid
            self.sl, self.sh = [(i, -p, cf) for i, p, cf in t.sh], [(i, -p, cf) for i, p, cf in t.sl]
        s = pd.Series(self.c)
        self.e20, self.e50, self.e200 = (ema(s, k).to_numpy(float) for k in (20, 50, 200))
        ml, ms = (x.to_numpy(float) for x in macd(s))
        self.ml, self.ms, self.mh = ml, ms, ml - ms
        r = rsi(pd.Series(t.c)).to_numpy(float)
        self.r = r if side > 0 else 100 - r
        self.v = t.v
        self.v20 = pd.Series(t.v).shift(1).rolling(20).mean().to_numpy()
        self.a = t.a
        bw = (t.up - t.lo) / t.mid
        self.bw = bw
        self.rank = pd.Series(bw).rolling(120, min_periods=60).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True).to_numpy()
        self.cx = cx[side]
        self.hi20 = pd.Series(self.h).shift(1).rolling(20).max().to_numpy()
        tk, kj, top, bot, fa, fb = (x.to_numpy(float) for x in ichimoku(t.b))
        if side > 0:
            self.tk, self.kj, self.ctop, self.cbot, self.fa, self.fb = tk, kj, top, bot, fa, fb
        else:                                                           # Ichimoku is symmetric under negation
            self.tk, self.kj, self.ctop, self.cbot, self.fa, self.fb = -tk, -kj, -bot, -top, -fa, -fb
        self.sl_arr = np.array([(i, p, cf) for i, p, cf in self.sl], float).reshape(-1, 3)
        self.sh_arr = np.array([(i, p, cf) for i, p, cf in self.sh], float).reshape(-1, 3)


def _last_swings(arr, j, n):
    k = int(np.searchsorted(arr[:, 2], j, side="right"))
    return arr[max(0, k - n):k]


def common(O: Oriented, j, trend, htf_trend):
    cx = O.cx
    return {"with the daily trend (EMA 200)": trend, "higher timeframe above its EMA 50": htf_trend,
            "structure up (HH + HL)": cx["struct"][j] > 0, "Bollinger bulge": O.rank[j] >= 0.8,
            "bands expanding": O.bw[j] > O.bw[j - 3], "RSI > 60": O.r[j] > 60, "volume >= 1.5x": O.v[j] >= 1.5 * O.v20[j],
            "liquidity ahead within 1 ATR": cx["liq_ahead"][j] <= 1.0, "close in the top quarter of the candle":
                (O.c[j] - O.l[j]) >= 0.75 * (O.h[j] - O.l[j]) if O.h[j] > O.l[j] else False}


def detect(O: Oriented, j):
    """All events at candle j (claim up for this orientation): list of (event, claim, specific conditions)."""
    out = []
    a, c, h, l, r = O.a[j], O.c, O.h, O.l, O.r
    if not np.isfinite(a) or a <= 0:
        return out
    # ---------------- RSI
    if r[j] > 70 >= r[j - 1]:
        prev_peak = np.nanmax(r[max(0, j - 30):j - 5]) if j > 35 else np.nan
        out.append(("RSI enters 70", 1, {
            "bearish divergence (higher high, lower RSI peak)": bool(h[j] >= np.max(h[j - 30:j]) and prev_peak > r[j]),
            "first time above 70 in 50 candles": not (r[j - 50:j] > 70).any(),
            "close outside the upper band": c[j] > O.up[j],
            "stretched > 2 ATR above EMA 20": (c[j] - O.e20[j]) / a > 2}))
    if r[j] < 70 <= r[j - 1]:
        out.append(("RSI leaves 70", -1, {
            "RSI failure swing (lower peak, then below the trough)": _failure_swing(r, j),
            "close back inside the upper band": c[j] <= O.up[j] and c[j - 1] > O.up[j - 1],
            "stayed above 70 for 5+ candles": (r[j - 5:j] > 70).all()}))
    # ---------------- MACD
    if O.ml[j] > O.ms[j] and O.ml[j - 1] <= O.ms[j - 1]:
        lows = _last_swings(O.sl_arr, j, 2)
        div = len(lows) == 2 and lows[1, 1] < lows[0, 1] and O.ml[int(lows[1, 0])] > O.ml[int(lows[0, 0])] and j - lows[1, 2] <= 10
        out.append(("MACD bull cross", 1, {
            "above the zero line": O.ml[j] > 0, "after a bullish divergence (10 candles)": bool(div),
            "at support (untaken low within 1 ATR below)": O.cx["liq_behind"][j] <= 1.0,
            "histogram was deep (< -0.5 ATR)": np.nanmin(O.mh[j - 10:j]) / a < -0.5}))
    # ---------------- EMA pullbacks
    for name, fast, slow in (("EMA 20 pullback", O.e20, O.e50), ("EMA 50 pullback", O.e50, O.e200)):
        if fast[j] > slow[j] and l[j] <= fast[j] and c[j] > fast[j] and not (l[j - 1] <= fast[j - 1]):
            k0 = max(0, j - 15)
            push = int(np.argmax(h[k0:j])) + k0
            out.append((name, 1, {
                "EMA 50 rising strongly (> 0.1 ATR per candle)": (O.e50[j] - O.e50[j - 10]) / (10 * a) > 0.1,
                "stacked 20 > 50 > 200": O.e20[j] > O.e50[j] > O.e200[j],
                "pullback volume below the push volume": O.v[j] < O.v[push],
                "RSI 40 - 50 at the touch (Cardwell)": 40 <= r[j] <= 50,
                "wick rejection (close in the top third)": (c[j] - l[j]) >= 0.67 * (h[j] - l[j]) if h[j] > l[j] else False,
                "first touch in 20 candles": not ((l[j - 20:j - 1] <= fast[j - 20:j - 1])).any()}))
    # ---------------- moving averages, more
    if O.e200[j] > O.e200[j - 10] and l[j] <= O.e200[j] and c[j] > O.e200[j] and not (l[j - 1] <= O.e200[j - 1]):
        out.append(("EMA 200 test (rising 200)", 1, {
            "first touch in 50 candles": not (l[j - 50:j - 1] <= O.e200[j - 50:j - 1]).any(),
            "EMA 20 still above EMA 200": O.e20[j] > O.e200[j],
            "wick rejection (close in the top third)": (c[j] - l[j]) >= 0.67 * (h[j] - l[j]) if h[j] > l[j] else False}))
    if O.e20[j] > O.e50[j] and O.e20[j - 1] <= O.e50[j - 1]:
        out.append(("EMA 20 crosses above 50", 1, {
            "price above EMA 200": c[j] > O.e200[j], "both EMAs rising": O.e20[j] > O.e20[j - 3] and O.e50[j] > O.e50[j - 3],
            "volume >= 1.5x on the cross": O.v[j] >= 1.5 * O.v20[j]}))
    if c[j] > O.e20[j] and (c[j - 6:j] < O.e20[j - 6:j]).all():
        out.append(("Reclaim EMA 20 (after 6+ closes below)", 1, {
            "EMA 50 above EMA 200 (pullback in an uptrend)": O.e50[j] > O.e200[j],
            "close above the 20 by > 0.5 ATR": (c[j] - O.e20[j]) / a > 0.5}))
    st = (c[j] - O.e20[j]) / a
    if st > 3 and (c[j - 1] - O.e20[j - 1]) / O.a[j - 1] <= 3:
        out.append(("Stretched > 3 ATR above EMA 20", -1, {
            "RSI > 80": r[j] > 80, "Bollinger bulge (top 20% width)": O.rank[j] >= 0.8,
            "volume >= 2x (climax?)": O.v[j] >= 2 * O.v20[j]}))
    # ---------------- candlesticks (bullish shapes; the mirror gives the bearish ones)
    rng = h[j] - l[j]
    if rng > 0:
        body = abs(c[j] - O.o[j])
        lw = min(O.o[j], c[j]) - l[j]
        uw = h[j] - max(O.o[j], c[j])
        down10 = c[j - 1] < c[j - 11]
        ctx = {"after a decline (10 candles down)": bool(down10), "at the lower band (low <= lower band)": l[j] <= O.lo[j],
               "sweeps an untaken low and closes above it": _sweep_low(O, j),
               "untaken low within 1 ATR below (support)": O.cx["liq_behind"][j] <= 1.0, "RSI < 40": r[j] < 40}
        if lw >= 2 / 3 * rng and (c[j] - l[j]) >= 0.6 * rng:
            out.append(("Hammer / pin bar", 1, ctx))
        po, pc = O.o[j - 1], c[j - 1]
        if pc < po and c[j] > O.o[j] and c[j] >= po and O.o[j] <= pc and body > abs(pc - po):
            out.append(("Bullish engulfing", 1, ctx))
        r2 = h[j - 1] - l[j - 1]
        if (c[j - 2] < O.o[j - 2] and abs(c[j - 2] - O.o[j - 2]) >= 0.6 * (h[j - 2] - l[j - 2] + 1e-12) and r2 > 0 and
                abs(c[j - 1] - O.o[j - 1]) <= 0.3 * r2 and c[j] > O.o[j] and c[j] > (O.o[j - 2] + c[j - 2]) / 2):
            out.append(("Morning star", 1, ctx))
        if body <= 0.1 * rng and O.cx["liq_behind"][j] <= 1.0:
            out.append(("Doji at support (claim up)", 1, ctx))
        if h[j - 1] <= h[j - 2] and l[j - 1] >= l[j - 2] and c[j] > h[j - 2]:            # mother = candle j-2
            out.append(("Inside bar, close above the mother high", 1, {"with the trend (EMA 20 > 50)": O.e20[j] > O.e50[j],
                                                                        "volume >= 1.5x": O.v[j] >= 1.5 * O.v20[j]}))
        if c[j] > O.o[j] and body >= 0.8 * rng and rng >= 1.5 * a:
            out.append(("Strong full-body candle (displacement)", 1, {
                "breaks a 20-candle high": c[j] > O.hi20[j], "volume >= 2x": O.v[j] >= 2 * O.v20[j],
                "after a squeeze": O.rank[j - 5] <= 0.2 if np.isfinite(O.rank[j - 5]) else False,
                "RSI > 75 after it": r[j] > 75}))
        if j >= 3 and all(c[k] > O.o[k] and c[k] > c[k - 1] and (c[k] - l[k]) >= 0.7 * (h[k] - l[k] + 1e-12) for k in (j - 2, j - 1, j)):
            out.append(("Three white soldiers", 1, {"RSI > 70": r[j] > 70, "close outside the upper band": c[j] > O.up[j]}))
    # ---------------- market structure (closes beyond confirmed swings)
    hs2, ls2 = _last_swings(O.sh_arr, j, 2), _last_swings(O.sl_arr, j, 2)
    if len(hs2) == 2 and len(ls2) == 2:
        last_hi = hs2[1, 1]
        up_s = hs2[1, 1] > hs2[0, 1] and ls2[1, 1] > ls2[0, 1]
        dn_s = hs2[1, 1] < hs2[0, 1] and ls2[1, 1] < ls2[0, 1]
        if c[j] > last_hi and c[j - 1] <= last_hi:
            disp = rng >= 1.5 * a and abs(c[j] - O.o[j]) >= 0.6 * rng if rng > 0 else False
            spec = {"made by a displacement candle": bool(disp), "volume >= 1.5x": O.v[j] >= 1.5 * O.v20[j],
                    "closes > 0.5 ATR beyond the swing": (c[j] - last_hi) / a > 0.5}
            if up_s:
                out.append(("Break of structure (with the trend)", 1, spec))
            if dn_s:
                out.append(("Change of character (first break against)", 1, spec))
    # ---------------- Ichimoku (Hosoda; 9 / 26 / 52, the cloud shown at j was computed 26 candles earlier)
    if j >= 80 and np.isfinite(O.ctop[j]) and np.isfinite(O.kj[j]):
        tk, kj, top, bot = O.tk, O.kj, O.ctop, O.cbot
        chikou = c[j] > h[j - 26]                                       # the lagging line clears the candles 26 back
        fut = O.fa[j] > O.fb[j]                                         # the cloud being drawn 26 ahead is bullish
        thick = (top[j] - bot[j]) / a > 1
        ich = {"Chikou free (close above the high 26 candles ago)": bool(chikou), "future cloud bullish": bool(fut),
               "Tenkan above Kijun": tk[j] > kj[j], "thick cloud (> 1 ATR)": bool(thick),
               "Kijun flat (5 candles)": abs(kj[j] - kj[j - 5]) < 1e-9 * max(1.0, abs(kj[j])),
               "Kijun rising": kj[j] > kj[j - 5] + 1e-9 * max(1.0, abs(kj[j]))}
        if tk[j] > kj[j] and tk[j - 1] <= kj[j - 1]:
            out.append(("Ichimoku TK cross", 1, {**ich, "above the cloud (strong cross)": c[j] > top[j],
                                                 "inside the cloud (neutral cross)": bot[j] <= c[j] <= top[j],
                                                 "below the cloud (weak cross)": c[j] < bot[j]}))
        if c[j] > top[j] and c[j - 1] <= top[j - 1]:
            out.append(("Ichimoku cloud breakout (close above the cloud)", 1, {**ich, "volume >= 1.5x": O.v[j] >= 1.5 * O.v20[j]}))
        if c[j] > top[j] and l[j] <= kj[j] and c[j] > kj[j] and l[j - 1] > kj[j - 1]:
            out.append(("Ichimoku Kijun bounce (above the cloud)", 1, ich))
        if c[j - 1] < bot[j - 1] and bot[j] <= c[j] <= top[j]:
            out.append(("Ichimoku enters the cloud from below (edge to edge)", 1, ich))
        if (c[j] - kj[j]) / a > 3 and (c[j - 1] - kj[j - 1]) / O.a[j - 1] <= 3:
            out.append(("Ichimoku stretched > 3 ATR above Kijun", -1, ich))
        if O.fa[j] > O.fb[j] and O.fa[j - 1] <= O.fb[j - 1]:
            out.append(("Ichimoku kumo twist ahead (future cloud turns bullish)", 1, {**ich, "price above the cloud": c[j] > top[j]}))
    # ---------------- volume breakout
    if c[j] > O.hi20[j] and not c[j - 1] > O.hi20[j - 1]:
        vr = O.v[j] / O.v20[j]
        out.append(("Volume breakout", 1, {
            "volume >= 2x": vr >= 2, "volume 1 - 2x": 1 <= vr < 2, "volume < 1x": vr < 1,
            "body >= 60% of the range": abs(c[j] - O.o[j]) >= 0.6 * (h[j] - l[j]) if h[j] > l[j] else False,
            "after a squeeze": O.rank[j - 5] <= 0.2 if np.isfinite(O.rank[j - 5]) else False,
            "breaks by > 1 ATR": (c[j] - O.hi20[j]) / a > 1}))
    # ---------------- Fibonacci pullback
    lows = _last_swings(O.sl_arr, j, 1)
    if len(lows):
        i_lo, p_lo = int(lows[0, 0]), lows[0, 1]
        if j - i_lo <= 80 and j - i_lo > 3:
            seg_h = h[i_lo:j]
            i_hi = int(np.argmax(seg_h)) + i_lo
            p_hi = h[i_hi]
            if p_hi - p_lo >= 3 * a and i_hi < j - 1 and l[i_lo:j].min() >= p_lo:
                lev = {f: p_hi - f * (p_hi - p_lo) for f in (0.382, 0.5, 0.618, 0.786)}
                prior_min = l[i_hi + 1:j].min() if i_hi + 1 < j else np.inf
                for f in (0.786, 0.618, 0.5, 0.382):                       # the deepest level reached now, first time
                    L = lev[f]
                    if l[j] <= L + 0.25 * a and c[j] > L and prior_min > L + 0.25 * a and l[j] >= p_lo:
                        hs = O.sh_arr[(O.sh_arr[:, 2] <= j) & (O.sh_arr[:, 0] >= j - 150)]
                        ls = O.sl_arr[(O.sl_arr[:, 2] <= j) & (O.sl_arr[:, 0] >= j - 150)]
                        pts = np.r_[hs[:, 1], ls[:, 1][ls[:, 0] != i_lo]] if len(hs) or len(ls) else np.array([])
                        conf = bool(len(pts) and np.min(np.abs(pts - L)) <= 0.25 * a)
                        out.append(("Fib pullback", 1, {
                            "level 0.382": f == 0.382, "level 0.5": f == 0.5, "level 0.618": f == 0.618, "level 0.786": f == 0.786,
                            "confluence with an old swing (within 0.25 ATR)": conf,
                            "pullback volume below the leg's average": O.v[j] < np.mean(O.v[i_lo:i_hi + 1])}))
                        break
    # ---------------- trendline (rising, through the last two confirmed swing lows)
    ls = _last_swings(O.sl_arr, j, 6)
    if len(ls) >= 2:
        (i1, p1, _), (i2, p2, _) = ls[-2], ls[-1]
        if p2 > p1:
            slope = (p2 - p1) / (i2 - i1)
            v = p1 + slope * (j - i1)
            vp = p1 + slope * (j - 1 - i1)
            touches = sum(1 for i, p, _ in ls if abs(p - (p1 + slope * (i - i1))) <= 0.25 * O.a[int(i)])
            spec = {"3+ touches (a valid line)": touches >= 3, "steep (> 0.15 ATR per candle)": slope / a > 0.15}
            if l[j] <= v + 0.25 * a and c[j] > v and c[j - 1] > vp:
                out.append(("Trendline rejection", 1, spec))
            if c[j] < v - 0.25 * a and c[j - 1] >= vp - 0.25 * O.a[j - 1]:
                out.append(("Trendline break", -1, {**spec, "break candle volume >= 1.5x": O.v[j] >= 1.5 * O.v20[j]}))
    return out


SHIFTS = 400


def shift_pvalue(res: pd.DataFrame, cn: str) -> float:
    """Circular time-shift test: shift the condition against the outcomes (both keep their own clustering) and count
    how often a shifted copy shows a difference at least as large as the real one."""
    m = res[cn].notna().to_numpy()
    cnd = res[cn].to_numpy()[m].astype(bool)
    y = res["right"].to_numpy(float)[m]
    n = len(y)
    if n < 60:
        return 1.0
    obs = y[cnd].mean() - y[~cnd].mean()
    rng = np.random.default_rng(11)
    ks = rng.integers(n // 20, n - n // 20, SHIFTS)
    cnt = 0
    for k in ks:
        cs = np.roll(cnd, k)
        if cs.all() or not cs.any():
            continue
        cnt += abs(y[cs].mean() - y[~cs].mean()) >= abs(obs)
    return (cnt + 1) / (SHIFTS + 1)


def _sweep_low(O: Oriented, j) -> bool:
    """The candle's low went below an untaken confirmed swing low (last 150 candles) and the candle closed above it."""
    ls = O.sl_arr[(O.sl_arr[:, 2] <= j - 1) & (O.sl_arr[:, 0] >= j - 150)]
    for i, p, _ in ls:
        i = int(i)
        if O.l[j] < p < O.c[j] and (i + 1 >= j or O.l[i + 1:j].min() >= p):
            return True
    return False


def _failure_swing(r, j):
    """Wilder: RSI above 70 peaks, pulls back (trough), makes a lower peak still above the trough, then closes below
    the trough. Checked on the last 20 candles."""
    w = r[max(0, j - 20):j + 1]
    if len(w) < 8 or not np.all(np.isfinite(w)):
        return False
    k1 = int(np.argmax(w))
    if w[k1] <= 70 or k1 >= len(w) - 3:
        return False
    trough = np.min(w[k1:-1])
    kt = k1 + int(np.argmin(w[k1:-1]))
    if kt >= len(w) - 2:
        return False
    peak2 = np.max(w[kt:-1])
    return bool(peak2 < w[k1] and w[-1] < trough)


def run_indicator_deep(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    tfs = {k: TF(resample(df5u, k)) for k in ("1h", "4h", "1D", "1W")}
    d1 = tfs["1D"]
    d200 = ema(pd.Series(d1.c), 200).to_numpy(float)
    L = ["# Every indicator in detail: when its signal works and when it fails", "",
         "Same fair test for all: from the event close, 1.5 ATR in the claimed direction before 1.5 ATR against (30 "
         "candles). **A coin flip = 50%.** Up and mirrored down versions pooled. Research 2020 - Oct 2025; holdout "
         "Nov 2025 on.", ""]
    allrows = []
    n_tested = n_yes = 0
    for tf in ("1h", "4h", "1D"):
        t, ht = tfs[tf], tfs[HTF[tf]]
        cx = context_table(t, daily=(tf == "1D"))
        y = outcome(t)
        ot = pd.to_datetime(t.ot)
        hold = np.asarray(ot >= HOLDOUT)
        late = np.asarray((ot < HOLDOUT) & (ot >= HOLDOUT - 30 * pd.Timedelta(tf)))   # outcome would use holdout prices
        jd_all = np.searchsorted(d1.ct, t.ct, side="right") - 1
        jh_all = np.searchsorted(ht.ct, t.ct, side="right") - 1
        h50 = ema(pd.Series(ht.c), 50).to_numpy(float)
        rows = []
        for side in (1, -1):
            O = Oriented(t, side, cx)
            for j in range(210, t.n - 1):
                if not np.isfinite(y[j]) or late[j]:
                    continue
                jd, jh = jd_all[j], jh_all[j]
                trend = ((d1.c[jd] - d200[jd]) * side > 0) if jd >= 0 and np.isfinite(d200[jd]) else None
                htf = ((ht.c[jh] - h50[jh]) * side > 0) if jh >= 0 and np.isfinite(h50[jh]) else None
                for ev, claim, spec in detect(O, j):
                    right = y[j] if side * claim > 0 else 1 - y[j]
                    rows.append({"tf": tf, "event": ev, "time": pd.Timestamp(t.ot[j]), "hold": bool(hold[j]), "right": right,
                                 **{f"s: {k}": bool(v) for k, v in spec.items()}, **{f"c: {k}": (None if v is None else bool(v)) for k, v in common(O, j, trend, htf).items()}})
        E = pd.DataFrame(rows)
        allrows.append(E)
        L += [f"## {tf}", ""]
        for ev, g in E.groupby("event", sort=False):
            g = g.sort_values("time")
            res, hol = g[~g["hold"]], g[g["hold"]]
            conds = [c for c in g.columns if c.startswith(("s: ", "c: ")) and g[c].notna().any()]
            tab = []
            for cn in conds:
                a_, b_ = res[res[cn] == True], hol[hol[cn] == True]  # noqa: E712
                a0, b0 = res[res[cn] == False], hol[hol[cn] == False]  # noqa: E712
                if len(a_) < 20 or len(a0) < 20:
                    continue
                d_r = a_["right"].mean() - a0["right"].mean()
                d_h = (b_["right"].mean() - b0["right"].mean()) if len(b_) >= 10 and len(b0) >= 10 else np.nan
                pv = shift_pvalue(res, cn)
                tab.append({"cond": cn[3:] + ("" if cn.startswith("s: ") else " (context)"), "n": len(a_), "p": a_["right"].mean(),
                            "p0": a0["right"].mean(), "d": d_r, "pv": pv, "nh": len(b_), "ph": b_["right"].mean() if len(b_) else np.nan,
                            "dh": d_h, "same": "yes" if (pv < 0.01 and d_h == d_h and np.sign(d_h) == np.sign(d_r)) else ""})
                n_tested += 1
                n_yes += tab[-1]["same"] == "yes"
            T = pd.DataFrame(tab).sort_values("d") if tab else pd.DataFrame()
            claim = "down" if ev in ("RSI leaves 70", "Trendline break", "Stretched > 3 ATR above EMA 20",
                                     "Ichimoku stretched > 3 ATR above Kijun") else "up"
            L += [f"### {tf} · {ev} (claim: price goes {claim}) · {len(res):,} cases, right {res['right'].mean():.0%}; "
                  f"holdout {len(hol)} cases, right {hol['right'].mean():.0%}" if len(hol) else
                  f"### {tf} · {ev} · {len(res):,} cases, right {res['right'].mean():.0%}", ""]
            if len(T):
                f2 = lambda v: "" if v != v else f"{v * 100:+.0f} pts"  # noqa: E731
                L += [_table(T, [("cond", "when", str), ("n", "cases", lambda v: f"{v:,}"), ("p", "right when present", _pct),
                                 ("p0", "right when absent", _pct), ("d", "difference", f2),
                                 ("pv", "chance it is noise (2020-25)", lambda v: f"{v:.3f}"), ("nh", "holdout cases", str),
                                 ("ph", "holdout right when present", _pct), ("dh", "holdout difference", f2),
                                 ("same", "real (p < 0.01) and same sign in holdout", str)]), ""]
    L.insert(4, f"**Significance:** a condition is marked real only if its 2020 - Oct 2025 difference beats 99% of {SHIFTS} "
                f"time-shifted copies of the same condition (which keep the clustering of nearby events), and the holdout "
                f"difference has the same sign. {n_yes} of {n_tested} conditions pass; noise alone would pass about "
                f"{n_tested * 0.01 * 0.5:.0f}.")
    L.insert(5, "")
    pd.concat(allrows).to_pickle(ROOT / "results" / "indicator_deep.pkl")
    path = out_dir / "indicator_deep.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_indicator_deep(load_config(ROOT / "config.yaml"), ROOT / "reports"))
