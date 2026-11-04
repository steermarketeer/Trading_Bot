"""
Rule-based master regime (Bull / Bear / Neutral), computed from completed daily bars.

Same scoring as the legacy regime.py:
  ETH weekly score  = close>SMA20 + close>SMA50 + SMA20>SMA50 + Ichimoku cloud side   (-4..+4)
  ETH monthly struct= +1 higher-high & higher-low, -1 lower-high & lower-low, else 0
  BTC weekly score  = same as ETH weekly
  total = weekly + 1.5*monthly + 0.5*sign(btc weekly)   -> Bull >= 2, Bear <= -2

No lookahead: a week (Mon-Sun UTC) or month is only used once it has fully closed.
`extra_lag` pushes it back further by N periods (legacy behaviour = 1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _resample(daily: pd.DataFrame, rule: str) -> pd.DataFrame:
    x = daily.set_index("ts")
    return x.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna(subset=["close"])


def _ichimoku_side(w: pd.DataFrame) -> pd.Series:
    h, l, c = w["high"], w["low"], w["close"]
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (h.rolling(52).max() + l.rolling(52).min()) / 2
    top = np.maximum(span_a, span_b)
    bot = np.minimum(span_a, span_b)
    side = pd.Series(np.where(c > top, 1.0, np.where(c < bot, -1.0, 0.0)), index=w.index)
    return side.where(span_b.notna())


def weekly_score(w: pd.DataFrame) -> pd.Series:
    c = w["close"]
    s20 = c.rolling(20, min_periods=20).mean()
    s50 = c.rolling(50, min_periods=50).mean()
    score = (
        np.where(c > s20, 1.0, -1.0)
        + np.where(c > s50, 1.0, -1.0)
        + np.where(s20 > s50, 1.0, -1.0)
    )
    score = pd.Series(score, index=w.index) + _ichimoku_side(w).fillna(0.0)
    return score.where(s50.notna())  # not enough history -> unknown


def monthly_structure(m: pd.DataFrame) -> pd.Series:
    h, l = m["high"], m["low"]
    up = (h > h.shift(1)) & (l > l.shift(1))
    dn = (h < h.shift(1)) & (l < l.shift(1))
    out = pd.Series(np.where(up, 1.0, np.where(dn, -1.0, 0.0)), index=m.index)
    return out.where(h.shift(1).notna())


def classify(w: pd.Series, m: pd.Series, b: pd.Series) -> pd.Series:
    total = w.fillna(0.0) + 1.5 * m.fillna(0.0) + 0.5 * np.sign(b.fillna(0.0))
    reg = np.where(total >= 2.0, "Bull", np.where(total <= -2.0, "Bear", "Neutral"))
    reg = np.where(w.isna(), "Neutral", reg)
    return pd.Series(reg, index=w.index)


def _available(series: pd.Series, period: str, extra_lag: int, name: str) -> pd.DataFrame:
    """Turn a period-labelled series into (available_at, value): usable once the period closed."""
    s = series.shift(extra_lag) if extra_lag else series
    if period == "W":
        avail = s.index + pd.Timedelta(days=7)
    else:
        avail = s.index + pd.offsets.MonthBegin(1)
    return pd.DataFrame({"available_at": pd.DatetimeIndex(avail).as_unit("ns"), name: s.to_numpy()})


def compute_daily_regime(eth_daily: pd.DataFrame, btc_daily: pd.DataFrame, extra_lag: int = 1) -> pd.DataFrame:
    """Return columns: day, regime, eth_weekly_score, eth_monthly_struct, btc_weekly_score."""
    ew = _available(weekly_score(_resample(eth_daily, "W-MON")), "W", extra_lag, "eth_weekly_score")
    em = _available(monthly_structure(_resample(eth_daily, "MS")), "M", extra_lag, "eth_monthly_struct")
    bw = _available(weekly_score(_resample(btc_daily, "W-MON")), "W", extra_lag, "btc_weekly_score")

    out = pd.DataFrame({"day": eth_daily["day"], "close_time": (eth_daily["ts"] + pd.Timedelta(days=1)).dt.as_unit("ns")})
    for tbl in (ew, em, bw):
        out = pd.merge_asof(
            out.sort_values("close_time"),
            tbl.sort_values("available_at"),
            left_on="close_time",
            right_on="available_at",
            direction="backward",
        ).drop(columns="available_at")
    out["regime"] = classify(out["eth_weekly_score"], out["eth_monthly_struct"], out["btc_weekly_score"]).to_numpy()
    return out.drop(columns="close_time")
