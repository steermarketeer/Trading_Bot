"""
Chart patterns from swing points, detected without hindsight.

Swing high at bar i: high[i] is the highest of bars i-K .. i+K. It is only KNOWN at bar i+K
(the K bars after it must exist), so a pattern can only use swings confirmed by day t.
A pattern event fires on the BREAKOUT day: the first close through the neckline / trend line.

Patterns: double top / bottom, head & shoulders (and inverse),
ascending / descending / symmetrical triangle (direction = breakout side).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

PATTERN_INFO = {
    "double_top": "Two similar highs with a dip between; close breaks below the dip (bearish)",
    "double_bottom": "Two similar lows with a bounce between; close breaks above the bounce (bullish)",
    "head_shoulders": "Three highs, middle highest; close breaks below the neckline (bearish)",
    "inv_head_shoulders": "Three lows, middle lowest; close breaks above the neckline (bullish)",
    "triangle_ascending": "Flat highs + rising lows; direction = breakout side",
    "triangle_descending": "Falling highs + flat lows; direction = breakout side",
    "triangle_symmetrical": "Falling highs + rising lows; direction = breakout side",
}


@dataclass(frozen=True)
class PatternParams:
    swing_k: int = 5             # bars each side for a swing point
    max_breakout_wait: int = 40  # breakout must come within N bars of the last swing
    double_tol: float = 0.03     # two tops/bottoms within 3%
    double_min_depth: float = 0.05
    double_min_gap: int = 10
    double_max_gap: int = 120
    hs_head_margin: float = 0.03  # head at least 3% beyond both shoulders
    hs_shoulder_tol: float = 0.08
    hs_max_span: int = 150
    tri_flat: float = 0.02       # a "flat" side moves less than 2% between its two swings
    tri_slope: float = 0.03      # a sloping side moves at least 3%
    tri_max_span: int = 90


def swing_points(high: np.ndarray, low: np.ndarray, k: int):
    """Return lists of (index, price, confirmed_at) for swing highs and lows."""
    n = len(high)
    highs, lows = [], []
    for i in range(k, n - k):
        hw = high[i - k:i + k + 1]
        lw = low[i - k:i + k + 1]
        # strict on the right so a flat top is counted once (at its last bar)
        if high[i] == hw.max() and (high[i + 1:i + k + 1] < high[i]).all():
            highs.append((i, float(high[i]), i + k))
        if low[i] == lw.min() and (low[i + 1:i + k + 1] > low[i]).all():
            lows.append((i, float(low[i]), i + k))
    return highs, lows


def _line(i1, p1, i2, p2, t):
    return p1 + (p2 - p1) * (t - i1) / (i2 - i1)


def detect_patterns(d: pd.DataFrame, p: PatternParams = PatternParams()) -> pd.DataFrame:
    high = d["high"].to_numpy(float)
    low = d["low"].to_numpy(float)
    close = d["close"].to_numpy(float)
    days = d["day"].to_numpy()
    n = len(d)
    sh, sl = swing_points(high, low, p.swing_k)
    # A swing point can belong to at most one pattern: once a pattern fires, its swings are
    # used up. This stops one breakout being counted as two patterns (e.g. a head & shoulders
    # whose head/shoulder also look like a triangle's highs) and stops the same structure
    # re-firing when a new swing appears next to it.
    used_hi: set = set()
    used_lo: set = set()
    events = []

    def free(his=(), los=()):
        return not (set(his) & used_hi) and not (set(los) & used_lo)

    def fire(t, name, direction, his, los, info):
        used_hi.update(his)
        used_lo.update(los)
        events.append({"day": days[t], "signal": name, "direction": direction, "kind": "pattern", **info})

    hi_ptr = lo_ptr = 0
    known_hi: list = []
    known_lo: list = []
    for t in range(1, n):
        while hi_ptr < len(sh) and sh[hi_ptr][2] <= t:
            known_hi.append(sh[hi_ptr])
            hi_ptr += 1
        while lo_ptr < len(sl) and sl[lo_ptr][2] <= t:
            known_lo.append(sl[lo_ptr])
            lo_ptr += 1
        c0, c1 = close[t], close[t - 1]

        # ---- double top / bottom
        if len(known_hi) >= 2:
            (i1, p1, _), (i2, p2, _) = known_hi[-2], known_hi[-1]
            if (p.double_min_gap <= i2 - i1 <= p.double_max_gap and t - i2 <= p.max_breakout_wait
                    and free(his=(i1, i2))):
                if abs(p1 - p2) / max(p1, p2) <= p.double_tol:
                    neck = low[i1:i2 + 1].min()
                    deep = neck <= min(p1, p2) * (1 - p.double_min_depth)
                    intact = high[i2 + 1:t + 1].max(initial=-np.inf) <= max(p1, p2) * (1 + p.double_tol)
                    first = (close[i2 + 1:t] >= neck).all()
                    if deep and intact and first and c0 < neck <= c1:
                        fire(t, "double_top", -1, (i1, i2), (), {"level": neck})
        if len(known_lo) >= 2:
            (i1, p1, _), (i2, p2, _) = known_lo[-2], known_lo[-1]
            if (p.double_min_gap <= i2 - i1 <= p.double_max_gap and t - i2 <= p.max_breakout_wait
                    and free(los=(i1, i2))):
                if abs(p1 - p2) / max(p1, p2) <= p.double_tol:
                    neck = high[i1:i2 + 1].max()
                    deep = neck >= max(p1, p2) * (1 + p.double_min_depth)
                    intact = low[i2 + 1:t + 1].min(initial=np.inf) >= min(p1, p2) * (1 - p.double_tol)
                    first = (close[i2 + 1:t] <= neck).all()
                    if deep and intact and first and c0 > neck >= c1:
                        fire(t, "double_bottom", 1, (), (i1, i2), {"level": neck})

        # ---- head & shoulders (tops) / inverse (bottoms)
        if len(known_hi) >= 3:
            (ia, pa, _), (ib, pb, _), (ic, pc, _) = known_hi[-3:]
            if ic - ia <= p.hs_max_span and t - ic <= p.max_breakout_wait and free(his=(ia, ib, ic)):
                head = pb >= max(pa, pc) * (1 + p.hs_head_margin)
                level = abs(pa - pc) / max(pa, pc) <= p.hs_shoulder_tol
                if head and level:
                    j1 = ia + int(np.argmin(low[ia:ib + 1]))
                    j2 = ib + int(np.argmin(low[ib:ic + 1]))
                    if j2 > j1:
                        neck_t, neck_p = _line(j1, low[j1], j2, low[j2], t), _line(j1, low[j1], j2, low[j2], t - 1)
                        intact = high[ic + 1:t + 1].max(initial=-np.inf) < pb
                        first = all(close[s] >= _line(j1, low[j1], j2, low[j2], s) for s in range(ic + 1, t))
                        if intact and first and c0 < neck_t and c1 >= neck_p:
                            fire(t, "head_shoulders", -1, (ia, ib, ic), (j1, j2), {"level": neck_t})
        if len(known_lo) >= 3:
            (ia, pa, _), (ib, pb, _), (ic, pc, _) = known_lo[-3:]
            if ic - ia <= p.hs_max_span and t - ic <= p.max_breakout_wait and free(los=(ia, ib, ic)):
                head = pb <= min(pa, pc) * (1 - p.hs_head_margin)
                level = abs(pa - pc) / max(pa, pc) <= p.hs_shoulder_tol
                if head and level:
                    j1 = ia + int(np.argmax(high[ia:ib + 1]))
                    j2 = ib + int(np.argmax(high[ib:ic + 1]))
                    if j2 > j1:
                        neck_t, neck_p = _line(j1, high[j1], j2, high[j2], t), _line(j1, high[j1], j2, high[j2], t - 1)
                        intact = low[ic + 1:t + 1].min(initial=np.inf) > pb
                        first = all(close[s] <= _line(j1, high[j1], j2, high[j2], s) for s in range(ic + 1, t))
                        if intact and first and c0 > neck_t and c1 <= neck_p:
                            fire(t, "inv_head_shoulders", 1, (j1, j2), (ia, ib, ic), {"level": neck_t})

        # ---- triangles
        if len(known_hi) >= 2 and len(known_lo) >= 2:
            (h1, ph1, _), (h2, ph2, _) = known_hi[-2:]
            (l1, pl1, _), (l2, pl2, _) = known_lo[-2:]
            first_i, last_i = min(h1, l1), max(h2, l2)
            if (last_i - first_i <= p.tri_max_span and t - last_i <= p.max_breakout_wait
                    and free(his=(h1, h2), los=(l1, l2))):
                hd, ld = (ph2 - ph1) / ph1, (pl2 - pl1) / pl1
                kind = None
                if abs(hd) <= p.tri_flat and ld >= p.tri_slope:
                    kind = "triangle_ascending"
                elif abs(ld) <= p.tri_flat and hd <= -p.tri_slope:
                    kind = "triangle_descending"
                elif hd <= -p.tri_slope and ld >= p.tri_slope:
                    kind = "triangle_symmetrical"
                if kind:
                    def up(s):
                        return _line(h1, ph1, h2, ph2, s)

                    def lo(s):
                        return _line(l1, pl1, l2, pl2, s)
                    if up(t) > lo(t):  # lines have not crossed (before the apex)
                        inside = all(lo(s) <= close[s] <= up(s) for s in range(last_i + 1, t))
                        if inside and c0 > up(t) and c1 <= up(t - 1):
                            fire(t, kind, 1, (h1, h2), (l1, l2), {"level": up(t)})
                        elif inside and c0 < lo(t) and c1 >= lo(t - 1):
                            fire(t, kind, -1, (h1, h2), (l1, l2), {"level": lo(t)})

    cols = ["day", "signal", "direction", "kind", "level"]
    return pd.DataFrame(events, columns=cols) if events else pd.DataFrame(columns=cols)
