import numpy as np
import pandas as pd

from bot.ml.manager import FailState, context_table, trade_states
from bot.study.defs import TF


def test_failstate_lower_high_then_close_below_pullback():
    f = FailState()
    assert not f.step(10, 9, 9.8)      # peak 10
    assert not f.step(9.9, 8, 8.5)     # pullback low 8 (no lower high yet: pull was unset)
    assert not f.step(9.5, 8.8, 9.2)   # lower high 9.5 between pullback 8 and peak 10
    assert f.lh
    assert f.step(9.0, 7.5, 7.8)       # close below the pullback low 8 -> failure
    assert f.fail
    assert not f.step(11, 10, 10.8)    # new high resets
    assert not f.fail and not f.lh


def _bars(n, seed=0, freq="5min"):
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.3, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.random(n) * 0.2
    l = np.minimum(o, c) - rng.random(n) * 0.2
    ot = pd.date_range("2022-01-01", periods=n, freq=freq)
    return pd.DataFrame({"open_time": ot, "open": o, "high": h, "low": l, "close": c, "volume": rng.random(n) + 1,
                         "close_time": ot + pd.Timedelta(freq)})


def _agg(df, rule):
    g = df.set_index("open_time").resample(rule, label="left", closed="left")
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "volume": g["volume"].sum()}).dropna().reset_index()
    b["close_time"] = b["open_time"] + pd.Timedelta(rule)
    return b


def _model_inputs(df):
    tfs = {k: TF(_agg(df, r)) for k, r in (("1h", "1h"), ("4h", "4h"), ("1D", "1D"))}
    M = {"t5": df["open_time"].to_numpy(), "O": df["open"].to_numpy(float), "H": df["high"].to_numpy(float),
         "L": df["low"].to_numpy(float), "C": df["close"].to_numpy(float),
         "fund": (np.array([], dtype="datetime64[ns]"), np.array([0.0])), "tf": tfs}
    M["ctx"] = {"4h": context_table(tfs["4h"]), "1D": context_table(tfs["1D"], daily=True)}
    return M


def test_states_use_only_closed_candles():
    df = _bars(288 * 60)
    i0 = 288 * 40
    tr = {"d": 1, "e": df["open"].iloc[i0], "s": df["open"].iloc[i0] - 50, "tg": df["open"].iloc[i0] + 50,
          "i0": i0, "end": i0 + 288 * 15, "tf_h": 4.0}
    st_a, _ = trade_states(_model_inputs(df), tr)
    # change everything after the 10th state's close: the first 10 states (inputs) must not change
    cut_t = st_a[9]["T"]
    df2 = df.copy()
    late = df2["open_time"] >= cut_t
    for col in ("open", "high", "low", "close"):
        df2.loc[late, col] = df2.loc[late, col] * 1.05
    st_b, _ = trade_states(_model_inputs(df2), tr)
    skip = {"y", "x_now", "T", "iT"}
    for a, b in zip(st_a[:10], st_b[:10]):
        for k in a:
            if k in skip:
                continue
            va, vb = a[k], b[k]
            assert (np.isnan(va) and np.isnan(vb)) or np.isclose(va, vb), k
