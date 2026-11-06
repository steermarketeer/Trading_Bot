"""
Detectors for the definitions in docs/trading_definitions.md (one timeframe at a time).

Every function takes a bar table of ONE timeframe (columns open/high/low/close/volume, open_time, close_time) wrapped
in `TF`, and only uses candles closed at the index it is asked about. Indices are candle positions in that table.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .indicators import atr as _atr, bollinger
from .patterns import swing_points

K = 5                        # swing: highest / lowest of K candles on each side
EQ_PCT, EQ_ATR = 0.0025, 0.50
TOUCH_ATR = 0.25
BREAK_ATR = 0.25
FAKEOUT_BARS = 3


class TF:
    def __init__(self, bars: pd.DataFrame):
        b = bars.reset_index(drop=True)
        self.b = b
        self.o, self.h, self.l, self.c, self.v = (b[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume"))
        self.n = len(b)
        self.ot = pd.to_datetime(b["open_time"], utc=True).dt.tz_convert(None).to_numpy()
        self.ct = pd.to_datetime(b["close_time"], utc=True).dt.tz_convert(None).to_numpy()
        self.a = _atr(b, 14).to_numpy(float)
        self.sh, self.sl = swing_points(self.h, self.l, K)            # (index, price, confirm index)
        mid, up, lo = bollinger(b["close"])
        self.mid, self.up, self.lo = mid.to_numpy(float), up.to_numpy(float), lo.to_numpy(float)

    def closed_before(self, t) -> int:
        """Number of candles closed at time t (so the last usable index is this - 1)."""
        return int(np.searchsorted(self.ct, np.datetime64(pd.Timestamp(t)), side="right"))

    def tol(self, j: int, price: float) -> float:
        return max(EQ_PCT * price, EQ_ATR * self.a[j])


# --------------------------------------------------------------------------------------------- equal highs / lows
@dataclass
class EqualLevel:
    side: str            # "H" (equal highs = double/triple top) or "L" (equal lows = double/triple bottom)
    price: float         # average of the matching swings
    idx: list            # swing candle indices
    known: int           # candle index at which the last swing was confirmed
    valley: float        # extreme between the swings (neckline)
    confirmed_at: int    # first close beyond the valley after `known` (-1 = not yet, within `upto`)
    taken_at: int        # first candle trading beyond the level after `known` (-1 = untaken)


def equal_levels(t: TF, side: str, upto: int, lookback: int = 150) -> list[EqualLevel]:
    """Double / triple tops (side H) or bottoms (side L) whose last swing is confirmed before candle `upto`."""
    pts = [(i, p, cf) for i, p, cf in (t.sh if side == "H" else t.sl) if cf < upto and i >= upto - lookback]
    out = []
    for a in range(len(pts)):
        group = [pts[a]]
        for b_ in range(a + 1, len(pts)):
            i, p, cf = pts[b_]
            ref = np.mean([g[1] for g in group])
            if abs(p - ref) <= t.tol(i, ref) and i - group[-1][0] >= K:
                seg = slice(group[-1][0] + 1, i)                       # strictly between the two swings
                valley = t.l[seg].min() if side == "H" else t.h[seg].max()
                if abs(ref - valley) >= t.a[i]:
                    group.append(pts[b_])
        if len(group) >= 2:
            idx = [g[0] for g in group]
            price = float(np.mean([g[1] for g in group]))
            valley = t.l[idx[0] + 1:idx[-1]].min() if side == "H" else t.h[idx[0] + 1:idx[-1]].max()   # neckline
            known = max(g[2] for g in group)
            conf = taken = -1
            for j in range(known, upto):
                if conf < 0 and ((t.c[j] < valley) if side == "H" else (t.c[j] > valley)):
                    conf = j
                if taken < 0 and ((t.h[j] > max(g[1] for g in group)) if side == "H" else (t.l[j] < min(g[1] for g in group))):
                    taken = j
            out.append(EqualLevel(side, price, idx, known, float(valley), conf, taken))
    # keep the largest group per price (drop subsets)
    out.sort(key=lambda e: -len(e.idx))
    kept = []
    for e in out:
        if not any(set(e.idx) <= set(k.idx) for k in kept):
            kept.append(e)
    return kept


# --------------------------------------------------------------------------------------------- reactions at a level
def is_rejection(t: TF, j: int, level: float, side: str) -> bool:
    """side "R" = resistance (rejection from above), "S" = support. Touch / pierce + close back by >= 0.25 ATR."""
    a = t.a[j]
    if side == "R":
        return t.h[j] >= level - TOUCH_ATR * a and t.c[j] <= level - TOUCH_ATR * a
    return t.l[j] <= level + TOUCH_ATR * a and t.c[j] >= level + TOUCH_ATR * a


def rejection_strength(t: TF, j: int, side: str) -> float:
    """Share of the candle's range in the wick toward the level (>= 2/3 = pin bar)."""
    rng = t.h[j] - t.l[j]
    if rng <= 0:
        return 0.0
    return ((t.h[j] - max(t.o[j], t.c[j])) if side == "R" else (min(t.o[j], t.c[j]) - t.l[j])) / rng


def rejections(t: TF, level: float, side: str, i0: int, i1: int) -> list[int]:
    return [j for j in range(max(0, i0), i1) if np.isfinite(t.a[j]) and is_rejection(t, j, level, side)]


def failed_pushes(t: TF, level: float, side: str, i0: int, i1: int) -> list[int]:
    """After a rejection at `level`: candles that push toward it (close > open at resistance) but stay short of it
    by more than 0.25 ATR. Returned with their extreme so 'each lower than the last' can be checked."""
    out = []
    for j in range(max(0, i0), i1):
        a = t.a[j]
        if side == "R" and t.c[j] > t.o[j] and t.h[j] < level - TOUCH_ATR * a:
            out.append(j)
        if side == "S" and t.c[j] < t.o[j] and t.l[j] > level + TOUCH_ATR * a:
            out.append(j)
    return out


# --------------------------------------------------------------------------------------------- breakouts
def breakout_close(t: TF, j: int, level: float, d: int) -> bool:
    return (t.c[j] - level) * d >= BREAK_ATR * t.a[j]


def fakeout(t: TF, j: int, level: float, d: int) -> bool:
    """A breakout at j that closes back inside the level within FAKEOUT_BARS candles (needs those candles closed)."""
    return any((t.c[k] - level) * d < 0 for k in range(j + 1, min(t.n, j + 1 + FAKEOUT_BARS)))


def sweep(t: TF, j: int, level: float, side: str) -> bool:
    """Wick beyond a pool, same candle closes back inside. side "H" = buy-side pool above, "L" = sell-side below."""
    return (t.h[j] > level and t.c[j] < level) if side == "H" else (t.l[j] < level and t.c[j] > level)


def displacement(t: TF, j: int) -> bool:
    rng = t.h[j] - t.l[j]
    return rng >= 1.5 * t.a[j] and abs(t.c[j] - t.o[j]) >= 0.6 * rng


# --------------------------------------------------------------------------------------------- Bollinger
def band_failure(t: TF, j: int, side: str) -> bool:
    """Close beyond the upper (side "U") / lower ("L") band at some candle in j-3..j-1, and a close back inside at j."""
    if side == "U":
        return t.c[j] < t.up[j] and any(t.c[k] > t.up[k] for k in range(max(0, j - FAKEOUT_BARS), j))
    return t.c[j] > t.lo[j] and any(t.c[k] < t.lo[k] for k in range(max(0, j - FAKEOUT_BARS), j))
