"""
Price-action concepts as tradeable events, detected without hindsight (swings are only used once
confirmed, i.e. K candles after they formed).

Concepts and their events (d = trade direction):
  STRUCTURE   state from the last 2 confirmed swing highs and lows: up (HH+HL) / down (LH+LL) / range
              bos      close through the last swing high in an uptrend (or low in a downtrend) -> continuation
              choch    close through the last swing high in a DOWNtrend (or low in an uptrend) -> first sign of reversal
  TRENDLINES  rising support line through two confirmed swing lows / falling resistance through two swing highs,
              no close beyond it since the first anchor; best = most swing touches (within 0.3 ATR), then most recent
              tl_bounce  candle touches the line, closes on its side, the NEXT candle confirms (bounce) -> reversal
              tl_break   first close beyond the line -> trade the break
  LIQUIDITY   pools of equal highs / equal lows: >= 2 confirmed swings within 0.25 ATR, untouched since
              liq_sweep  wick beyond the pool, close back inside -> reversal (stop beyond the wick)
              liq_run    close beyond the pool -> continuation
  ZONES       strong support/resistance zones (levels.py), bounce-confirmed reversal and breakout
              zone_bounce / zone_break

Every event: decision at a candle close, entry next open, stop as described per event, targets 1R/1.5R/2R
(sr2.label_multi). Confluence flags describe what else lined up at the decision time.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .indicators import adx, atr, bollinger, ema, macd, rsi
from .levels import _level_table, strong_levels
from .patterns import swing_points
from .sr2 import label_multi

K = 5
TL_TOUCH_ATR = 0.3
TL_BAND_ATR = 0.25
TL_MAX_SWINGS = 6
TL_LOOKBACK = 200
LIQ_EQ_ATR = 0.25
LIQ_LOOKBACK = 100
PAD = 0.25
BREAK_PAD = 0.5


class Bars:
    """Arrays + indicators for one timeframe (all backward-looking)."""

    def __init__(self, b: pd.DataFrame):
        self.b = b.reset_index(drop=True)
        b = self.b
        self.o, self.h, self.l, self.c, self.v = (b[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume"))
        self.n = len(b)
        self.ot = pd.to_datetime(b["open_time"], utc=True)
        self.ct = pd.to_datetime(b["close_time"], utc=True)
        self.a = atr(b, 14).to_numpy(float)
        self.r = rsi(b["close"]).to_numpy(float)
        line, sig = macd(b["close"])
        self.hist = (line - sig).to_numpy(float)
        self.e20, self.e50, self.e200 = (ema(b["close"], n).to_numpy(float) for n in (20, 50, 200))
        ad, pdi, mdi = adx(b)
        self.adx, self.pdi, self.mdi = ad.to_numpy(float), pdi.to_numpy(float), mdi.to_numpy(float)
        _, bu, bl = bollinger(b["close"])
        self.bu, self.bl = bu.to_numpy(float), bl.to_numpy(float)
        self.vavg = pd.Series(self.v).shift(1).rolling(20, min_periods=20).mean().to_numpy(float)
        self.v5 = pd.Series(self.v).rolling(5, min_periods=5).mean().to_numpy(float)
        self.sh, self.sl = swing_points(self.h, self.l, K)

    def known_swings(self, t: int):
        """Swings confirmed by the close of candle t: lists of (index, price)."""
        return ([(i, p) for i, p, cf in self.sh if cf <= t], [(i, p) for i, p, cf in self.sl if cf <= t])

    def features(self, j: int, d: int) -> dict:
        """Direction-relative context at the close of candle j (d = trade direction)."""
        a = self.a[j]
        c = self.c
        win = slice(max(0, j - 20), j)
        new_ext = (self.l[j] <= self.l[win].min()) if d > 0 else (self.h[j] >= self.h[win].max())
        pi = (j - 20 + int(np.argmin(self.l[win]))) if d > 0 else (j - 20 + int(np.argmax(self.h[win])))
        rng = self.h[j] - self.l[j]
        return {
            "f_vol": self.v[j] / self.vavg[j] if self.vavg[j] > 0 else np.nan,
            "f_vol_prev": self.v[j - 1] / self.vavg[j] if self.vavg[j] > 0 else np.nan,
            "f_vol_approach": self.v5[j - 1] / self.v5[j - 6] if self.v5[j - 6] > 0 else np.nan,
            "f_vol_slope": np.polyfit(np.arange(10), self.v[j - 9:j + 1], 1)[0] / self.vavg[j] if self.vavg[j] > 0 else np.nan,
            "f_vol_div": float(new_ext and self.v[j] < self.v[pi]),
            "f_rsi": self.r[j] if d > 0 else 100 - self.r[j],  # high = momentum with the trade
            "f_rsi_div": float(new_ext and ((self.r[j] > self.r[pi]) if d > 0 else (self.r[j] < self.r[pi]))),
            "f_adx": self.adx[j], "f_di": (self.pdi[j] - self.mdi[j]) * d,
            "f_bb_pos": ((c[j] - self.bl[j]) / (self.bu[j] - self.bl[j]) if d > 0 else (self.bu[j] - c[j]) / (self.bu[j] - self.bl[j]))
            if self.bu[j] > self.bl[j] else np.nan,
            "f_d_e20": (c[j] - self.e20[j]) / a * d, "f_d_e50": (c[j] - self.e50[j]) / a * d,
            "f_d_e200": (c[j] - self.e200[j]) / a * d, "f_macd": self.hist[j] / a * d,
            "f_macd_turn": float(d * (self.hist[j] - self.hist[j - 1]) > 0),
            "f_body": d * (c[j] - self.o[j]) / a, "f_range": rng / a,
            "f_close_pos": ((c[j] - self.l[j]) / rng if d > 0 else (self.h[j] - c[j]) / rng) if rng > 0 else np.nan,
            "f_ret_5": (c[j] / c[j - 5] - 1) * d, "f_ret_20": (c[j] / c[j - 20] - 1) * d,
            "f_atr_pct": a / c[j],
        }


def structure_state(highs, lows) -> int:
    if len(highs) < 2 or len(lows) < 2:
        return 0
    (_, h1), (_, h2) = highs[-2:]
    (_, l1), (_, l2) = lows[-2:]
    if h2 > h1 and l2 > l1:
        return 1
    if h2 < h1 and l2 < l1:
        return -1
    return 0


def best_trendline(points, kind: str, t: int, bars: Bars):
    """
    points: confirmed swings (index, price). kind 'support' = rising line through lows,
    'resistance' = falling line through highs. Valid if no close beyond it (by > 0.1 ATR) from the
    first anchor through candle t. Returns (i1, p1, i2, p2, touches) or None.
    """
    pts = [(i, p) for i, p in points if t - i <= TL_LOOKBACK][-TL_MAX_SWINGS:]
    best = None
    a_t = bars.a[t]
    for x in range(len(pts)):
        for y in range(x + 1, len(pts)):
            (i1, p1), (i2, p2) = pts[x], pts[y]
            slope = (p2 - p1) / (i2 - i1)
            if (kind == "support" and slope <= 0) or (kind == "resistance" and slope >= 0):
                continue
            idx = np.arange(i1, t + 1)
            line = p1 + slope * (idx - i1)
            closes = bars.c[i1:t + 1]
            tol = 0.1 * bars.a[i1:t + 1]
            if kind == "support" and (closes < line - tol).any():
                continue
            if kind == "resistance" and (closes > line + tol).any():
                continue
            touches = sum(1 for i, p in pts if i >= i1 and abs(p - (p1 + slope * (i - i1))) <= TL_TOUCH_ATR * a_t)
            cand = (touches, i2, (i1, p1, i2, p2, touches))
            if best is None or cand[:2] > best[:2]:
                best = cand
    return best[2] if best else None


def _line_at(line, i):
    i1, p1, i2, p2, _ = line
    return p1 + (p2 - p1) / (i2 - i1) * (i - i1)


def detect_events(df5: pd.DataFrame, rule: str, resample_fn) -> pd.DataFrame:
    bars = Bars(resample_fn(df5, rule))
    o, h, l, c, a = bars.o, bars.h, bars.l, bars.c, bars.a
    table = _level_table(df5)
    rows = []
    broken_swings: set = set()
    used_pools: set = set()
    tl_cache = {"support": (None, None), "resistance": (None, None)}  # kind -> (swing count key, line)
    zone_key, zones = None, np.array([])
    last_zone_ev: dict = {}

    def add(kind, j_dec, d, stop, extra):
        if j_dec + 1 >= bars.n:
            return
        lab = label_multi(o, h, l, c, j_dec + 1, d, stop)
        if lab is None:
            return
        rows.append({"event": kind, "j": j_dec, "decision_time": bars.ct.iloc[j_dec],
                     "day": bars.ct.iloc[j_dec].strftime("%Y-%m-%d"), "direction": d, "atr": a[j_dec],
                     **extra, **bars.features(j_dec, d), **lab})

    for j in range(210, bars.n - 2):
        if not np.isfinite(a[j]) or a[j] <= 0 or not np.isfinite(bars.vavg[j]):
            continue
        highs, lows = bars.known_swings(j - 1)   # swings known before candle j (confirmed by j-1's close)
        st = structure_state(highs, lows)
        ctx = {"structure": st}

        # ---------------- STRUCTURE: BOS / CHoCH on the close of j
        if highs:
            hi_i, hi_p = highs[-1]
            if c[j] > hi_p and c[j - 1] <= hi_p and ("H", hi_i) not in broken_swings:
                broken_swings.add(("H", hi_i))
                ev = "bos" if st == 1 else ("choch" if st == -1 else "range_break")
                add(ev, j, 1, hi_p - BREAK_PAD * a[j], {**ctx, "ref_level": hi_p})
        if lows:
            lo_i, lo_p = lows[-1]
            if c[j] < lo_p and c[j - 1] >= lo_p and ("L", lo_i) not in broken_swings:
                broken_swings.add(("L", lo_i))
                ev = "bos" if st == -1 else ("choch" if st == 1 else "range_break")
                add(ev, j, -1, lo_p + BREAK_PAD * a[j], {**ctx, "ref_level": lo_p})

        # ---------------- TRENDLINES
        for kind, pts, d in (("support", lows, 1), ("resistance", highs, -1)):
            key, line = tl_cache[kind]
            if key != len(pts) or line is None:
                line = best_trendline(pts, kind, j - 1, bars) if len(pts) >= 2 else None
                tl_cache[kind] = (len(pts), line)
            if line is None:
                continue
            lv, lv_prev = _line_at(line, j), _line_at(line, j - 1)
            touches = line[4]
            if (kind == "support" and c[j] < lv - 0.1 * a[j]) or (kind == "resistance" and c[j] > lv + 0.1 * a[j]):
                add("tl_break", j, -d, lv + d * BREAK_PAD * a[j],
                    {**ctx, "ref_level": lv, "tl_touches": touches, "tl_age": j - line[0]})
                tl_cache[kind] = (len(pts), None)  # line is broken; wait for a new one
                continue
            touched = (l[j] <= lv + TL_BAND_ATR * a[j]) if d > 0 else (h[j] >= lv - TL_BAND_ATR * a[j])
            was_away = (c[j - 1] > lv_prev + TL_BAND_ATR * a[j]) if d > 0 else (c[j - 1] < lv_prev - TL_BAND_ATR * a[j])
            held = (c[j] > lv) if d > 0 else (c[j] < lv)
            k = j + 1
            if touched and was_away and held and k + 1 < bars.n:
                lv_k = _line_at(line, k)
                bounce = d * (c[k] - o[k]) > 0 and d * (c[k] - c[j]) > 0 and ((c[k] > lv_k) if d > 0 else (c[k] < lv_k))
                if bounce:
                    stop = (min(l[j], l[k], lv) - PAD * a[j]) if d > 0 else (max(h[j], h[k], lv) + PAD * a[j])
                    add("tl_bounce", k, d, stop, {**ctx, "ref_level": lv, "tl_touches": touches,
                                                  "tl_age": j - line[0], "f_bvol": bars.v[k] / bars.vavg[j]})

        # ---------------- LIQUIDITY: equal highs / lows
        for side, pts, d_sweep in (("H", highs, -1), ("L", lows, 1)):
            recent = [(i, p) for i, p in pts if j - i <= LIQ_LOOKBACK]
            pool = None
            for x in range(len(recent) - 1, 0, -1):     # newest pair of equal swings
                for y in range(x - 1, -1, -1):
                    (i1, p1), (i2, p2) = recent[y], recent[x]
                    if abs(p1 - p2) <= LIQ_EQ_ATR * a[j]:
                        lvl = max(p1, p2) if side == "H" else min(p1, p2)
                        seg = slice(i2 + 1, j)
                        untouched = (h[seg] <= lvl).all() if side == "H" else (l[seg] >= lvl).all()
                        if untouched and (side, i1, i2) not in used_pools:
                            pool = (i1, i2, lvl)
                        break
                if pool:
                    break
            if not pool:
                continue
            i1, i2, lvl = pool
            if side == "H" and h[j] > lvl:
                used_pools.add((side, i1, i2))
                if c[j] < lvl:
                    add("liq_sweep", j, -1, h[j] + PAD * a[j], {**ctx, "ref_level": lvl})
                else:
                    add("liq_run", j, 1, lvl - BREAK_PAD * a[j], {**ctx, "ref_level": lvl})
            if side == "L" and l[j] < lvl:
                used_pools.add((side, i1, i2))
                if c[j] > lvl:
                    add("liq_sweep", j, 1, l[j] - PAD * a[j], {**ctx, "ref_level": lvl})
                else:
                    add("liq_run", j, -1, lvl + BREAK_PAD * a[j], {**ctx, "ref_level": lvl})

        # ---------------- ZONES (strong S/R), bounce-confirmed and breakout
        t_open = bars.ot.iloc[j]
        zk = (int((table["known"] <= t_open).sum()), t_open.normalize())
        if zk != zone_key:
            zones = strong_levels(table, t_open)
            zone_key = zk
        if len(zones):
            band = TL_BAND_ATR * a[j]
            for kind, cand, d in (("support", zones[(zones < c[j - 1]) & (l[j] <= zones + band)], 1),
                                  ("resistance", zones[(zones > c[j - 1]) & (h[j] >= zones - band)], -1)):
                if len(cand) == 0:
                    continue
                L = cand.max() if d > 0 else cand.min()
                zkey = (kind, round(L, 2))
                if j - last_zone_ev.get(zkey, -10**9) < 6:
                    continue
                last_zone_ev[zkey] = j
                held = (c[j] > L) if d > 0 else (c[j] < L)
                if held:
                    k = j + 1
                    if k + 1 < bars.n and d * (c[k] - o[k]) > 0 and d * (c[k] - c[j]) > 0 and ((c[k] > L) if d > 0 else (c[k] < L)):
                        stop = (min(l[j], l[k], L) - PAD * a[j]) if d > 0 else (max(h[j], h[k], L) + PAD * a[j])
                        add("zone_bounce", k, d, stop, {**ctx, "ref_level": L, "f_bvol": bars.v[k] / bars.vavg[j]})
                else:
                    add("zone_break", j, -d, L + d * BREAK_PAD * a[j], {**ctx, "ref_level": L})

    ev = pd.DataFrame(rows)
    if ev.empty:
        return ev
    ev["structure_with"] = np.sign(ev["structure"]) * ev["direction"]  # +1 with, -1 against, 0 range/unknown
    return ev


def add_confluence(ev: pd.DataFrame) -> pd.DataFrame:
    """For each event: did other concepts fire in the same direction within the last 3 candles (or same candle)?"""
    ev = ev.sort_values(["j", "event"]).reset_index(drop=True)
    for other in ("zone_bounce", "tl_bounce", "liq_sweep", "bos", "choch", "tl_break", "zone_break", "liq_run"):
        o_ev = ev[ev["event"] == other][["j", "direction"]].to_numpy()
        flags = np.zeros(len(ev), dtype=int)
        for n, (j, d, e) in enumerate(ev[["j", "direction", "event"]].to_numpy()):
            if e == other:
                continue
            m = (o_ev[:, 0] <= j) & (o_ev[:, 0] >= j - 3) & (o_ev[:, 1] == d)
            flags[n] = int(m.any())
        ev[f"c_{other}"] = flags
    ccols = [c for c in ev.columns if c.startswith("c_")]
    ev["c_count"] = ev[ccols].sum(axis=1)
    return ev
