"""
Top-failure detector: a failure at a higher-timeframe pool, then a close below the failure structure's low.
(The shape of the missed shorts: 16 Dec 2024, 7 Jun 2024, 27 Mar 2023.) Mirrored for bottoms -> longs.
Everything from closed candles; pools known at the candle before the trigger.

pool P      an untaken swing high of the pool timeframes (confirmed before the trigger candle, not traded above since)
            that the structure reached (its high within REACH ATR of P; a wick may exceed P by up to 1 ATR)
structure   the last WIN candles before the trigger: price reached P (high >= P - REACH * ATR), never CLOSED above P
            since the first reach, and either
              (a) sweep:  a candle with high > P and close < P                 (wick through, close back)
              (b) pushes: >= 2 local-high candles reaching P - PUSH * ATR with the last high below the first
              (c) cap:    three failures at a cap (bot/study/three_failures.setups, the audited detector) with an
                          untaken pool of the higher timeframe within CAP_ATR above the cap (the 27 Mar 2023 shape)
neckline    the lowest low from the first push (sweep: from the first reach) to the candle before the trigger; one
            trigger per structure ((c): the last push's low)
trigger j   the first close below the neckline (the close before was not)
stop        the structure's highest high * (1 + 0.001)
target      the first untaken swing low of the target timeframes >= 1.2R below the entry, else 2R
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .defs import TF
from .fibliq import Swings

WIN, REACH, PUSH, CAP_ATR = 20, 0.5, 1.0, 3.0


@dataclass(frozen=True)
class TopFail:
    j: int                 # trigger candle index (its close is the signal)
    side: int              # +1 = top failure (short), -1 = bottom failure (long)
    pool: float            # real price of the pool
    kind: str              # "sweep" / "pushes"
    neckline: float        # real price
    stop: float            # real price
    first: int             # first reach candle index
    n_push: int


def _pools(sw: dict, t_known, side: int, lookback: dict) -> np.ndarray:
    out = []
    for tf, s in sw.items():
        out.extend(s.untaken(t_known, "H" if side > 0 else "L", lookback=lookback.get(tf, 400)))
    return np.array(sorted(set(np.round(out, 2))))


def detect(t: TF, sw_pool: dict, side: int, lookback: dict | None = None) -> list[TopFail]:
    """t = the signal timeframe (4h or 1h); sw_pool = {tf: Swings} of the pool timeframes (e.g. 1D, 1W; or 4h for 1h).
    side +1: top failures. Returns one TopFail per trigger."""
    lookback = lookback or {}
    h, l, c = (t.h, t.l, t.c) if side > 0 else (-t.l, -t.h, -t.c)
    a = t.a
    out, done = [], set()                                                  # one trigger per (pool, first reach)
    for j in range(WIN + 1, t.n):
        if not np.isfinite(a[j]):
            continue
        pools = _pools(sw_pool, pd.Timestamp(t.ct[j - 1]), side, lookback)   # known before the trigger candle
        pools = pools if side > 0 else -pools[::-1]                            # oriented
        w0 = j - WIN
        hmax = h[w0:j].max()                                                   # the structure's high
        # the pool must have been reached by the structure (within REACH ATR) and may be exceeded only by a wick (sweep)
        near = pools[(pools <= hmax + 1.0 * a[j]) & (pools >= hmax - REACH * a[j])] if len(pools) else pools
        if not len(near):
            continue
        best = None
        for P in near:
            reach = [k for k in range(w0, j) if h[k] >= P - REACH * a[k]]
            if not reach:
                continue
            f = reach[0]
            if np.any(c[f:j] > P):
                continue                                                      # it broke out instead
            sweep = any(h[k] > P and c[k] < P for k in range(f, j))
            pushes = [k for k in range(max(f, w0 + 1), j - 1) if h[k] > h[k - 1] and h[k] >= h[k + 1]
                      and h[k] >= P - PUSH * a[k] and c[k] < P]
            lower = len(pushes) >= 2 and h[pushes[-1]] < h[pushes[0]]
            if not (sweep or lower):
                continue
            if (round(float(P), 2), f) in done:
                continue                                                      # this structure already triggered
            f_struct = pushes[0] if (lower and not sweep) else f               # neckline: the pullback low of the failure
            neck = l[f_struct:j].min()
            if c[j] < neck and c[j - 1] >= neck:
                hi = h[f:j].max()
                best = TopFail(j, side, float(P if side > 0 else -P), "sweep" if sweep else "pushes",
                               float(neck if side > 0 else -neck), float(hi * 1.001 if side > 0 else -hi * 0.999),
                               f, len(pushes))
                done.add((round(float(P), 2), f))
                break
        if best is not None:
            out.append(best)
    return out


def detect_cap(t: TF, sw_pool: dict, side: int, lookback: dict | None = None) -> list[TopFail]:
    """Sub-shape (c): the three-failures cap with an untaken higher-timeframe pool within CAP_ATR above it."""
    from .three_failures import setups
    lookback = lookback or {}
    out = []
    for j, cap_o, _, kind in setups(t, side):
        if kind != "last push":
            continue
        cap = cap_o if side > 0 else -cap_o
        pools = _pools(sw_pool, pd.Timestamp(t.ct[j - 1]), side, lookback)
        if not len(pools):
            continue
        above = pools[(pools - cap) * side > 0] if side > 0 else pools[(pools - cap) * side > 0]
        dist = (above - cap) * side
        ok = dist[(dist <= CAP_ATR * t.a[j])]
        if not len(ok):
            continue
        P = cap + side * ok.min()
        lo = t.l[j - 1] if side > 0 else t.h[j - 1]
        out.append(TopFail(j, side, float(P), "cap", float(lo), float(cap * (1 + 0.001 * side)), j - 1, 3))
    return out


def describe(t: TF, ev: TopFail) -> str:
    ot = pd.to_datetime(t.ot)
    return (f"{ot[ev.j]:%Y-%m-%d %H:%M} close {t.c[ev.j]:.1f}: {ev.kind} at the pool {ev.pool:.1f} "
            f"(first reach {ot[ev.first]:%m-%d %H:%M}, {ev.n_push} pushes), neckline {ev.neckline:.1f}, stop {ev.stop:.1f}")
