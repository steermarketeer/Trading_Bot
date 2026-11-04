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
