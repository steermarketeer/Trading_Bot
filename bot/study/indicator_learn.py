"""
Learning the indicators: each one's classic signals tested the same fair way on ETH, so they can be compared.

Fair test: at the close of the signal candle, does price move 1.5 ATR in the direction the signal claims before it
moves 1.5 ATR against (within 30 candles of that timeframe; a candle doing both is dropped)? A coin flip = 50%.
Bullish and mirrored bearish signals are pooled ("right %"). Each signal is an EVENT (the candle where it appears), not
a state held for many candles, except where marked "state". Split by the daily trend (close above / below the daily
EMA 200 at the signal), by year (2020 - 2025: years above 50%), and the holdout (Nov 2025 on) separately.
Also: how much the indicators overlap (rank correlation of their values on 4h), to see which ones say the same thing.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .defs import TF
from .indicators import ema, ichimoku, macd, rsi
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
K, HORIZON = 1.5, 30


def outcome(t: TF) -> np.ndarray:
    """1 = +K ATR first, 0 = -K ATR first, nan = neither / both in one candle."""
    out = np.full(t.n, np.nan)
    for j in range(t.n - 1):
        a = t.a[j]
        if not np.isfinite(a):
            continue
        up, dn = t.c[j] + K * a, t.c[j] - K * a
        for k in range(j + 1, min(t.n, j + 1 + HORIZON)):
            hu, hd = t.h[k] >= up, t.l[k] <= dn
            if hu and hd:
                break
            if hu:
                out[j] = 1; break
            if hd:
                out[j] = 0; break
    return out


SHIFTS = 400


def event_pvalue(y, bu, be) -> float:
    """Circular time-shift test (2020 - Oct 2025 only): move the signal's event dates by a random offset (keeping their
    clustering) and count how often the shifted copy is as far from its own coin-flip rate as the real one."""
    def rate(b, e):
        r = np.concatenate([y[b], 1 - y[e]])
        r = r[~np.isnan(r)]
        return r.mean() if len(r) else np.nan
    n = len(y)
    obs = rate(bu, be)
    if not np.isfinite(obs) or (bu.sum() + be.sum()) < 20:
        return 1.0
    rng = np.random.default_rng(5)
    null = np.array([rate(np.roll(bu, k), np.roll(be, k)) for k in rng.integers(n // 20, n - n // 20, SHIFTS)])
    null = null[np.isfinite(null)]
    return (np.sum(np.abs(null - null.mean()) >= abs(obs - null.mean())) + 1) / (len(null) + 1)


def _cross_up(x, y):
    return (x > y) & (np.r_[False, x[:-1] <= y[:-1]])


def _swing_div(t: TF, ind: np.ndarray, side: int, look=30):
    """Bearish (side +1): a confirmed swing high above the previous swing high (within `look`), indicator lower.
    Event at the confirming candle. Mirrored for bullish (side -1)."""
    ev = np.zeros(t.n, bool)
    pts = t.sh if side > 0 else t.sl
    for (i1, p1, _), (i2, p2, cf2) in zip(pts[:-1], pts[1:]):
        if i2 - i1 > look or cf2 >= t.n:
            continue
        if side > 0 and p2 > p1 and ind[i2] < ind[i1]:
            ev[cf2] = True
        if side < 0 and p2 < p1 and ind[i2] > ind[i1]:
            ev[cf2] = True
    return ev


def signals(t: TF):
    """Dict name -> (bullish event mask, bearish event mask). Masks at the candle whose close shows the signal."""
    c, h, l, o, v = t.c, t.h, t.l, t.o, t.v
    s = pd.Series(c)
    e20, e50, e200 = (ema(s, k).to_numpy(float) for k in (20, 50, 200))
    ml, ms = (x.to_numpy(float) for x in macd(s))
    mh = ml - ms
    r = rsi(s).to_numpy(float)
    up, lo, mid = t.up, t.lo, t.mid
    v20 = pd.Series(v).shift(1).rolling(20).mean().to_numpy()
    hi20 = pd.Series(h).shift(1).rolling(20).max().to_numpy()
    lo20 = pd.Series(l).shift(1).rolling(20).min().to_numpy()
    prev = lambda x: np.r_[np.nan, x[:-1]]  # noqa: E731
    S = {}
    # --- moving averages
    S["EMA: close crosses above / below EMA 20"] = (_cross_up(c, e20), _cross_up(-c, -e20))
    S["EMA: close crosses above / below EMA 200"] = (_cross_up(c, e200), _cross_up(-c, -e200))
    S["EMA: 20 crosses 50 (golden / death cross)"] = (_cross_up(e20, e50), _cross_up(-e20, -e50))
    stack_u, stack_d = (e20 > e50) & (e50 > e200), (e20 < e50) & (e50 < e200)
    S["EMA: state - 20 > 50 > 200 stacked (every candle)"] = (stack_u, stack_d)
    S["EMA: pullback to EMA 20 in a stacked trend, close back above"] = (
        stack_u & (l <= e20) & (c > e20), stack_d & (h >= e20) & (c < e20))
    S["EMA: pullback to EMA 50 in a stacked trend, close back above"] = (
        stack_u & (l <= e50) & (c > e50), stack_d & (h >= e50) & (c < e50))
    # --- MACD
    xu, xd = _cross_up(ml, ms), _cross_up(-ml, -ms)
    S["MACD: line crosses signal"] = (xu, xd)
    S["MACD: cross on the trend side of zero (bull cross above 0)"] = (xu & (ml > 0), xd & (ml < 0))
    S["MACD: cross on the far side of zero (bull cross below 0)"] = (xu & (ml < 0), xd & (ml > 0))
    S["MACD: line crosses zero"] = (_cross_up(ml, np.zeros_like(ml)), _cross_up(-ml, np.zeros_like(ml)))
    S["MACD: histogram turns (first rising bar below 0)"] = ((mh < 0) & (mh > prev(mh)) & (prev(mh) <= np.r_[np.nan, prev(mh)[:-1]]),
                                                            (mh > 0) & (mh < prev(mh)) & (prev(mh) >= np.r_[np.nan, prev(mh)[:-1]]))
    S["MACD: divergence (price new low, MACD higher low)"] = (_swing_div(t, ml, -1), _swing_div(t, ml, 1))
    # --- RSI
    S["RSI: crosses above 70 / below 30 (momentum reading)"] = (_cross_up(r, np.full_like(r, 70)), _cross_up(-r, np.full_like(r, -30)))
    S["RSI: crosses below 30 / above 70 (classic 'buy oversold')"] = (_cross_up(-r, np.full_like(r, -30)), _cross_up(r, np.full_like(r, 70)))
    S["RSI: back above 30 / below 70 (leaves the extreme)"] = (_cross_up(r, np.full_like(r, 30)), _cross_up(-r, np.full_like(r, -70)))
    S["RSI: crosses 50"] = (_cross_up(r, np.full_like(r, 50)), _cross_up(-r, np.full_like(r, -50)))
    S["RSI: divergence (price new low, RSI higher low)"] = (_swing_div(t, r, -1), _swing_div(t, r, 1))
    S["RSI: 40-50 dip in an uptrend, turns up (Cardwell range)"] = (
        (e50 > e200) & (prev(r) >= 40) & (prev(r) <= 50) & (r > prev(r)) & (prev(r) < np.r_[np.nan, prev(r)[:-1]]),
        (e50 < e200) & (prev(r) >= 50) & (prev(r) <= 60) & (r < prev(r)) & (prev(r) > np.r_[np.nan, prev(r)[:-1]]))
    # --- Bollinger
    S["Bollinger: close outside the band (momentum reading)"] = (_cross_up(c, up), _cross_up(-c, -lo))
    S["Bollinger: close outside the band (classic 'fade it')"] = (_cross_up(-c, -lo), _cross_up(c, up))
    S["Bollinger: band failure (close outside, then back inside)"] = (
        (c > lo) & (prev(c) < prev(lo)), (c < up) & (prev(c) > prev(up)))
    S["Bollinger: pullback to the middle band in an uptrend, holds"] = (
        (mid > prev(mid)) & (c > e200) & (l <= mid) & (c > mid), (mid < prev(mid)) & (c < e200) & (h >= mid) & (c < mid))
    bw = (up - lo) / mid
    rank = pd.Series(bw).rolling(120, min_periods=60).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True).to_numpy()
    sq = np.r_[np.full(5, np.nan), rank[:-5]] <= 0.2
    S["Bollinger: squeeze breakout (close outside after a squeeze)"] = (sq & _cross_up(c, up), sq & _cross_up(-c, -lo))
    # --- volume
    brk_u, brk_d = (c > hi20), (c < lo20)
    S["Volume: 20-candle breakout close on volume >= 1.5x"] = (brk_u & (v >= 1.5 * v20), brk_d & (v >= 1.5 * v20))
    S["Volume: 20-candle breakout close on low volume (< 1x)"] = (brk_u & (v < v20), brk_d & (v < v20))
    # --- Ichimoku (Hosoda 9 / 26 / 52; the cloud at each candle was computed 26 candles earlier)
    tk, kj, ctop, cbot, fa, fb = (x.to_numpy(float) for x in ichimoku(t.b))
    S["Ichimoku: Tenkan crosses Kijun (any position)"] = (_cross_up(tk, kj), _cross_up(-tk, -kj))
    S["Ichimoku: TK cross on the trend side of the cloud (strong)"] = (_cross_up(tk, kj) & (c > ctop), _cross_up(-tk, -kj) & (c < cbot))
    S["Ichimoku: close breaks out of the cloud"] = (_cross_up(c, ctop), _cross_up(-c, -cbot))
    S["Ichimoku: cloud breakout with Chikou free and a bullish future cloud"] = (
        _cross_up(c, ctop) & (c > np.r_[np.full(26, np.nan), h[:-26]]) & (fa > fb),
        _cross_up(-c, -cbot) & (c < np.r_[np.full(26, np.nan), l[:-26]]) & (fa < fb))
    S["Ichimoku: Kijun bounce above / below the cloud"] = (
        (c > ctop) & (l <= kj) & (c > kj) & (prev(l) > prev(kj)), (c < cbot) & (h >= kj) & (c < kj) & (prev(h) < prev(kj)))
    S["Ichimoku: kumo twist (future cloud turns)"] = (_cross_up(fa, fb), _cross_up(fb, fa))
    S["Ichimoku: Chikou crosses the price of 26 candles ago"] = (_cross_up(c, np.r_[np.full(26, np.nan), c[:-26]]),
                                                               _cross_up(-c, -np.r_[np.full(26, np.nan), c[:-26]]))
    # --- price action reference points (main rules, for comparison)
    S["Price: 20-candle breakout close (any volume)"] = (brk_u, brk_d)
    return S, {"e20": (c - e20) / t.a, "e50": (c - e50) / t.a, "e200": (c - e200) / t.a, "macd_line": ml / t.a,
               "macd_hist": mh / t.a, "rsi": r, "bb_%b": (c - lo) / (up - lo), "bb_width": bw,
               "ret20": (c - np.r_[np.full(20, np.nan), c[:-20]]) / t.a, "vol_ratio": v / v20}


def run_indicator_learn(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    d1 = TF(resample(df5u, "1D"))
    d_e200 = ema(pd.Series(d1.c), 200).to_numpy(float)
    L = ["# Learning the indicators: every classic signal, the same fair test", "",
         f"At the signal close: does ETH move {K} ATR the way the signal says before {K} ATR against (30 candles max)? "
         "**A coin flip = 50%.** Bullish and mirrored bearish signals pooled. Research 2020 - Oct 2025, holdout Nov 2025 on. "
         "**chance it is noise**: the share of 400 time-shifted copies of the signal (same events moved to random dates, "
         "clustering kept) that are as far from a coin flip as the real one; below 0.01 = real.", ""]
    for tf in ("1h", "4h", "1D"):
        t = TF(resample(df5u, tf))
        y = outcome(t)
        ot = pd.to_datetime(t.ot)
        jd = np.searchsorted(d1.ct, t.ct, side="right") - 1
        jdc = np.clip(jd, 0, None)
        e_ok = (jd >= 0) & np.isfinite(d_e200[jdc])                  # no daily EMA 200 yet: in neither trend column
        bull_day = e_ok & (d1.c[jdc] > d_e200[jdc])
        hold = np.asarray(ot >= HOLDOUT)
        late = np.asarray((ot < HOLDOUT) & (ot >= HOLDOUT - HORIZON * pd.Timedelta(tf)))   # outcome would use holdout prices
        years = np.asarray(ot.year)
        S, vals = signals(t)
        rows = []
        for name, (bu, be) in S.items():
            bu, be = np.nan_to_num(bu).astype(bool), np.nan_to_num(be).astype(bool)
            bu, be = bu & ~late, be & ~late
            right = np.concatenate([y[bu], 1 - y[be]])
            hd = np.concatenate([hold[bu], hold[be]])
            eok = np.concatenate([e_ok[bu], e_ok[be]])
            yr = np.concatenate([years[bu], years[be]])
            trend = np.concatenate([bull_day[bu], ~bull_day[be]])        # signal WITH the daily trend
            ok = ~np.isnan(right)
            right, hd, yr, trend, eok = right[ok], hd[ok], yr[ok], trend[ok], eok[ok]
            res = ~hd
            good_years = sum(1 for yy in range(2020, 2026) if (m := res & (yr == yy)).sum() >= 10 and right[m].mean() > 0.5)
            n_years = sum(1 for yy in range(2020, 2026) if (res & (yr == yy)).sum() >= 10)
            okr = ~hold & ~late
            pv = event_pvalue(y[okr], bu[okr], be[okr])
            rows.append({"sig": name, "n": int(res.sum()), "p": right[res].mean(), "pv": pv, "pw": right[res & eok & trend].mean(),
                         "pa": right[res & eok & ~trend].mean(), "yrs": f"{good_years}/{n_years}", "nh": int(hd.sum()),
                         "ph": right[hd].mean() if hd.sum() else np.nan})
        base = np.nanmean(y[~hold])
        L += [f"## {tf} (all candles: up first {base:.0%})", "",
              _table(pd.DataFrame(rows), [("sig", "signal", str), ("n", "cases", lambda v: f"{v:,}"), ("p", "right", _pct),
                                          ("pv", "chance it is noise", lambda v: f"{v:.3f}"),
                                          ("pw", "right, with the daily trend", _pct), ("pa", "right, against it", _pct),
                                          ("yrs", "years above 50%", str), ("nh", "holdout cases", str), ("ph", "holdout right", _pct)]), ""]
        if tf == "4h":
            V = pd.DataFrame(vals).replace([np.inf, -np.inf], np.nan).dropna()
            Cm = V.corr(method="spearman")
            L += ["## How much the indicators say the same thing (4h, rank correlation of their values; 1 = identical)", "",
                  "| | " + " | ".join(Cm.columns) + " |", "|---" * (len(Cm.columns) + 1) + "|"]
            L += [f"| {i} | " + " | ".join(f"{Cm.loc[i, j]:+.2f}" for j in Cm.columns) + " |" for i in Cm.index]
            L += [""]
    path = out_dir / "indicator_learn.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_indicator_learn(load_config(ROOT / "config.yaml"), ROOT / "reports"))
