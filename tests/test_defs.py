import numpy as np
import pandas as pd

from bot.study.defs import TF, equal_levels, failed_pushes, rejections, sweep, breakout_close, fakeout, band_failure


def _bars(highs, lows, closes, opens=None):
    n = len(highs)
    t = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    opens = opens if opens is not None else np.r_[closes[0], closes[:-1]]
    return TF(pd.DataFrame({"open_time": t, "close_time": t + pd.Timedelta(hours=4) - pd.Timedelta(milliseconds=1),
                            "open": opens, "high": highs, "low": lows, "close": closes, "volume": 1.0}))


def _wave(peaks):
    """Piecewise-linear closes through the given (index, price) points; highs/lows +-0.5 around closes."""
    xs, ys = zip(*peaks)
    c = np.interp(np.arange(xs[-1] + 1), xs, ys)
    return c + 0.5, c - 0.5, c


def test_double_top_found_confirmed_and_no_lookahead():
    h, l, c = _wave([(0, 90), (20, 100), (30, 94), (40, 100.1), (55, 88), (70, 90)])
    t = _bars(h, l, c)
    found = [e for e in equal_levels(t, "H", t.n) if len(e.idx) >= 2]
    assert found, "double top not found"
    e = found[0]
    assert sorted(e.idx) == [20, 40]
    assert abs(e.valley - (94 - 0.5)) < 1e-9                 # neckline = low between the tops
    assert e.confirmed_at > 40 and c[e.confirmed_at] < e.valley
    # truncated before the second top is confirmed: no double top yet
    t2 = _bars(h[:43], l[:43], c[:43])
    assert not [x for x in equal_levels(t2, "H", t2.n) if 40 in x.idx]


def test_rejection_and_failed_pushes():
    n = 40
    c = np.full(n, 95.0); h = c + 1; l = c - 1; o = c.copy()
    h[20], c[20], o[20] = 101.0, 96.0, 97.0                  # pierced 100 and closed well below: rejection
    h[25], c[25], o[25] = 98.5, 98.0, 95.0                   # up candle that falls short: failed push
    h[30], c[30], o[30] = 97.5, 97.0, 95.0                   # lower failed push
    t = _bars(h, l, c, o)
    assert rejections(t, 100.0, "R", 0, n) == [20]
    fp = failed_pushes(t, 100.0, "R", 21, n)
    assert 25 in fp and 30 in fp and h[25] > h[30]


def test_sweep_breakout_fakeout_band_failure():
    n = 60
    c = 100 + np.sin(np.arange(n) / 3.0); h = c + 0.6; l = c - 0.6
    h[30], c[30] = 103.5, 101.0                              # wick above 103, close back below: sweep of 103
    t = _bars(h, l, c)
    assert sweep(t, 30, 103.0, "H")
    c2 = c.copy(); c2[40] = 104.0; c2[41] = 101.0; h2 = np.maximum(h, c2 + 0.3); l2 = np.minimum(l, c2 - 0.3)
    t2 = _bars(h2, l2, c2)
    assert breakout_close(t2, 40, 103.0, 1) and fakeout(t2, 40, 103.0, 1)
    assert band_failure(t2, 41, "U")
