"""
Support / resistance hints at entry, from swing points that were CONFIRMED before entry.

Levels = swing highs and swing lows (both act as support/resistance; broken ones flip role):
  * daily candles, K=3, from the last 180 days
  * 4h candles,   K=5, from the last 60 days
  * weekly candles, K=3, from the last 2 years
Strong zones: swings clustered within 1%, kept if touched >= 3 times or containing a weekly swing.
A swing at candle i is known once candle i+K has closed.

Hints (-1 = warns against the trade, 0 otherwise):
  sr_into_level   short: a level within 0.5 ATR BELOW entry (selling into support)
                  long:  a level within 0.5 ATR ABOVE entry (buying into resistance)
  sr_path_2plus   2 or more distinct levels (merged within 1%) between entry and the +2 ATR target
  sr_sweep        the signal-day candle wicked through a level and closed back on the other side,
                  against the trade (short after a support sweep / long after a resistance sweep)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .mtf import resample
from .patterns import swing_points

SOURCES = [("1W", "W-MON", 3, pd.Timedelta(weeks=104)), ("1D", "1D", 3, pd.Timedelta(days=180)),
           ("4h", "4h", 5, pd.Timedelta(days=60))]
MERGE = 0.01
STRONG_TOUCHES = 3   # a zone touched by >= 3 swings, or containing a weekly swing, is a strong level


def _level_table(df5: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tf, rule, k, look in SOURCES:
        b = resample(df5, rule).reset_index(drop=True)
        sh, sl = swing_points(b["high"].to_numpy(float), b["low"].to_numpy(float), k)
        for i, p, c in sh + sl:
            rows.append({"tf": tf, "price": p, "formed": b["open_time"].iloc[i],
                         "known": b["close_time"].iloc[c], "lookback": look})
    t = pd.DataFrame(rows)
    t["formed"] = pd.to_datetime(t["formed"], utc=True)
    t["known"] = pd.to_datetime(t["known"], utc=True)
    return t


def levels_at(table: pd.DataFrame, t: pd.Timestamp) -> np.ndarray:
    ok = (table["known"] <= t) & (table["formed"] >= t - table["lookback"])
    return np.sort(table.loc[ok, "price"].to_numpy(float))


def strong_levels(table: pd.DataFrame, t: pd.Timestamp) -> np.ndarray:
    """Cluster swings known at t into zones (within MERGE of the zone's first price); keep strong zones."""
    ok = (table["known"] <= t) & (table["formed"] >= t - table["lookback"])
    sw = table.loc[ok].sort_values("price")
    zones, cur = [], []
    for p, tf in zip(sw["price"].to_numpy(float), sw["tf"].to_numpy()):
        if cur and p > cur[0][0] * (1 + MERGE):
            zones.append(cur)
            cur = []
        cur.append((p, tf))
    if cur:
        zones.append(cur)
    out = [np.mean([p for p, _ in z]) for z in zones
           if len(z) >= STRONG_TOUCHES or any(tf == "1W" for _, tf in z)]
    return np.array(out)


def _distinct(levels: np.ndarray) -> np.ndarray:
    out: list[float] = []
    for p in np.sort(levels):
        if not out or p > out[-1] * (1 + MERGE):
            out.append(p)
    return np.array(out)


def level_hints(trades: pd.DataFrame, df5: pd.DataFrame, target_atr: float = 2.0, strong: bool = True,
                into_atr: float = 0.5) -> pd.DataFrame:
    """
    trades needs: entry_time, direction, entry, atr14.
    strong=True uses only strong zones (>= 3 touches or a weekly swing); False uses every swing (loose).
    """
    table = _level_table(df5)
    get = strong_levels if strong else levels_at
    daily = resample(df5, "1D")
    daily = daily.set_index(pd.to_datetime(daily["close_time"], utc=True))
    out = {"sr_into_level": [], "sr_path_2plus": [], "sr_sweep": []}
    for et, d, e, a in zip(pd.to_datetime(trades["entry_time"], utc=True), trades["direction"],
                           trades["entry"], trades["atr14"]):
        sig = daily.loc[et] if et in daily.index else None  # the signal-day candle (closes at entry)
        lv_now = get(table, et)
        if d < 0:
            into = ((lv_now < e) & (lv_now >= e - into_atr * a)).any()
            path = _distinct(lv_now[(lv_now < e) & (lv_now > e - target_atr * a)])
        else:
            into = ((lv_now > e) & (lv_now <= e + into_atr * a)).any()
            path = _distinct(lv_now[(lv_now > e) & (lv_now < e + target_atr * a)])
        sweep = False
        if sig is not None:
            # levels known before the signal candle opened, so its own swing can't be used
            lv_before = get(table, et - pd.Timedelta(days=1))
            if d < 0:   # bullish sweep: low pierced a level, close back above it
                sweep = ((sig["low"] < lv_before) & (sig["close"] > lv_before)).any()
            else:       # bearish sweep: high pierced a level, close back below it
                sweep = ((sig["high"] > lv_before) & (sig["close"] < lv_before)).any()
        out["sr_into_level"].append(-1 if into else 0)
        out["sr_path_2plus"].append(-1 if len(path) >= 2 else 0)
        out["sr_sweep"].append(-1 if sweep else 0)
    return pd.DataFrame(out, index=trades.index)
