"""
Weekly trend: Up / Down / Sideways, from completed weeks only (Mon-Sun UTC).

  Up       weekly close above BOTH SMA20w and SMA50w, and SMA20w rising vs 3 weeks ago
  Down     weekly close below BOTH SMA20w and SMA50w, and SMA20w falling vs 3 weeks ago
  Sideways anything else
  Unknown  fewer than 50 completed weeks of history (SMA50w not available yet)

(No SMA20w-vs-SMA50w crossover requirement: it lagged by months, e.g. ETH fell 60% from
Nov 2025 to Feb 2026 while still "Sideways" because the 20w average was above the 50w.)

A week becomes usable at its Sunday close (Monday 00:00 UTC), so on a Sunday the
trend already includes the week that just ended, and never anything later.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SLOPE_WEEKS = 3


def weekly_bars(daily: pd.DataFrame) -> pd.DataFrame:
    w = daily.set_index("ts").resample("W-MON", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "day": "count"}
    ).rename(columns={"day": "n_days"})
    return w.dropna(subset=["close"])


def weekly_trend_table(daily: pd.DataFrame) -> pd.DataFrame:
    w = weekly_bars(daily)
    w = w[w["n_days"] == 7]  # a partial week (start/end of data) is not a completed week
    c = w["close"]
    s20 = c.rolling(20, min_periods=20).mean()
    s50 = c.rolling(50, min_periods=50).mean()
    rising = s20 > s20.shift(SLOPE_WEEKS)
    falling = s20 < s20.shift(SLOPE_WEEKS)
    up = (c > s20) & (c > s50) & rising
    dn = (c < s20) & (c < s50) & falling
    trend = np.where(up, "Up", np.where(dn, "Down", "Sideways"))
    trend = np.where(s50.isna() | s20.shift(SLOPE_WEEKS).isna(), "Unknown", trend)
    return pd.DataFrame({
        "available_at": (w.index + pd.Timedelta(days=7)).as_unit("ns"),
        "week_start": w.index,
        "weekly_trend": trend,
        "w_close": c.to_numpy(),
        "w_sma20": s20.to_numpy(),
        "w_sma50": s50.to_numpy(),
    })


def add_weekly_trend(daily: pd.DataFrame) -> pd.DataFrame:
    """Attach the weekly trend known at each day's close."""
    tbl = weekly_trend_table(daily)
    d = daily.copy()
    d["_close_time"] = (d["ts"] + pd.Timedelta(days=1)).dt.as_unit("ns")
    d = pd.merge_asof(
        d.sort_values("_close_time"), tbl[["available_at", "weekly_trend"]].sort_values("available_at"),
        left_on="_close_time", right_on="available_at", direction="backward",
    ).drop(columns=["_close_time", "available_at"])
    d["weekly_trend"] = d["weekly_trend"].fillna("Unknown")
    return d


def alignment(direction: int, trend: str) -> str:
    if trend == "Unknown":
        return "unknown"
    if trend == "Sideways":
        return "sideways"
    with_trend = (trend == "Up" and direction > 0) or (trend == "Down" and direction < 0)
    return "with" if with_trend else "against"
