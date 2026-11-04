"""
Standard indicator signals on daily bars. Each fires on a day's close with a direction
(+1 bullish, -1 bearish). Only data up to and including that day is used.
"""
from __future__ import annotations

import pandas as pd

from .indicators import atr, bollinger, cross_down, cross_up, ichimoku, macd, rsi, sma

# (signal name, plain-English description) — shown in the report
SIGNAL_INFO = {
    "ichimoku_tk_cross": "Tenkan (9) crosses Kijun (26)",
    "ichimoku_cloud_break": "Close breaks out of the Ichimoku cloud (above top / below bottom)",
    "ichimoku_kumo_twist": "Future cloud changes colour (Span A crosses Span B)",
    "macd_signal_cross": "MACD (12,26) crosses its 9-day signal line",
    "macd_zero_cross": "MACD line crosses zero",
    "ma30_cross": "Close crosses the 30-day average",
    "ma60_cross": "Close crosses the 60-day average",
    "ma200_cross": "Close crosses the 200-day average",
    "golden_death_cross": "50-day average crosses the 200-day average",
    "bb_breakout": "Close moves outside a Bollinger band (20, 2) - continuation",
    "bb_reversal": "Close comes back inside a Bollinger band after closing outside - reversal",
    "bb_squeeze_breakout": "Bollinger breakout within 5 days of a 120-day low in band width",
    "volume_spike": "Volume > 2x its 20-day average; direction = day's candle colour",
    "rsi_reversal": "RSI (14) crosses back above 30 (bullish) / below 70 (bearish)",
}


def _events(day: pd.Series, mask_up: pd.Series, mask_dn: pd.Series, name: str) -> pd.DataFrame:
    up = pd.DataFrame({"day": day[mask_up.fillna(False).astype(bool)], "direction": 1})
    dn = pd.DataFrame({"day": day[mask_dn.fillna(False).astype(bool)], "direction": -1})
    out = pd.concat([up, dn])
    out["signal"] = name
    return out


def compute_signals(d: pd.DataFrame) -> pd.DataFrame:
    """d: daily bars with day, open, high, low, close, volume. Returns day, direction, signal."""
    c, day = d["close"], d["day"]
    ev = []

    tenkan, kijun, top, bot, fa, fb = ichimoku(d)
    ev.append(_events(day, cross_up(tenkan, kijun), cross_down(tenkan, kijun), "ichimoku_tk_cross"))
    ev.append(_events(day, cross_up(c, top), cross_down(c, bot), "ichimoku_cloud_break"))
    ev.append(_events(day, cross_up(fa, fb), cross_down(fa, fb), "ichimoku_kumo_twist"))

    line, sig = macd(c)
    ev.append(_events(day, cross_up(line, sig), cross_down(line, sig), "macd_signal_cross"))
    ev.append(_events(day, cross_up(line, 0.0), cross_down(line, 0.0), "macd_zero_cross"))

    for n in (30, 60, 200):
        m = sma(c, n)
        ev.append(_events(day, cross_up(c, m), cross_down(c, m), f"ma{n}_cross"))
    s50, s200 = sma(c, 50), sma(c, 200)
    ev.append(_events(day, cross_up(s50, s200), cross_down(s50, s200), "golden_death_cross"))

    mid, upper, lower = bollinger(c)
    ev.append(_events(day, cross_up(c, upper), cross_down(c, lower), "bb_breakout"))
    # back inside: yesterday closed below the lower band, today closes above it (bullish), and mirror
    ev.append(_events(day, cross_up(c, lower), cross_down(c, upper), "bb_reversal"))
    width = (upper - lower) / mid
    squeeze = width <= width.rolling(120, min_periods=120).min() * 1.0001
    recent_squeeze = squeeze.astype(float).rolling(5, min_periods=1).max().shift(1).fillna(0) > 0
    ev.append(_events(day, cross_up(c, upper) & recent_squeeze, cross_down(c, lower) & recent_squeeze,
                      "bb_squeeze_breakout"))

    vol = d["volume"]
    vavg = vol.shift(1).rolling(20, min_periods=20).mean()
    spike = vol > 2 * vavg
    ev.append(_events(day, spike & (c > d["open"]), spike & (c < d["open"]), "volume_spike"))

    r = rsi(c)
    ev.append(_events(day, cross_up(r, 30.0), cross_down(r, 70.0), "rsi_reversal"))

    out = pd.concat(ev, ignore_index=True)
    out["kind"] = "signal"
    return out[["day", "signal", "direction", "kind"]]


__all__ = ["compute_signals", "SIGNAL_INFO", "atr"]
