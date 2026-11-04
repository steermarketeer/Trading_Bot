import numpy as np
import pytest

from bot.study.exits import simulate


def path(prices, spread=0.0):
    p = np.asarray(prices, float)
    o = np.r_[p[0], p[:-1]]
    return o, np.maximum(o, p) + spread, np.minimum(o, p) - spread, p


def test_fixed_targets_and_stop():
    o, h, l, c = path([100, 100.5, 101, 101.5, 102, 102.5, 103])
    r = simulate(o, h, l, c, entry=100, risk=1, atr_=1, bars_per_tf=1)
    assert r["fixed_1R"] == pytest.approx(1) and r["fixed_2R"] == pytest.approx(2) and r["fixed_3R"] == pytest.approx(3)
    o, h, l, c = path([100, 99.5, 98.9, 103])
    r = simulate(o, h, l, c, 100, 1, 1, 1)
    assert r["fixed_2R"] == pytest.approx(-1)


def test_break_even_saves_a_trade_that_was_winning_first():
    o, h, l, c = path([100, 100.6, 100.8, 100.2, 99.5, 98.5])  # +0.8R then reverses through the stop
    r = simulate(o, h, l, c, 100, 1, 1, 1)
    assert r["fixed_2R"] == pytest.approx(-1)
    assert r["be0.5_2R"] == pytest.approx(0)   # stopped at entry instead


def test_partial_takes_half_at_1R():
    o, h, l, c = path([100, 100.6, 101.2, 100.4, 99.9, 99])
    r = simulate(o, h, l, c, 100, 1, 1, 1)
    assert r["partial_2R"] == pytest.approx(0.5)   # +1R on half, the rest stopped at entry


def test_atr_trail_follows_price():
    o, h, l, c = path([100, 101, 102, 103, 104, 103.4, 102])
    r = simulate(o, h, l, c, 100, 1, atr_=1, bars_per_tf=1)
    assert r["atr_trail_1.5"] == pytest.approx(104 - 1.5 - 100)   # trailed to 102.5, exited there


def test_gap_through_stop_fills_at_open():
    o = np.array([100, 97.0]); h = np.array([100.2, 97.5]); l = np.array([99.8, 96.5]); c = np.array([100, 97])
    r = simulate(o, h, l, c, 100, 1, 1, 1)
    assert r["fixed_2R"] == pytest.approx(-3)


def test_time_stop_exits_flat_trades():
    o, h, l, c = path([100, 100.1, 100.2, 100.1, 100.3, 100.2, 102.5])
    r = simulate(o, h, l, c, 100, 1, 1, 1)
    assert r["time3_2R"] == pytest.approx(0.2)   # out at the 3rd candle close (100.2); never reached +0.5R


def test_smalltf_exits_and_account():
    import pandas as pd
    from bot.study.smalltf import account, exits
    o, h, l, c = path([100, 100.6, 101.2, 100.4, 99.9, 99])
    ex = exits(o, h, l, c, 100, 1)
    assert ex["1:1"][0] == pytest.approx(1) and ex["2:1"][0] == pytest.approx(-1)
    assert ex["half@1R+2R"][0] == pytest.approx(0.5)
    t0 = pd.Timestamp("2024-01-01")
    x = pd.DataFrame({"decision_time": [t0, t0 + pd.Timedelta(hours=1)], "stop_pct": [0.01, 0.01],
                      "R_1:1": [1.0, -1.0], "exit_1:1": [t0 + pd.Timedelta(hours=3), t0 + pd.Timedelta(hours=2)]})
    a = account(x, "1:1", 0.0, 0.02)
    # both sized on equity 1.0 (overlapping): -2% booked first, then +2%
    assert a["final"] == pytest.approx(1.0)
