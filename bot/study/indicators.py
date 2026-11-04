"""Standard indicators. All backward-looking: value at row t uses rows <= t only."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def atr(d: pd.DataFrame, n: int = 14) -> pd.Series:
    """Wilder's ATR: seeded with the simple average of the first n true ranges, then
    atr_t = (atr_{t-1} * (n-1) + tr_t) / n."""
    prev = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - prev).abs(), (d["low"] - prev).abs()], axis=1).max(axis=1)
    tr = tr.to_numpy(float)
    out = np.full(len(tr), np.nan)
    if len(tr) >= n:
        out[n - 1] = tr[:n].mean()
        for i in range(n, len(tr)):
            out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return pd.Series(out, index=d.index)


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    diff = close.diff()
    up = diff.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-diff.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = up / dn.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(dn != 0, 100.0).where(up.notna())


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(close, fast) - ema(close, slow)
    sig = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return line, sig


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0):
    mid = sma(close, n)
    sd = close.rolling(n, min_periods=n).std(ddof=0)
    return mid, mid + k * sd, mid - k * sd


def ichimoku(d: pd.DataFrame, t: int = 9, k: int = 26, b: int = 52, shift: int = 26):
    """
    Returns tenkan, kijun, cloud_top, cloud_bottom, future_a, future_b.
    The cloud plotted at day t was computed `shift` days earlier, so cloud_* use only past data.
    future_a/b are today's span values (the cloud drawn 26 days ahead), used for kumo twists.
    """
    h, l = d["high"], d["low"]
    tenkan = (h.rolling(t, min_periods=t).max() + l.rolling(t, min_periods=t).min()) / 2
    kijun = (h.rolling(k, min_periods=k).max() + l.rolling(k, min_periods=k).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (h.rolling(b, min_periods=b).max() + l.rolling(b, min_periods=b).min()) / 2
    a_now, b_now = span_a.shift(shift), span_b.shift(shift)
    top = pd.concat([a_now, b_now], axis=1).max(axis=1, skipna=False)
    bot = pd.concat([a_now, b_now], axis=1).min(axis=1, skipna=False)
    return tenkan, kijun, top, bot, span_a, span_b


def cross_up(a: pd.Series, b) -> pd.Series:
    b = b if isinstance(b, pd.Series) else pd.Series(b, index=a.index)
    ok = a.notna() & b.notna() & a.shift(1).notna() & b.shift(1).notna()
    return ok & (a > b) & (a.shift(1) <= b.shift(1))


def cross_down(a: pd.Series, b) -> pd.Series:
    b = b if isinstance(b, pd.Series) else pd.Series(b, index=a.index)
    ok = a.notna() & b.notna() & a.shift(1).notna() & b.shift(1).notna()
    return ok & (a < b) & (a.shift(1) >= b.shift(1))


# ----------------------------------------------------------------------------- more indicators
def rma(s: pd.Series, n: int) -> pd.Series:
    """Wilder's moving average, seeded with the simple mean of the first n valid values."""
    v = s.to_numpy(float)
    out = np.full(len(v), np.nan)
    valid = np.flatnonzero(~np.isnan(v))
    if len(valid) < n:
        return pd.Series(out, index=s.index)
    start = valid[0]
    seed_end = start + n - 1
    if np.isnan(v[start:seed_end + 1]).any():
        return pd.Series(out, index=s.index)
    out[seed_end] = v[start:seed_end + 1].mean()
    for i in range(seed_end + 1, len(v)):
        out[i] = out[i - 1] if np.isnan(v[i]) else (out[i - 1] * (n - 1) + v[i]) / n
    return pd.Series(out, index=s.index)


def adx(d: pd.DataFrame, n: int = 14):
    """Wilder ADX. Returns (adx, +DI, -DI)."""
    h, l, c = d["high"], d["low"], d["close"]
    up, dn = h.diff(), -l.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=d.index).where(up.notna())
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=d.index).where(dn.notna())
    prev = c.shift(1)
    tr = pd.concat([h - l, (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1).where(prev.notna())
    atr_n = rma(tr, n)
    pdi = 100 * rma(plus_dm, n) / atr_n
    mdi = 100 * rma(minus_dm, n) / atr_n
    dx = (100 * (pdi - mdi).abs() / (pdi + mdi)).where((pdi + mdi) != 0, 0.0).where(pdi.notna())
    return rma(dx, n), pdi, mdi


def stochastic(d: pd.DataFrame, n: int = 14, smooth: int = 3) -> pd.Series:
    """Slow %K: SMA(smooth) of 100*(C-LL)/(HH-LL)."""
    hh = d["high"].rolling(n, min_periods=n).max()
    ll = d["low"].rolling(n, min_periods=n).min()
    k = 100 * (d["close"] - ll) / (hh - ll).replace(0, np.nan)
    return k.rolling(smooth, min_periods=smooth).mean()


def cci(d: pd.DataFrame, n: int = 20) -> pd.Series:
    tp = (d["high"] + d["low"] + d["close"]) / 3
    m = tp.rolling(n, min_periods=n).mean()
    mad = tp.rolling(n, min_periods=n).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - m) / (0.015 * mad.replace(0, np.nan))


def williams_r(d: pd.DataFrame, n: int = 14) -> pd.Series:
    hh = d["high"].rolling(n, min_periods=n).max()
    ll = d["low"].rolling(n, min_periods=n).min()
    return -100 * (hh - d["close"]) / (hh - ll).replace(0, np.nan)


def mfi(d: pd.DataFrame, n: int = 14) -> pd.Series:
    tp = (d["high"] + d["low"] + d["close"]) / 3
    mf = tp * d["volume"]
    pos = mf.where(tp > tp.shift(1), 0.0).where(tp.shift(1).notna())
    neg = mf.where(tp < tp.shift(1), 0.0).where(tp.shift(1).notna())
    ps = pos.rolling(n, min_periods=n).sum()
    ns = neg.rolling(n, min_periods=n).sum()
    out = 100 - 100 / (1 + ps / ns.replace(0, np.nan))
    out = out.where(ns != 0, 100.0)
    out = out.where(~((ps == 0) & (ns == 0)), 50.0)  # flat window: no flow either way -> neutral
    return out.where(ps.notna())


def obv(d: pd.DataFrame) -> pd.Series:
    step = np.sign(d["close"].diff()).fillna(0) * d["volume"]
    return step.cumsum()


def cmf(d: pd.DataFrame, n: int = 20) -> pd.Series:
    rng = (d["high"] - d["low"]).replace(0, np.nan)
    mfm = (((d["close"] - d["low"]) - (d["high"] - d["close"])) / rng).fillna(0.0)
    mfv = mfm * d["volume"]
    return mfv.rolling(n, min_periods=n).sum() / d["volume"].rolling(n, min_periods=n).sum().replace(0, np.nan)


def rolling_vwap(d: pd.DataFrame, n: int = 20) -> pd.Series:
    tp = (d["high"] + d["low"] + d["close"]) / 3
    pv = (tp * d["volume"]).rolling(n, min_periods=n).sum()
    return pv / d["volume"].rolling(n, min_periods=n).sum().replace(0, np.nan)


def keltner(d: pd.DataFrame, n: int = 20, k: float = 2.0, atr_n: int = 10):
    mid = ema(d["close"], n)
    a = atr(d, atr_n)
    return mid, mid + k * a, mid - k * a


def donchian(d: pd.DataFrame, n: int = 20):
    return d["high"].rolling(n, min_periods=n).max(), d["low"].rolling(n, min_periods=n).min()


def supertrend(d: pd.DataFrame, n: int = 10, mult: float = 3.0) -> pd.Series:
    """+1 uptrend, -1 downtrend (standard final-band recursion), NaN during warm-up."""
    h, l, c = d["high"].to_numpy(float), d["low"].to_numpy(float), d["close"].to_numpy(float)
    a = atr(d, n).to_numpy(float)
    hl2 = (h + l) / 2
    bu, bl = hl2 + mult * a, hl2 - mult * a
    fu, fl = np.full(len(c), np.nan), np.full(len(c), np.nan)
    trend = np.full(len(c), np.nan)
    for i in range(len(c)):
        if np.isnan(a[i]):
            continue
        if np.isnan(fu[i - 1]) if i > 0 else True:
            fu[i], fl[i] = bu[i], bl[i]
            trend[i] = 1.0 if c[i] >= hl2[i] else -1.0
            continue
        fu[i] = bu[i] if (bu[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = bl[i] if (bl[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
        if trend[i - 1] == 1.0:
            trend[i] = -1.0 if c[i] < fl[i] else 1.0
        else:
            trend[i] = 1.0 if c[i] > fu[i] else -1.0
    return pd.Series(trend, index=d.index)


def psar(d: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
    """
    Parabolic SAR (Wilder). Starts long with SAR = first low, EP = first high; first output on bar 1.
    The SAR may not move inside the last two bars' range; on a reversal it jumps to the prior
    extreme point, but never inside the reversal bar (or the bar before it).
    """
    h, l = d["high"].to_numpy(float), d["low"].to_numpy(float)
    n = len(h)
    out = np.full(n, np.nan)
    if n < 2:
        return pd.Series(out, index=d.index)
    up, af, ep, sar = True, step, h[0], l[0]
    for i in range(1, n):
        s = sar + af * (ep - sar)
        if up:
            s = min(s, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if l[i] < s:  # reversal to down
                up, s, ep, af = False, max(ep, h[i], h[i - 1]), l[i], step
            elif h[i] > ep:
                ep, af = h[i], min(af + step, max_step)
        else:
            s = max(s, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > s:  # reversal to up
                up, s, ep, af = True, min(ep, l[i], l[i - 1]), h[i], step
            elif l[i] < ep:
                ep, af = l[i], min(af + step, max_step)
        out[i] = sar = s
    return pd.Series(out, index=d.index)
