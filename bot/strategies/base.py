"""
Strategy interface. To write your own strategy:

1. Create bot/strategies/my_idea.py with a class that subclasses Strategy
   and decorate it with @register("my_idea").
2. Import it in bot/strategies/__init__.py.
3. Create strategies/my_idea.yaml with `type: my_idea` and your params.

Rules the engine guarantees, so you don't have to:
  * entry_signal / exit_signal are called at a day's CLOSE with that day's row.
    Orders fill at the NEXT day's open (plus slippage). No lookahead possible
    as long as prepare() only uses rolling/backward-looking calculations.
  * Stops, leverage, liquidation, fees, funding, cooldown and drawdown halts
    are handled by the engine from the `risk:` block of the YAML.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class PositionView:
    side: str               # "long" | "short"
    entry_day: str
    entry_price: float
    days_held: int
    unrealized_pct: float   # price move in the position's favour since entry (not levered)


class Strategy:
    #: default params; YAML `params:` overrides these. Unknown keys are rejected.
    defaults: dict[str, Any] = {}

    def __init__(self, name: str, params: dict[str, Any] | None = None):
        params = params or {}
        unknown = set(params) - set(self.defaults)
        if unknown:
            raise ValueError(f"{name}: unknown params {sorted(unknown)}; allowed: {sorted(self.defaults)}")
        self.name = name
        self.p = {**self.defaults, **params}

    # --- override these -------------------------------------------------
    def prepare(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Add indicator columns. Must only look backward (rolling, shift(+n))."""
        return bars

    def required_columns(self) -> list[str]:
        """Rows where any of these is NaN are skipped (indicator warm-up)."""
        return []

    def entry_signal(self, row: dict) -> str | None:
        """Return 'long', 'short' or None. Called only when flat."""
        raise NotImplementedError

    def exit_signal(self, row: dict, pos: PositionView) -> str | None:
        """Return an exit reason string to close at the next open, or None to hold."""
        raise NotImplementedError

    def explain(self, row: dict) -> dict[str, Any]:
        """Optional: gate-by-gate checklist for the dashboard / logs."""
        return {}


_REGISTRY: dict[str, type[Strategy]] = {}


def register(type_name: str):
    def deco(cls):
        _REGISTRY[type_name] = cls
        return cls
    return deco


def make_strategy(type_name: str, name: str, params: dict | None) -> Strategy:
    if type_name not in _REGISTRY:
        raise ValueError(f"unknown strategy type '{type_name}'. Known: {sorted(_REGISTRY)}")
    return _REGISTRY[type_name](name, params)
