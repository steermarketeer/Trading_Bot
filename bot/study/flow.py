"""
Order-flow and volume-location indicators at the entry time (5m data strictly before entry).

  CVD (cumulative volume delta) from taker buy volume: delta = 2 x taker_buy - volume per 5m candle.
    n_cvd_trend    CVD change over the last 20 candles of the trade's timeframe / their volume, in the trade direction
    n_cvd_div      over those 20 candles: CVD moved our way while price did NOT (+1 = hidden pressure our way,
                   e.g. price made a lower low but CVD a higher low before a long); -1 = the opposite (fakeout risk)
  Volume profile over the last 30 days (2h/4h) or 120 days (1D), 60 price bins:
    n_vp_hvn_path  1 if a high-volume node (top 20% bins) lies between entry and the 2R target (obstacle)
    n_vp_lvn_share share of bins between entry and the 2R target that are low-volume nodes (bottom 30%) - room to run
    n_vp_poc_side  entry on our side of the point of control (long above POC / short below), in ATR
  VWAP:
    n_vwap_day     price vs today's VWAP (from 00:00 UTC), in ATR, in the trade direction
    n_vwap_week    price vs this week's VWAP (from Monday 00:00 UTC), in ATR, in the trade direction
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_flow(data_dir, symbol: str) -> pd.DataFrame:
    df = pd.read_csv(Path(data_dir) / "klines" / f"{symbol}_5m.csv",
                     usecols=["open_time", "high", "low", "close", "volume", "taker_buy_base"])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)
    df["delta"] = 2 * df["taker_buy_base"] - df["volume"]
    df["cvd"] = df["delta"].cumsum()
    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3
    return df


def flow_features(trades: pd.DataFrame, fl: pd.DataFrame) -> pd.DataFrame:
    """trades: entry_time (naive UTC), tf, direction, entry, risk, plus an ATR column 'atr_ref' (price units)."""
    t5 = fl["open_time"].to_numpy()
    H, Lo, C, V = (fl[x].to_numpy(float) for x in ("high", "low", "close", "volume"))
    CVD, TP = fl["cvd"].to_numpy(float), fl["tp"].to_numpy(float)
    rows = []
    for et, tf, d, e, rk, a in zip(trades["entry_time"], trades["tf"], trades["direction"], trades["entry"],
                                   trades["risk"], trades["atr_ref"]):
        end = int(np.searchsorted(t5, np.datetime64(pd.Timestamp(et)), side="left"))  # candles strictly before entry
        bpt = int(pd.Timedelta(tf) / pd.Timedelta(minutes=5))
        r = {}
        st = end - 20 * bpt
        if st > 0 and end > st:
            dv = V[st:end].sum()
            dc = CVD[end - 1] - CVD[st - 1]
            dp = C[end - 1] - C[st - 1]
            r["n_cvd_trend"] = d * dc / dv if dv > 0 else np.nan
            r["n_cvd_div"] = float(np.sign(d * dc) > 0 and np.sign(d * dp) <= 0) - float(np.sign(d * dc) < 0 and np.sign(d * dp) >= 0)
        days = 120 if tf == "1D" else 30
        vs = end - days * 288
        if vs > 0:
            lo, hi = Lo[vs:end].min(), H[vs:end].max()
            bins = np.linspace(lo, hi, 61)
            prof, _ = np.histogram(TP[vs:end], bins=bins, weights=V[vs:end])
            poc = (bins[np.argmax(prof)] + bins[np.argmax(prof) + 1]) / 2
            hvn, lvn = np.quantile(prof, 0.8), np.quantile(prof, 0.3)
            tgt = e + d * 2 * rk
            a_, b_ = sorted((e, tgt))
            centers = (bins[:-1] + bins[1:]) / 2
            inpath = (centers > a_) & (centers < b_)
            r["n_vp_hvn_path"] = float((prof[inpath] >= hvn).any()) if inpath.any() else 0.0
            r["n_vp_lvn_share"] = float((prof[inpath] <= lvn).mean()) if inpath.any() else 1.0
            r["n_vp_poc_side"] = d * (e - poc) / a if a > 0 else np.nan
        ts = pd.Timestamp(et)
        for name, anchor in (("n_vwap_day", ts.normalize()), ("n_vwap_week", (ts - pd.Timedelta(days=ts.dayofweek)).normalize())):
            s0 = int(np.searchsorted(t5, np.datetime64(anchor), side="left"))
            if end > s0:
                vw = (TP[s0:end] * V[s0:end]).sum() / V[s0:end].sum()
                r[name] = d * (C[end - 1] - vw) / a if a > 0 else np.nan
        rows.append(r)
    return pd.DataFrame(rows, index=trades.index)
