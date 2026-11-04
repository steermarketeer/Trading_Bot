"""
Daily trend follower under the weekly/monthly regime gate (legacy S1/S2/S3 family).

Entry (when flat, at daily close -> fill next open):
  long : regime Bull, stable >= regime_stable_days, close > SMA(entry_sma),
         [align] SMA(align_sma) > SMA(entry_sma), [btc_confirm] BTC close > BTC SMA(btc_sma),
         ATR% within [atr_pct_min, atr_pct_max]
  short: mirror image with Bear
Exit:
  regime no longer matches the side, or close crosses SMA(exit_sma) against the side.
"""
from __future__ import annotations

import math

import pandas as pd

from ..data import atr, run_length, sma
from .base import PositionView, Strategy, register


def _ok(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


@register("htf_trend")
class HtfTrend(Strategy):
    defaults = {
        "sides": "both",            # both | long_only | short_only
        "entry_sma": 50,
        "exit_sma": 30,
        "align_sma": 20,            # null disables the alignment check
        "regime_stable_days": 5,
        "atr_period": 14,
        "atr_pct_min": 0.01,        # null disables
        "atr_pct_max": 0.08,        # null disables
        "btc_confirm": False,
        "btc_sma": 50,
    }

    def prepare(self, bars: pd.DataFrame) -> pd.DataFrame:
        d = bars.copy()
        p = self.p
        for n in {p["entry_sma"], p["exit_sma"], p["align_sma"]} - {None}:
            d[f"sma{n}"] = sma(d["close"], int(n))
        d["atr_pct"] = atr(d, int(p["atr_period"])) / d["close"]
        d["regime_stable_days"] = run_length(d["regime"])
        if p["btc_confirm"]:
            d[f"btc_sma{p['btc_sma']}"] = sma(d["btc_close"], int(p["btc_sma"]))
        return d

    def required_columns(self) -> list[str]:
        p = self.p
        cols = [f"sma{p['entry_sma']}", f"sma{p['exit_sma']}", "atr_pct"]
        if p["align_sma"]:
            cols.append(f"sma{p['align_sma']}")
        if p["btc_confirm"]:
            cols += ["btc_close", f"btc_sma{p['btc_sma']}"]
        return cols

    # ------------------------------------------------------------------
    def explain(self, row: dict) -> dict:
        p = self.p
        reg = row["regime"]
        side = "long" if reg == "Bull" else "short" if reg == "Bear" else None
        sgn = 1 if side == "long" else -1
        c, se = row["close"], row[f"sma{p['entry_sma']}"]
        checks = {
            "regime": reg,
            "side_allowed": side is not None
            and (p["sides"] == "both" or p["sides"] == f"{side}_only"),
            "regime_stable": row["regime_stable_days"] >= p["regime_stable_days"],
            "price_vs_entry_sma": side is not None and sgn * (c - se) > 0,
        }
        if p["align_sma"]:
            checks["sma_aligned"] = side is not None and sgn * (row[f"sma{p['align_sma']}"] - se) > 0
        if _ok(p["atr_pct_min"]):
            checks["atr_not_too_low"] = row["atr_pct"] >= p["atr_pct_min"]
        if _ok(p["atr_pct_max"]):
            checks["atr_not_too_high"] = row["atr_pct"] <= p["atr_pct_max"]
        if p["btc_confirm"]:
            checks["btc_confirms"] = side is not None and sgn * (row["btc_close"] - row[f"btc_sma{p['btc_sma']}"]) > 0
        checks["entry_side"] = side if all(v for k, v in checks.items() if k not in ("regime",)) else None
        return checks

    def entry_signal(self, row: dict) -> str | None:
        return self.explain(row)["entry_side"]

    def exit_signal(self, row: dict, pos: PositionView) -> str | None:
        want = "Bull" if pos.side == "long" else "Bear"
        if row["regime"] != want:
            return f"regime_{row['regime'].lower()}"
        se = row[f"sma{self.p['exit_sma']}"]
        if pos.side == "long" and row["close"] < se:
            return f"close_below_sma{self.p['exit_sma']}"
        if pos.side == "short" and row["close"] > se:
            return f"close_above_sma{self.p['exit_sma']}"
        return None
