"""
Multi-timeframe "hints" at the moment of each trade entry.

For every trade we look at 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1D and 1W charts and read the
state of standard indicators on the LAST CANDLE THAT HAD CLOSED at entry time (no hindsight).
Each hint is expressed relative to the trade: +1 = supports the trade's direction,
-1 = points the opposite way ("warning"), 0 = neutral.

Hints per timeframe:
  trend      close vs EMA50
  slope      EMA20 rising/falling vs 3 candles ago
  macd       MACD histogram sign
  macd_fade  MACD histogram shrinking for 2 candles in the trade direction (momentum fading)
  rsi_ext    RSI(14) > 70 for a long / < 30 for a short = stretched against the trade
  cloud      close above / below the Ichimoku cloud
  bb_ext     close outside the Bollinger band in the trade direction (over-extended)
  stretch    more than 2 ATR away from EMA20 in the trade direction
  diverge    price at a 20-candle extreme but RSI is not (bearish/bullish divergence)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import atr, bollinger, ema, ichimoku, macd, rsi

TIMEFRAMES = {
    "15m": "15min", "30m": "30min", "1h": "1h", "2h": "2h", "4h": "4h",
    "6h": "6h", "8h": "8h", "12h": "12h", "1D": "1D", "1W": "W-MON",
}
HINTS = ["trend", "slope", "macd", "macd_fade", "rsi_ext", "cloud", "bb_ext", "stretch", "diverge"]


def resample(df5: pd.DataFrame, rule: str) -> pd.DataFrame:
    x = df5.set_index("open_time")
    b = x.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["close"]).reset_index()
    if rule == "W-MON":
        dur = pd.Timedelta(days=7)
    else:
        dur = pd.Timedelta(rule)
    b["close_time"] = (b["open_time"] + dur).dt.as_unit("ns")
    # drop the final candle if it had not finished when the data ends
    if b["close_time"].iloc[-1] > df5["open_time"].iloc[-1] + pd.Timedelta(minutes=5):
        b = b.iloc[:-1]
    return b


def tf_states(b: pd.DataFrame) -> pd.DataFrame:
    """Raw (direction-free) indicator states per candle: +1 bullish, -1 bearish, 0 neutral."""
    c = b["close"]
    e20, e50 = ema(c, 20), ema(c, 50)
    line, sig = macd(c)
    hist = line - sig
    r = rsi(c)
    mid, up, lo = bollinger(c)
    _, _, top, bot, _, _ = ichimoku(b)
    a = atr(b, 14)
    out = pd.DataFrame({"close_time": b["close_time"]})
    out["trend"] = np.sign(c - e50).where(e50.notna(), 0)
    out["slope"] = np.sign(e20 - e20.shift(3)).where(e20.shift(3).notna(), 0)
    out["macd"] = np.sign(hist).where(hist.notna(), 0)
    # fading: histogram positive but falling 2 candles -> bullish momentum fading (-1 for longs)
    falling = (hist < hist.shift(1)) & (hist.shift(1) < hist.shift(2))
    rising = (hist > hist.shift(1)) & (hist.shift(1) > hist.shift(2))
    out["macd_fade"] = np.where((hist > 0) & falling, -1, np.where((hist < 0) & rising, 1, 0))
    # stretched: overbought counts as a bearish hint, oversold as bullish
    out["rsi_ext"] = np.where(r > 70, -1, np.where(r < 30, 1, 0))
    out["cloud"] = np.where(c > top, 1, np.where(c < bot, -1, 0))
    out["bb_ext"] = np.where(c > up, -1, np.where(c < lo, 1, 0))
    dist = (c - e20) / a
    out["stretch"] = np.where(dist > 2, -1, np.where(dist < -2, 1, 0))
    hh = c >= c.rolling(20, min_periods=20).max()
    ll = c <= c.rolling(20, min_periods=20).min()
    r_hi = r < r.rolling(20, min_periods=20).max() - 5
    r_lo = r > r.rolling(20, min_periods=20).min() + 5
    out["diverge"] = np.where(hh & r_hi, -1, np.where(ll & r_lo, 1, 0))
    return out


def hints_at(df5: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """
    trades: needs `entry_time` (UTC Timestamp) and `direction` (+1/-1).
    Returns trades + one column per (timeframe, hint): +1 supports, -1 warns, 0 neutral.
    """
    t = trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True).dt.as_unit("ns")
    t = t.sort_values("entry_time")
    for tf, rule in TIMEFRAMES.items():
        st = tf_states(resample(df5, rule))
        st = st.rename(columns={h: f"{tf}_{h}" for h in HINTS})
        t = pd.merge_asof(t, st, left_on="entry_time", right_on="close_time", direction="backward")
        t = t.drop(columns="close_time")
        for h in HINTS:
            col = f"{tf}_{h}"
            t[col] = (t[col].fillna(0) * t["direction"]).astype(int)
    return t.sort_index()


def hint_columns() -> list[str]:
    return [f"{tf}_{h}" for tf in TIMEFRAMES for h in HINTS]
