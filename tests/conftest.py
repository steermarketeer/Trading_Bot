import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.strategies.base import Strategy, register  # noqa: E402


@register("scripted")
class Scripted(Strategy):
    """Test strategy: enters/exits on given days."""
    defaults = {"entries": {}, "exits": {}}

    def entry_signal(self, row):
        return self.p["entries"].get(row["day"])

    def exit_signal(self, row, pos):
        return self.p["exits"].get(row["day"])


def make_bars(prices, start="2024-01-01", funding=None, **overrides):
    """Daily bars where open == previous close unless overridden: {day_index: {"open":..}}."""
    days = pd.date_range(start, periods=len(prices), freq="D", tz="UTC")
    rows = []
    prev = prices[0]
    for i, (ts, c) in enumerate(zip(days, prices)):
        o = prev
        r = {"ts": ts, "day": ts.strftime("%Y-%m-%d"), "open": o, "high": max(o, c) * 1.001,
             "low": min(o, c) * 0.999, "close": c, "volume": 1.0, "regime": "Bull",
             "funding": (funding or {}).get(i, [])}
        r.update(overrides.get(i, {}))
        rows.append(r)
        prev = c
    return pd.DataFrame(rows)


@pytest.fixture
def random_daily():
    rng = np.random.default_rng(7)
    n = 900
    close = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.03, n)))
    ts = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    o = np.r_[close[0], close[:-1]]
    hi = np.maximum(o, close) * (1 + rng.uniform(0, 0.02, n))
    lo = np.minimum(o, close) * (1 - rng.uniform(0, 0.02, n))
    return pd.DataFrame({"ts": ts, "day": ts.strftime("%Y-%m-%d"), "open": o, "high": hi,
                         "low": lo, "close": close, "volume": 1.0})
