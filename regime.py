"""
Rule-based master regime gate (Bull / Bear / Neutral).

Per claude_code_brief_v2.md §3:
  - Weekly close vs weekly 20/50 SMA
  - Weekly Ichimoku cloud position
  - Monthly HH/HL vs LH/LL structure
  - BTC weekly regime as a modifier
  Bull -> longs only | Bear -> shorts only | Neutral -> no trades

No lookahead: higher-TF features are shifted by 1 period before
being mapped onto 5m bars (only completed weeks/months).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("data")


def _load_5m(symbol: str) -> pd.DataFrame:
    path = DATA_DIR / "klines" / f"{symbol}_5m.csv"
    df = pd.read_csv(path)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df


def _ohlc_resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    x = df.set_index("open_time")
    out = x.resample(rule, label="right", closed="right").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["close"])
    return out


def _ichimoku_cloud_side(weekly: pd.DataFrame) -> pd.Series:
    """+1 above cloud, -1 below, 0 inside. Uses completed bars only (caller shifts)."""
    high, low, close = weekly["high"], weekly["low"], weekly["close"]
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (high.rolling(52).max() + low.rolling(52).min()) / 2
    cloud_top = pd.concat([span_a, span_b], axis=1).max(axis=1)
    cloud_bot = pd.concat([span_a, span_b], axis=1).min(axis=1)
    side = pd.Series(0, index=weekly.index, dtype=int)
    side = side.mask(close > cloud_top, 1)
    side = side.mask(close < cloud_bot, -1)
    return side


def _weekly_score(weekly: pd.DataFrame) -> pd.Series:
    close = weekly["close"]
    sma20 = close.rolling(20, min_periods=20).mean()
    sma50 = close.rolling(50, min_periods=50).mean()
    score = pd.Series(0.0, index=weekly.index)
    score += np.where(close > sma20, 1.0, -1.0)
    score += np.where(close > sma50, 1.0, -1.0)
    score += np.where(sma20 > sma50, 1.0, -1.0)
    score += _ichimoku_cloud_side(weekly).astype(float)
    return score  # roughly -4 .. +4


def _monthly_structure(monthly: pd.DataFrame) -> pd.Series:
    """+1 HH/HL (bullish structure), -1 LH/LL (bearish), 0 mixed/unknown."""
    high = monthly["high"]
    low = monthly["low"]
    # compare last completed swing pair: current vs previous month extremes
    hh = high > high.shift(1)
    hl = low > low.shift(1)
    lh = high < high.shift(1)
    ll = low < low.shift(1)
    out = pd.Series(0, index=monthly.index, dtype=int)
    out = out.mask(hh & hl, 1)
    out = out.mask(lh & ll, -1)
    return out


def _classify(eth_w_score: float, eth_m_struct: float, btc_w_score: float) -> str:
    # BTC modifier: soft nudge
    total = eth_w_score + 1.5 * eth_m_struct + 0.5 * np.sign(btc_w_score)
    if total >= 2.0:
        return "Bull"
    if total <= -2.0:
        return "Bear"
    return "Neutral"


def compute_regime_5m(eth_5m: pd.DataFrame | None = None, btc_5m: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Returns DataFrame with columns: open_time, regime (Bull/Bear/Neutral),
    eth_weekly_score, eth_monthly_struct, btc_weekly_score.
    """
    eth = eth_5m if eth_5m is not None else _load_5m("ETHUSDT")
    btc = btc_5m if btc_5m is not None else _load_5m("BTCUSDT")

    eth_w = _ohlc_resample(eth, "W-SUN")
    eth_m = _ohlc_resample(eth, "ME")
    btc_w = _ohlc_resample(btc, "W-SUN")

    eth_w_score = _weekly_score(eth_w).shift(1)  # completed week only
    eth_m_struct = _monthly_structure(eth_m).shift(1).astype(float)
    btc_w_score = _weekly_score(btc_w).shift(1)

    # Map onto 5m via merge_asof (backward = last known completed HTF value)
    base = eth[["open_time"]].copy()
    w = eth_w_score.rename("eth_weekly_score").reset_index().rename(columns={"open_time": "open_time"})
    # resample index name
    w = eth_w_score.reset_index()
    w.columns = ["open_time", "eth_weekly_score"]
    m = eth_m_struct.reset_index()
    m.columns = ["open_time", "eth_monthly_struct"]
    bw = btc_w_score.reset_index()
    bw.columns = ["open_time", "btc_weekly_score"]

    out = base.sort_values("open_time")
    out = pd.merge_asof(out, w.sort_values("open_time"), on="open_time", direction="backward")
    out = pd.merge_asof(out, m.sort_values("open_time"), on="open_time", direction="backward")
    out = pd.merge_asof(out, bw.sort_values("open_time"), on="open_time", direction="backward")

    out["eth_weekly_score"] = out["eth_weekly_score"].fillna(0.0)
    out["eth_monthly_struct"] = out["eth_monthly_struct"].fillna(0.0)
    out["btc_weekly_score"] = out["btc_weekly_score"].fillna(0.0)

    out["regime"] = [
        _classify(ws, ms, bs)
        for ws, ms, bs in zip(
            out["eth_weekly_score"], out["eth_monthly_struct"], out["btc_weekly_score"]
        )
    ]
    return out


def allowed_side(regime: str) -> str | None:
    """Return 'long', 'short', or None (flat)."""
    if regime == "Bull":
        return "long"
    if regime == "Bear":
        return "short"
    return None


if __name__ == "__main__":
    r = compute_regime_5m()
    print(r["regime"].value_counts())
    print(r.tail(3))
