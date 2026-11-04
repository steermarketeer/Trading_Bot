"""
What happened after each event.

Entry: next day's OPEN after the signal day's close (you can't trade the close you just saw).
Target: entry + target_atr x ATR14 (in the signal's direction). Stop: entry - stop_atr x ATR14.
ATR is the value at the signal day's close.
Walk forward day by day up to max_days (entry day included):
  * stop hit (low/high through it, or the open gapped past it)  -> loss, R = -stop_atr ... or the gap fill
  * target hit                                                  -> win,  R = +target_atr ... or the gap fill
  * both inside the same day: counted as a LOSS (can't know the order on daily bars)
  * neither by max_days: timeout, R = (close - entry) / ATR in the trade direction
R is measured in ATR units, so 1R = one ATR. Costs are not included here (see report notes).
mae_r / mfe_r = worst adverse / best favourable move while the trade was OPEN (up to the exit).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OutcomeParams:
    target_atr: float = 2.0
    stop_atr: float = 1.0
    max_days: int = 20


def label_outcomes(bars: pd.DataFrame, events: pd.DataFrame, atr_col: str = "atr14",
                   p: OutcomeParams = OutcomeParams()) -> pd.DataFrame:
    idx = {d: i for i, d in enumerate(bars["day"])}
    o = bars["open"].to_numpy(float)
    h = bars["high"].to_numpy(float)
    l = bars["low"].to_numpy(float)
    c = bars["close"].to_numpy(float)
    a = bars[atr_col].to_numpy(float)
    n = len(bars)
    rows = []
    for ev in events.itertuples(index=False):
        i = idx[ev.day]
        rec = {"outcome": None, "r": np.nan, "days_to_exit": np.nan, "entry": np.nan,
               "mfe_r": np.nan, "mae_r": np.nan}
        if i + p.max_days >= n or not np.isfinite(a[i]) or a[i] <= 0:
            rec["outcome"] = "incomplete"
            rows.append(rec)
            continue
        dr = int(ev.direction)
        entry = o[i + 1]
        unit = a[i]
        tgt = entry + dr * p.target_atr * unit
        stp = entry - dr * p.stop_atr * unit
        out, r, k_exit = "timeout", None, p.max_days
        mfe = mae = 0.0
        for k in range(1, p.max_days + 1):
            j = i + k
            fav = ((h[j] - entry) if dr > 0 else (entry - l[j])) / unit
            adv = ((entry - l[j]) if dr > 0 else (h[j] - entry)) / unit
            # gap at the open (not possible on the entry day: entry == open)
            if k > 1 and dr * (o[j] - stp) <= 0:
                out, r, k_exit = "loss", dr * (o[j] - entry) / unit, k
                mae = max(mae, -r)
                break
            if k > 1 and dr * (o[j] - tgt) >= 0:
                out, r, k_exit = "win", dr * (o[j] - entry) / unit, k
                mfe = max(mfe, r)
                break
            hit_stop = (l[j] <= stp) if dr > 0 else (h[j] >= stp)
            hit_tgt = (h[j] >= tgt) if dr > 0 else (l[j] <= tgt)
            if hit_stop:
                # exit at the stop: price beyond it after the exit doesn't count
                out, r, k_exit = "loss", -p.stop_atr, k
                mae = max(mae, p.stop_atr)
                mfe = max(mfe, min(fav, p.target_atr))
                break
            if hit_tgt:
                out, r, k_exit = "win", p.target_atr, k
                mfe = max(mfe, p.target_atr)
                mae = max(mae, adv)  # adv < stop here, else it would have been a loss
                break
            mfe, mae = max(mfe, fav), max(mae, adv)
        if r is None:
            r = dr * (c[i + p.max_days] - entry) / unit
        rec.update({"outcome": out, "r": float(r), "days_to_exit": k_exit, "entry": entry,
                    "mfe_r": mfe, "mae_r": mae})
        rows.append(rec)
    return pd.concat([events.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
