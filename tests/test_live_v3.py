import numpy as np
import pandas as pd
import pytest

from bot.live.v3 import account, replay


def _df5(prices, start="2024-01-01"):
    t = pd.date_range(start, periods=len(prices), freq="5min")
    p = np.asarray(prices, float)
    o = np.r_[p[0], p[:-1]]
    return pd.DataFrame({"open_time": t, "open": o, "high": np.maximum(o, p), "low": np.minimum(o, p), "close": p})


def _sig(entry_time, d, entry, stop, target, setup="breakout", tf="2h"):
    return pd.DataFrame([{"entry_time": pd.Timestamp(entry_time), "setup": setup, "tf": tf, "event": "x",
                          "direction": d, "entry": entry, "stop": stop, "risk": abs(entry - stop),
                          "stop_pct": abs(entry - stop) / entry, "certainty": 7, "pending_entry": False,
                          "target": target}])


def test_replay_target_stop_open_and_pending():
    df = _df5([100, 100.5, 101, 101.5, 102.2, 102, 101])
    t = replay(_sig("2024-01-01", 1, 100, 99, 102), df).iloc[0]
    assert t.status == "closed" and t.reason == "target" and t.R == pytest.approx(2)
    t = replay(_sig("2024-01-01", -1, 100, 101, 98), df).iloc[0]
    assert t.status == "closed" and t.reason == "stop" and t.R == pytest.approx(-1)
    t = replay(_sig("2024-01-01", 1, 100, 95, 110), df).iloc[0]
    assert t.status == "open" and t.R == pytest.approx(0.2)        # last close 101, risk 5
    s = _sig("2024-01-01", 1, np.nan, 95, np.nan).assign(pending_entry=True)
    assert replay(s, df).iloc[0].status == "pending"


def test_account_books_closed_and_marks_open():
    tr = pd.DataFrame([
        {"entry_time": pd.Timestamp("2024-01-01"), "exit_time": pd.Timestamp("2024-01-02"), "status": "closed",
         "setup": "breakout", "stop_pct": 0.01, "R": 2.0},
        {"entry_time": pd.Timestamp("2024-01-03"), "exit_time": pd.NaT, "status": "open",
         "setup": "breakout", "stop_pct": 0.01, "R": 0.5}])
    curve, eq, unreal = account(tr, pd.Timestamp("2024-01-01"))
    cost = 0.0018
    assert eq == pytest.approx(1 + 2.0 * (0.02 - cost))          # 2% risk, 1% stop -> 2x notional
    assert unreal == pytest.approx(eq * 2.0 * (0.005 - cost))
