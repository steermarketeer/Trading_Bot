"""Truncating the future must not change any past value."""
import pandas as pd

from bot.regime import compute_daily_regime
from bot.strategies import make_strategy


def test_regime_has_no_lookahead(random_daily):
    btc = random_daily.copy()
    full = compute_daily_regime(random_daily, btc, extra_lag=0).set_index("day")
    for cut in (400, 517, 650, 899):
        part = compute_daily_regime(random_daily.iloc[:cut], btc.iloc[:cut], extra_lag=0).set_index("day")
        pd.testing.assert_frame_equal(part, full.loc[part.index], check_dtype=False)


def test_regime_uses_only_closed_weeks(random_daily):
    """A day's regime must equal the one computed when the data ends on that same day."""
    btc = random_daily.copy()
    full = compute_daily_regime(random_daily, btc, extra_lag=0).set_index("day")
    for cut in (420, 421, 422, 423, 424, 425, 426):  # every weekday
        part = compute_daily_regime(random_daily.iloc[:cut], btc.iloc[:cut], extra_lag=0)
        last = part.iloc[-1]
        assert full.loc[last["day"], "regime"] == last["regime"]


def test_htf_trend_prepare_has_no_lookahead(random_daily):
    d = random_daily.copy()
    d["btc_close"] = d["close"] * 20
    d["regime"] = (["Bull"] * 300 + ["Bear"] * 300 + ["Neutral"] * 300)
    s = make_strategy("htf_trend", "t", {"btc_confirm": True})
    full = s.prepare(d)
    part = s.prepare(d.iloc[:500])
    cols = s.required_columns() + ["regime_stable_days"]
    pd.testing.assert_frame_equal(part[cols], full.iloc[:500][cols])
