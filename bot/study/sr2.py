"""
Support/resistance study v2: bounce-candle confirmation, retests, breakouts, multi-target win rates,
and a walk-forward machine-learning filter over ~300 indicator features.

Events per timeframe (1h, 4h, 1D), from strong zones known before each candle opened (levels.py):
  touch      candle j reaches a zone from one side (see sr_study.find logic)
  REVERSAL-NOW     held at j's close -> enter j+1 open (as in v1)
  REVERSAL-BOUNCE  held at j's close AND bounce candle j+1 closes in the reversal direction
                   (up candle, close above j's close for support) -> decide at j+1 close, enter j+2 open
  BREAKOUT         j closed THROUGH the zone -> enter j+1 open in the break direction

Stops: reversal = beyond the zone and the touch/bounce wicks + 0.25 ATR;
       breakout = back inside, 0.5 ATR on the other side of the level.
Targets: 1R, 1.5R, 2R (R = entry-to-stop distance). Max 60 candles. Same-candle stop+target = loss.
Break-even win rate: 50% at 1R, 40% at 1.5R, 33% at 2R.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .indicators import adx, atr, bollinger, ema, macd, rsi
from .levels import _level_table, strong_levels
from .mtf import hints_at
from .mtf2 import tf_hints2
from .patterns import swing_points

BAND_ATR = 0.25
PAD_ATR = 0.25
BREAK_PAD_ATR = 0.5
RRS = (1.0, 1.5, 2.0)
MAX_BARS = 60
COOLDOWN = 6
TOUCH_MEMORY = 120  # candles: earlier touches of the same zone within this window count as retests


def label_multi(o, h, l, c, i, d, stop, max_bars=MAX_BARS):
    """Enter at o[i]. Returns {rr: (outcome, r)} for each RR plus entry and risk."""
    n = len(o)
    e = o[i]
    risk = (e - stop) * d
    if risk <= 0:
        return None
    out = {}
    last = min(n - 1, i + max_bars - 1)
    complete_window = (last - i + 1) == max_bars
    for rr in RRS:
        tgt = e + d * rr * risk
        res = None
        for k in range(i, last + 1):
            if k > i and d * (o[k] - stop) <= 0:
                res = ("loss", d * (o[k] - e) / risk)
                break
            if k > i and d * (o[k] - tgt) >= 0:
                res = ("win", d * (o[k] - e) / risk)
                break
            hit_s = (l[k] <= stop) if d > 0 else (h[k] >= stop)
            hit_t = (h[k] >= tgt) if d > 0 else (l[k] <= tgt)
            if hit_s:
                res = ("loss", -1.0)
                break
            if hit_t:
                res = ("win", rr)
                break
        if res is None:
            res = ("timeout", d * (c[last] - e) / risk) if complete_window else ("incomplete", math.nan)
        out[rr] = res
    return {"entry": e, "risk": risk, **{f"out_{rr:g}": v[0] for rr, v in out.items()},
            **{f"r_{rr:g}": v[1] for rr, v in out.items()}}


def _structure(sh, sl, t):
    hs = [p for i, p, cf in sh if cf <= t][-2:]
    ls = [p for i, p, cf in sl if cf <= t][-2:]
    if len(hs) < 2 or len(ls) < 2:
        return 0
    if hs[1] > hs[0] and ls[1] > ls[0]:
        return 1
    if hs[1] < hs[0] and ls[1] < ls[0]:
        return -1
    return 0


def build_events(df5: pd.DataFrame, rule: str, resample_fn) -> pd.DataFrame:
    b = resample_fn(df5, rule).reset_index(drop=True)
    table = _level_table(df5)
    a = atr(b, 14)
    r = rsi(b["close"])
    line, sig = macd(b["close"])
    hist = line - sig
    e20, e50, e200 = ema(b["close"], 20), ema(b["close"], 50), ema(b["close"], 200)
    ad, pdi, mdi = adx(b)
    mid, bu, bl = bollinger(b["close"])
    vol = b["volume"]
    vavg20 = vol.shift(1).rolling(20, min_periods=20).mean()
    v5 = vol.rolling(5, min_periods=5).mean()
    sh, sl = swing_points(b["high"].to_numpy(float), b["low"].to_numpy(float), 5)
    o, h, l, c = (b[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ot = pd.to_datetime(b["open_time"], utc=True)
    ct = pd.to_datetime(b["close_time"], utc=True)
    A, R, H, E20, E50, E200 = (x.to_numpy(float) for x in (a, r, hist, e20, e50, e200))
    AD, PD, MD, BU, BL, V, VA, V5 = (x.to_numpy(float) for x in (ad, pdi, mdi, bu, bl, vol, vavg20, v5))

    touches: dict = {}   # zone key -> list of touch candle indexes
    last_ev: dict = {}
    key_cache, zones = None, np.array([])
    rows = []
    for j in range(210, len(b) - 2):
        aj = A[j]
        if not np.isfinite(aj) or aj <= 0 or not np.isfinite(VA[j]) or VA[j] <= 0:
            continue
        t_open = ot.iloc[j]
        key = (int((table["known"] <= t_open).sum()), t_open.normalize())
        if key != key_cache:
            zones = strong_levels(table, t_open)
            key_cache = key
        if len(zones) == 0:
            continue
        band = BAND_ATR * aj
        pc = c[j - 1]
        for kind, cand in (("support", zones[(zones < pc) & (l[j] <= zones + band)]),
                           ("resistance", zones[(zones > pc) & (h[j] >= zones - band)])):
            if len(cand) == 0:
                continue
            L = cand.max() if kind == "support" else cand.min()
            zkey = (kind, round(L, 2))
            if j - last_ev.get(zkey, -10**9) < COOLDOWN:
                continue
            last_ev[zkey] = j
            # earlier touches of a zone within 1% (either side's role), inside the memory window
            prior = [jj for (k2, lv2), lst in touches.items() if abs(lv2 - L) / L < 0.01
                     for jj in lst if 0 < j - jj <= TOUCH_MEMORY]
            touches.setdefault(zkey, []).append(j)
            d = 1 if kind == "support" else -1
            held = (c[j] > L) if d > 0 else (c[j] < L)
            rng = h[j] - l[j]
            wick = ((min(o[j], c[j]) - l[j]) if d > 0 else (h[j] - max(o[j], c[j]))) / rng if rng > 0 else 0.0
            win = slice(j - 20, j)
            new_ext = (l[j] <= l[win].min()) if d > 0 else (h[j] >= h[win].max())
            pi = (j - 20 + int(np.argmin(l[win]))) if d > 0 else (j - 20 + int(np.argmax(h[win])))
            base = {
                "j": j, "time": ct.iloc[j], "day": ct.iloc[j].strftime("%Y-%m-%d"), "kind": kind, "zone_dir": d,
                "level": L, "atr": aj, "atr_pct": aj / c[j], "held": bool(held), "touch_n": len(prior) + 1,
                "bars_since_touch": (j - max(prior)) if prior else 999,
                "f_vol_touch": V[j] / VA[j], "f_vol_approach": V5[j - 1] / V5[j - 6] if V5[j - 6] > 0 else np.nan,
                "f_vol_slope": np.polyfit(np.arange(10), V[j - 9:j + 1], 1)[0] / VA[j],
                "f_vol_div": float(new_ext and V[j] < V[pi]),
                "f_rsi_div": float(new_ext and ((R[j] > R[pi]) if d > 0 else (R[j] < R[pi]))),
                "f_wick": wick, "f_body": abs(c[j] - o[j]) / aj, "f_range": rng / aj,
                "f_pierce": d * (L - (l[j] if d > 0 else h[j])) / aj,
                "f_rsi": R[j], "f_adx": AD[j], "f_di": (PD[j] - MD[j]) * d,
                "f_bb_pos": (c[j] - BL[j]) / (BU[j] - BL[j]) if BU[j] > BL[j] else np.nan,
                "f_d_e20": (c[j] - E20[j]) / aj * d, "f_d_e50": (c[j] - E50[j]) / aj * d,
                "f_d_e200": (c[j] - E200[j]) / aj * d, "f_macd": H[j] / aj * d,
                "f_macd_turn": float(d * (H[j] - H[j - 1]) > 0),
                "f_speed": d * (c[j - 5] - (l[j] if d > 0 else h[j])) / aj,
                "f_ret_20": (c[j] / c[j - 20] - 1) * d, "f_structure": _structure(sh, sl, j) * d,
                "f_hour": ot.iloc[j].hour, "f_dow": ot.iloc[j].dayofweek,
            }
            # --- REVERSAL-NOW: enter j+1 open
            if held:
                stop = (min(l[j], L) - PAD_ATR * aj) if d > 0 else (max(h[j], L) + PAD_ATR * aj)
                lab = label_multi(o, h, l, c, j + 1, d, stop)
                if lab:
                    rows.append({**base, "event": "reversal_now", "direction": d, "decision_time": ct.iloc[j], **lab})
                # --- REVERSAL-BOUNCE: confirmation candle j+1
                k = j + 1
                bounce = d * (c[k] - o[k]) > 0 and d * (c[k] - c[j]) > 0 and ((c[k] > L) if d > 0 else (c[k] < L))
                if bounce and k + 1 < len(b):
                    stop_b = (min(l[j], l[k], L) - PAD_ATR * aj) if d > 0 else (max(h[j], h[k], L) + PAD_ATR * aj)
                    lab = label_multi(o, h, l, c, k + 1, d, stop_b)
                    if lab:
                        rows.append({**base, "event": "reversal_bounce", "direction": d, "decision_time": ct.iloc[k],
                                     "f_bvol": V[k] / VA[j], "f_bvol_vs_touch": V[k] / V[j] if V[j] > 0 else np.nan,
                                     "f_bbody": abs(c[k] - o[k]) / aj, "f_bclose_pos": (
                                         (c[k] - l[k]) / (h[k] - l[k]) if d > 0 else (h[k] - c[k]) / (h[k] - l[k]))
                                     if h[k] > l[k] else np.nan, **lab})
            else:
                # --- BREAKOUT: closed through the level, trade in the break direction
                db = -d
                stop = L - db * BREAK_PAD_ATR * aj
                lab = label_multi(o, h, l, c, j + 1, db, stop)
                if lab:
                    fb = c[j + 1:j + 7]
                    failed = bool(((fb > L) if d > 0 else (fb < L)).any())  # back on the old side within 6 candles
                    rows.append({**base, "event": "breakout", "direction": db, "decision_time": ct.iloc[j],
                                 "false_break_6": failed, **lab})
    return pd.DataFrame(rows)


def add_mtf_features(ev: pd.DataFrame, df5: pd.DataFrame) -> pd.DataFrame:
    """~260 multi-timeframe hint states at the decision time, relative to the trade direction."""
    t = pd.DataFrame({"entry_time": ev["decision_time"], "direction": ev["direction"]}, index=ev.index)
    h1 = hints_at(df5, t)
    h1 = h1.drop(columns=["entry_time", "direction"])
    h2 = tf_hints2(df5, t)
    feats = pd.concat([h1, h2], axis=1)
    feats.columns = [f"m_{c}" for c in feats.columns]
    return pd.concat([ev, feats], axis=1)
