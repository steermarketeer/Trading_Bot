"""
Extra hints (indicators the first analysis did not use), read at each trade's entry time from
candles that had already closed. Convention as in mtf.py: -1 = warns against the trade,
+1 = supports it, 0 = neutral.

Per timeframe (15m ... 1W):
  adx_weak     ADX(14) < 20: no trend                                   (direction-free: -1 or 0)
  di           -DI > +DI is against a long (+DI > -DI against a short)
  stoch_ext    slow %K(14,3) > 80 against a long, < 20 against a short
  cci_ext      CCI(20) > +100 against a long, < -100 against a short
  willr_ext    Williams %R(14) > -20 against a long, < -80 against a short
  mfi_ext      MFI(14) > 80 against a long, < 20 against a short
  obv          OBV below its EMA20 is against a long (above: against a short)
  cmf          Chaikin Money Flow(20) < 0 against a long, > 0 against a short
  vwap         close below rolling VWAP(20) against a long, above against a short
  supertrend   Supertrend(10,3) pointing the other way
  psar         Parabolic SAR on the wrong side of price
  keltner_ext  close outside the Keltner channel(20, 2xATR10) in the trade direction (over-extended)
  donch_room   less than 1 ATR left to the 20-candle high (long) / low (short)
  vol_expand   ATR(14) > 1.5 x ATR(50): volatility expanding           (direction-free)
  climax       volume > 3x its 20-candle average on a candle against the trade
  candle       last candle is a bearish engulfing / shooting star (vs long) or bullish engulfing / hammer (vs short)
  roc_against  10-candle rate of change against the trade

Context (one value per trade):
  ctx_funding     3 latest funding rates average >= 0.03% (crowded longs, vs long) or < 0 (crowded shorts, vs short)
  ctx_btc_daily   BTC daily close vs its EMA50 against the trade
  ctx_btc_weekly  BTC weekly trend (same rule as ETH's) against the trade
  ctx_ethbtc      ETH/BTC daily ratio vs its EMA50 against the trade
  ctx_room_1d     a confirmed daily swing high (long) / low (short) from the last 120 days between entry and the +2 ATR target
  ctx_room_1w     same with weekly swings from the last 2 years
  ctx_sma200_ext  close > 1.4x SMA200 (vs long) or < 0.7x SMA200 (vs short): far stretched
  ctx_weekend     entry on Saturday or Sunday UTC                           (direction-free)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import (adx, atr, cci, cmf, donchian, ema, keltner, mfi, obv, psar,
                         rolling_vwap, stochastic, supertrend, williams_r)
from .mtf import TIMEFRAMES, resample
from .patterns import swing_points
from .trend import add_weekly_trend

TF_HINTS2 = ["adx_weak", "di", "stoch_ext", "cci_ext", "willr_ext", "mfi_ext", "obv", "cmf", "vwap",
             "supertrend", "psar", "keltner_ext", "donch_room", "vol_expand", "climax", "candle", "roc_against"]
DIRECTION_FREE = {"adx_weak", "vol_expand"}
CTX_HINTS = ["ctx_funding", "ctx_btc_daily", "ctx_btc_weekly", "ctx_ethbtc", "ctx_room_1d",
             "ctx_room_1w", "ctx_sma200_ext", "ctx_weekend"]


def tf_states2(b: pd.DataFrame) -> pd.DataFrame:
    """Direction-free raw states per candle: +1 bullish / -1 bearish (or -1 = flag for direction-free)."""
    c, o, h, l, v = b["close"], b["open"], b["high"], b["low"], b["volume"]
    out = pd.DataFrame({"close_time": b["close_time"]})
    ad, pdi, mdi = adx(b)
    out["adx_weak"] = np.where(ad < 20, -1, 0)
    out["di"] = np.where(pdi > mdi, 1, np.where(mdi > pdi, -1, 0))
    k = stochastic(b)
    out["stoch_ext"] = np.where(k > 80, -1, np.where(k < 20, 1, 0))
    cc = cci(b)
    out["cci_ext"] = np.where(cc > 100, -1, np.where(cc < -100, 1, 0))
    wr = williams_r(b)
    out["willr_ext"] = np.where(wr > -20, -1, np.where(wr < -80, 1, 0))
    m = mfi(b)
    out["mfi_ext"] = np.where(m > 80, -1, np.where(m < 20, 1, 0))
    ob = obv(b)
    ob_e = ema(ob, 20)
    out["obv"] = np.where(ob > ob_e, 1, np.where(ob < ob_e, -1, 0))
    cm = cmf(b)
    out["cmf"] = np.where(cm > 0, 1, np.where(cm < 0, -1, 0))
    vw = rolling_vwap(b)
    out["vwap"] = np.where(c > vw, 1, np.where(c < vw, -1, 0))
    out["supertrend"] = supertrend(b).fillna(0).astype(int)
    sar = psar(b)
    out["psar"] = np.where(sar < c, 1, np.where(sar > c, -1, 0))
    _, ku, kl = keltner(b)
    out["keltner_ext"] = np.where(c > ku, -1, np.where(c < kl, 1, 0))
    dh, dl = donchian(b)
    a14 = atr(b, 14)
    # little room up = bearish for a long; little room down = bullish hint relative to shorts
    room_up = (dh - c) / a14
    room_dn = (c - dl) / a14
    out["donch_room_up"] = (room_up < 1).astype(int)   # used for longs
    out["donch_room_dn"] = (room_dn < 1).astype(int)   # used for shorts
    a50 = atr(b, 50)
    out["vol_expand"] = np.where(a14 > 1.5 * a50, -1, 0)
    vavg = v.shift(1).rolling(20, min_periods=20).mean()
    big = v > 3 * vavg
    out["climax"] = np.where(big & (c < o), -1, np.where(big & (c > o), 1, 0))
    body = (c - o).abs()
    up_w = h - np.maximum(c, o)
    lo_w = np.minimum(c, o) - l
    po, pc = o.shift(1), c.shift(1)
    bear_engulf = (pc > po) & (c < o) & (o >= pc) & (c <= po)
    bull_engulf = (pc < po) & (c > o) & (o <= pc) & (c >= po)
    star = (up_w >= 2 * body) & (lo_w <= 0.3 * body) & (body > 0)
    hammer = (lo_w >= 2 * body) & (up_w <= 0.3 * body) & (body > 0)
    out["candle"] = np.where(bear_engulf | star, -1, np.where(bull_engulf | hammer, 1, 0))
    roc = c / c.shift(10) - 1
    out["roc_against"] = np.where(roc > 0, 1, np.where(roc < 0, -1, 0))
    return out


def tf_hints2(df5: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """Columns <tf>_<hint> for TF_HINTS2, relative to each trade's direction."""
    t = trades[["entry_time", "direction"]].copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True).dt.as_unit("ns")
    t["_row"] = np.arange(len(t))
    t = t.sort_values("entry_time")
    cols = {}
    for tf, rule in TIMEFRAMES.items():
        st = tf_states2(resample(df5, rule))
        m = pd.merge_asof(t, st, left_on="entry_time", right_on="close_time", direction="backward")
        d = m["direction"].to_numpy()
        for hnt in TF_HINTS2:
            if hnt == "donch_room":
                flag = np.where(d > 0, m["donch_room_up"].fillna(0), m["donch_room_dn"].fillna(0))
                vals = -flag.astype(int)
            elif hnt in DIRECTION_FREE:
                vals = m[hnt].fillna(0).to_numpy().astype(int)
            else:
                vals = (m[hnt].fillna(0).to_numpy() * d).astype(int)
            cols[f"{tf}_{hnt}"] = pd.Series(vals, index=m["_row"].to_numpy())
    out = pd.DataFrame(cols).sort_index()
    out.index = trades.index
    return out


def _asof(times: pd.Series, table: pd.DataFrame, time_col: str, value_cols: list[str]) -> pd.DataFrame:
    left = pd.DataFrame({"t": pd.to_datetime(times, utc=True).dt.as_unit("ns"), "_row": np.arange(len(times))})
    right = table[[time_col, *value_cols]].copy()
    right[time_col] = pd.to_datetime(right[time_col], utc=True).dt.as_unit("ns")
    m = pd.merge_asof(left.sort_values("t"), right.sort_values(time_col), left_on="t", right_on=time_col,
                      direction="backward")
    return m.sort_values("_row").reset_index(drop=True)


def context_hints(trades: pd.DataFrame, eth5: pd.DataFrame, btc5: pd.DataFrame,
                  funding: pd.DataFrame, target_atr: float = 2.0) -> pd.DataFrame:
    """trades needs: entry_time, direction, entry, atr14. All inputs must be known at entry_time."""
    et = pd.to_datetime(trades["entry_time"], utc=True)
    d = trades["direction"].to_numpy()
    out = pd.DataFrame(index=trades.index)

    # funding: average of the 3 latest settlements at or before entry
    f = funding.sort_values("time").copy()
    f["avg3"] = f["rate"].rolling(3, min_periods=3).mean()
    fa = _asof(et, f, "time", ["avg3"])["avg3"].to_numpy()
    fl = np.where(np.isnan(fa), 0, np.where((d > 0) & (fa >= 0.0003), -1, np.where((d < 0) & (fa < 0), -1, 0)))
    out["ctx_funding"] = fl

    # BTC daily trend and weekly trend
    bd = resample(btc5, "1D")
    bd["e50"] = ema(bd["close"], 50)
    bd["side"] = np.sign(bd["close"] - bd["e50"]).where(bd["e50"].notna(), 0)
    bs = _asof(et, bd, "close_time", ["side"])["side"].fillna(0).to_numpy()
    out["ctx_btc_daily"] = np.where(bs * d < 0, -1, np.where(bs * d > 0, 1, 0))
    bdd = bd.rename(columns={"open_time": "ts"})
    bdd["day"] = bdd["ts"].dt.strftime("%Y-%m-%d")
    btr = add_weekly_trend(bdd)
    btr["wside"] = btr["weekly_trend"].map({"Up": 1, "Down": -1}).fillna(0)
    ws = _asof(et, btr, "close_time", ["wside"])["wside"].fillna(0).to_numpy()
    out["ctx_btc_weekly"] = np.where(ws * d < 0, -1, np.where(ws * d > 0, 1, 0))

    # ETH/BTC ratio
    ed = resample(eth5, "1D")
    r = ed[["close_time", "close"]].merge(bd[["close_time", "close"]], on="close_time", suffixes=("_e", "_b"))
    r["ratio"] = r["close_e"] / r["close_b"]
    r["e50"] = ema(r["ratio"], 50)
    r["side"] = np.sign(r["ratio"] - r["e50"]).where(r["e50"].notna(), 0)
    rs = _asof(et, r, "close_time", ["side"])["side"].fillna(0).to_numpy()
    out["ctx_ethbtc"] = np.where(rs * d < 0, -1, np.where(rs * d > 0, 1, 0))

    # room to the target: a confirmed swing level between entry and target
    entry = trades["entry"].to_numpy(float)
    a = trades["atr14"].to_numpy(float)
    tgt = entry + d * target_atr * a
    for label, rule, k, lookback in (("1d", "1D", 5, pd.Timedelta(days=120)),
                                     ("1w", "W-MON", 3, pd.Timedelta(weeks=104))):
        b = resample(eth5, rule)
        sh, sl = swing_points(b["high"].to_numpy(float), b["low"].to_numpy(float), k)
        ct = b["close_time"].to_numpy()
        ot = b["open_time"].dt.as_unit("ns").to_numpy()
        lb = np.timedelta64(int(lookback.value), "ns")

        def arr(sw):
            if not sw:
                return np.array([], dtype=ct.dtype), np.array([], dtype=ot.dtype), np.array([])
            return (np.array([ct[cf] for _, _, cf in sw]), np.array([ot[i] for i, _, _ in sw]),
                    np.array([p for _, p, _ in sw]))
        hi_known, hi_at, hi_p = arr(sh)
        lo_known, lo_at, lo_p = arr(sl)
        flags = np.zeros(len(trades), dtype=int)
        for i, t in enumerate(et.dt.as_unit("ns").to_numpy()):
            # a swing counts once confirmed (its K-th following candle closed) and if recent
            if d[i] > 0 and len(hi_p):
                lv = hi_p[(hi_known <= t) & (hi_at >= t - lb)]
                flags[i] = -1 if ((lv > entry[i]) & (lv < tgt[i])).any() else 0
            elif d[i] < 0 and len(lo_p):
                lv = lo_p[(lo_known <= t) & (lo_at >= t - lb)]
                flags[i] = -1 if ((lv < entry[i]) & (lv > tgt[i])).any() else 0
        out[f"ctx_room_{label}"] = flags

    # stretched vs SMA200 (daily)
    ed["s200"] = ed["close"].rolling(200, min_periods=200).mean()
    ed["ratio200"] = ed["close"] / ed["s200"]
    r2 = _asof(et, ed, "close_time", ["ratio200"])["ratio200"].to_numpy()
    out["ctx_sma200_ext"] = np.where(np.isnan(r2), 0,
                                     np.where((d > 0) & (r2 > 1.4), -1, np.where((d < 0) & (r2 < 0.7), -1, 0)))

    out["ctx_weekend"] = np.where(et.dt.dayofweek.to_numpy() >= 5, -1, 0)
    return out


def load_funding_table(data_dir, symbol: str) -> pd.DataFrame:
    from pathlib import Path
    f = pd.read_csv(Path(data_dir) / "funding" / f"{symbol}.csv")
    return pd.DataFrame({"time": pd.to_datetime(f["fundingTime"], unit="ms", utc=True),
                         "rate": f["fundingRate"].astype(float)})
