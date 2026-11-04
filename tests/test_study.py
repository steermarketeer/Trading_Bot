"""Signal study: outcome labelling, no-lookahead for signals/patterns/trend, pattern detection."""
import numpy as np
import pandas as pd
import pytest

from bot.study.outcomes import OutcomeParams, label_outcomes
from bot.study.patterns import detect_patterns, swing_points
from bot.study.run import add_leverage, wilson
from bot.study.signals import compute_signals
from bot.study.trend import add_weekly_trend, alignment


def bars_from(closes, atr=1.0, start="2024-01-01"):
    ts = pd.date_range(start, periods=len(closes), freq="D", tz="UTC")
    c = np.asarray(closes, float)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"ts": ts, "day": ts.strftime("%Y-%m-%d"), "open": o,
                         "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c,
                         "volume": 1.0, "atr14": atr})


def label(b, direction, p=OutcomeParams(target_atr=2, stop_atr=1, max_days=5)):
    ev = pd.DataFrame({"day": [b["day"][0]], "direction": [direction], "signal": ["x"]})
    return label_outcomes(b, ev, p=p).iloc[0]


# ---------------------------------------------------------------- outcomes
def test_win_when_target_first():
    b = bars_from([100, 100, 100.5, 102.5, 103, 103, 103, 103])
    r = label(b, 1)
    assert r.outcome == "win" and r.r == 2 and r.entry == 100


def test_loss_when_stop_first():
    b = bars_from([100, 100, 99.5, 98.5, 103, 103, 103, 103])
    r = label(b, 1)
    assert r.outcome == "loss" and r.r == -1


def test_same_day_both_hit_counts_as_loss():
    b = bars_from([100] * 8)
    b.loc[2, ["high", "low"]] = [103, 98.5]
    assert label(b, 1).outcome == "loss"


def test_short_mirror():
    b = bars_from([100, 100, 99.5, 97.5, 97, 97, 97, 97])
    r = label(b, -1)
    assert r.outcome == "win" and r.r == 2


def test_timeout_uses_close_after_max_days():
    b = bars_from([100, 100, 100.3, 100.6, 100.9, 100.5, 100.4, 100])
    r = label(b, 1)
    assert r.outcome == "timeout" and r.r == pytest.approx(0.5)  # close[5] - entry(100)


def test_gap_through_stop_fills_at_open():
    b = bars_from([100, 100, 100, 100, 100, 100, 100, 100])
    b.loc[2, ["open", "high", "low", "close"]] = [97, 97.5, 96.5, 97]
    r = label(b, 1)
    assert r.outcome == "loss" and r.r == pytest.approx(-3)
    assert r.mae_r == pytest.approx(3)


def test_mae_ignores_price_after_stop_exit():
    b = bars_from([100] * 8)
    b.loc[2, "low"] = 90  # stop at 99 hit; the rest of the wick happened after the exit
    r = label(b, 1)
    assert r.outcome == "loss" and r.mae_r == pytest.approx(1)


def test_incomplete_at_end_of_data():
    b = bars_from([100])  # no next day to enter on
    assert label(b, 1).outcome == "incomplete"


def test_leverage_and_liquidation():
    ev = pd.DataFrame({"r": [2.0, -1.0, -1.0], "mae_r": [0.5, 1.0, 1.0],
                       "atr14": [4.0, 4.0, 25.0], "entry": [100.0, 100.0, 100.0]})
    out = add_leverage(ev, leverage=5, cost_frac=0.0, mmr=0.005)
    assert out["margin_ret"].tolist()[:2] == pytest.approx([0.40, -0.20])
    assert out["liquidated"].tolist() == [False, False, True]  # 25% stop beyond ~19.5% liq distance
    assert out["margin_ret"].iloc[2] == -1.0


# ---------------------------------------------------------------- trend
def test_alignment():
    assert alignment(1, "Up") == "with" and alignment(-1, "Down") == "with"
    assert alignment(-1, "Up") == "against" and alignment(1, "Sideways") == "sideways"
    assert alignment(1, "Unknown") == "unknown"


def test_weekly_trend_up_in_steady_rise():
    b = bars_from(np.linspace(100, 400, 600))
    t = add_weekly_trend(b)
    assert t["weekly_trend"].iloc[-1] == "Up"
    assert t["weekly_trend"].iloc[0] == "Unknown"


def test_weekly_trend_no_lookahead(random_daily):
    full = add_weekly_trend(random_daily).set_index("day")["weekly_trend"]
    for cut in range(500, 515):  # every weekday, incl. Sunday/Monday boundaries
        part = add_weekly_trend(random_daily.iloc[:cut]).set_index("day")["weekly_trend"]
        pd.testing.assert_series_equal(part, full.loc[part.index])


def test_weekly_trend_changes_only_on_mondays(random_daily):
    t = add_weekly_trend(random_daily)
    changed = t["weekly_trend"].ne(t["weekly_trend"].shift(1)) & t.index.to_series().gt(0)
    # the trend switches at the Sunday close, i.e. it is first visible on a Sunday row
    assert set(t.loc[changed, "ts"].dt.dayofweek) <= {6}


# ---------------------------------------------------------------- no lookahead: signals & patterns
def _events_up_to(df, cut, fn):
    ev = fn(df.iloc[:cut].reset_index(drop=True))
    last = df["day"].iloc[cut - 1]
    return ev[ev["day"] <= last].sort_values(["day", "signal", "direction"]).reset_index(drop=True)


def test_signals_no_lookahead(random_daily):
    full = compute_signals(random_daily)
    for cut in (300, 450, 777):
        part = _events_up_to(random_daily, cut, compute_signals)
        exp = full[full["day"] <= random_daily["day"].iloc[cut - 1]].sort_values(
            ["day", "signal", "direction"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(part, exp)


def test_patterns_no_lookahead(random_daily):
    full = detect_patterns(random_daily)
    assert len(full) > 0
    for cut in (300, 450, 777):
        part = _events_up_to(random_daily, cut, detect_patterns)
        exp = full[full["day"] <= random_daily["day"].iloc[cut - 1]].sort_values(
            ["day", "signal", "direction"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(part, exp, check_dtype=False)


def test_swing_confirmed_k_bars_later():
    h = np.array([1, 2, 3, 9, 3, 2, 1, 1, 1, 1, 1], float)
    highs, _ = swing_points(h, h - 0.5, k=3)
    assert highs == [(3, 9.0, 6)]


def _path(points):
    """Piecewise-linear closes through (index, price) points."""
    xs, ys = zip(*points)
    return np.interp(np.arange(xs[-1] + 1), xs, ys)


def test_detects_double_top():
    c = _path([(0, 80), (20, 100), (35, 90), (50, 100), (65, 85), (80, 85)])
    ev = detect_patterns(bars_from(c))
    dt = ev[ev["signal"] == "double_top"]
    assert len(dt) == 1 and dt["direction"].iloc[0] == -1
    assert dt["day"].iloc[0] > bars_from(c)["day"].iloc[50]


def test_detects_head_and_shoulders():
    c = _path([(0, 80), (15, 100), (25, 92), (40, 110), (55, 92), (70, 100), (85, 85), (95, 85)])
    ev = detect_patterns(bars_from(c))
    assert (ev["signal"] == "head_shoulders").sum() == 1


def test_detects_ascending_triangle_breakout_up():
    # breakout comes after the last swing low (bar 50) is confirmed at bar 55
    c = _path([(0, 90), (15, 100), (25, 90), (40, 100), (50, 95), (62, 99), (70, 104), (80, 104)])
    ev = detect_patterns(bars_from(c))
    tri = ev[ev["signal"] == "triangle_ascending"]
    assert len(tri) == 1 and tri["direction"].iloc[0] == 1


def test_wilson_interval():
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.404, abs=0.002) and hi == pytest.approx(0.596, abs=0.002)


def test_no_triangle_before_last_swing_is_confirmed():
    # same shape, but price breaks out before the swing low at bar 50 is confirmed -> not knowable
    c = _path([(0, 90), (15, 100), (25, 90), (40, 100), (50, 95), (60, 108), (70, 108)])
    ev = detect_patterns(bars_from(c))
    assert (ev["signal"] == "triangle_ascending").sum() == 0


def test_one_breakout_is_one_pattern():
    """Audit finding: an H&S breakout was also counted as a triangle at the same level."""
    c = _path([(0, 80), (15, 100), (25, 92), (40, 110), (55, 92), (70, 100), (85, 85), (95, 85)])
    ev = detect_patterns(bars_from(c))
    assert len(ev) == 1 and ev["signal"].iloc[0] == "head_shoulders"


def test_pattern_swings_are_not_reused(random_daily):
    from bot.study.patterns import PatternParams
    ev = detect_patterns(random_daily)
    # every breakout day + level is unique (no structure counted twice)
    assert not ev.duplicated(["day", "level"]).any()


def test_early_exit_near_data_end_is_labelled():
    b = bars_from([100, 100, 100.5, 102.5, 103])  # target hit on day 3, only 4 days of data
    r = label(b, 1)
    assert r.outcome == "win"


def test_open_trade_at_data_end_is_incomplete():
    b = bars_from([100, 100, 100.2, 100.1])
    assert label(b, 1).outcome == "incomplete"


def test_bad_wick_is_clipped_but_real_crash_kept():
    from bot.data import clip_bad_wicks
    ts = pd.date_range("2020-03-13", periods=5, freq="5min", tz="UTC")
    df = pd.DataFrame({"open_time": ts, "open": [104, 103, 103, 117, 117], "close": [103, 103, 117, 117, 116],
                       "high": [105, 104, 323, 118, 118], "low": [102, 102, 101, 116, 80], "volume": 1.0})
    out, hits = clip_bad_wicks(df)
    assert out["high"].iloc[2] == 117  # 323 spike removed (body/neighbours max is 117)
    assert out["low"].iloc[4] == 116  # isolated -31% wick also removed
    assert len(hits) == 2
    real = df.copy()
    real.loc[2, ["open", "close", "high", "low"]] = [103, 90, 104, 88]  # real move: echoed by the close
    real.loc[3, "open"] = 90
    out2, hits2 = clip_bad_wicks(real.iloc[:4])
    assert hits2 == []


def test_mtf_hints_use_only_closed_candles():
    """Hints at entry must not change when all 5m data after the entry time is removed."""
    from bot.study.mtf import hint_columns, hints_at
    rng = np.random.default_rng(3)
    n = 288 * 120  # 120 days of 5m bars
    ts = pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC")
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    o = np.r_[c[0], c[:-1]]
    df5 = pd.DataFrame({"open_time": ts, "open": o, "close": c, "high": np.maximum(o, c) * 1.001,
                        "low": np.minimum(o, c) * 0.999, "volume": 1.0})
    trades = pd.DataFrame({"entry_time": pd.to_datetime(["2024-03-20", "2024-04-10"], utc=True),
                           "direction": [1, -1]})
    full = hints_at(df5, trades)
    for k in range(2):
        cut = df5[df5["open_time"] < trades["entry_time"][k]]
        part = hints_at(cut, trades.iloc[[k]])
        assert part[hint_columns()].iloc[0].tolist() == full[hint_columns()].iloc[k].tolist()


def _synthetic_5m(days=150, seed=5, start="2024-01-01"):
    rng = np.random.default_rng(seed)
    n = 288 * days
    ts = pd.date_range(start, periods=n, freq="5min", tz="UTC")
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open_time": ts, "open": o, "close": c, "high": np.maximum(o, c) * 1.001,
                         "low": np.minimum(o, c) * 0.999, "volume": rng.uniform(1, 10, n)})


def test_new_hints_use_only_closed_candles():
    from bot.study.mtf2 import context_hints, tf_hints2
    eth, btc = _synthetic_5m(seed=5), _synthetic_5m(seed=6)
    btc[["open", "close", "high", "low"]] *= 300
    fund = pd.DataFrame({"time": pd.date_range("2024-01-01", periods=150 * 3, freq="8h", tz="UTC"),
                         "rate": np.random.default_rng(1).normal(0.0001, 0.0002, 450)})
    trades = pd.DataFrame({"entry_time": pd.to_datetime(["2024-04-20", "2024-05-11"], utc=True),
                           "direction": [1, -1], "entry": [100.0, 100.0], "atr14": [3.0, 3.0]})
    full_tf = tf_hints2(eth, trades)
    full_ctx = context_hints(trades, eth, btc, fund)
    for k in range(2):
        t = trades["entry_time"][k]
        e_cut, b_cut = eth[eth["open_time"] < t], btc[btc["open_time"] < t]
        f_cut = fund[fund["time"] <= t]
        one = trades.iloc[[k]].reset_index(drop=True)
        assert tf_hints2(e_cut, one).iloc[0].tolist() == full_tf.iloc[k].tolist()
        assert context_hints(one, e_cut, b_cut, f_cut).iloc[0].tolist() == full_ctx.iloc[k].tolist()


def test_direction_free_hints_ignore_direction():
    from bot.study.mtf2 import tf_hints2
    eth = _synthetic_5m()
    t = pd.DataFrame({"entry_time": pd.to_datetime(["2024-04-20", "2024-04-20"], utc=True), "direction": [1, -1]})
    h = tf_hints2(eth, t)
    for tf in ("1h", "1D"):
        assert h[f"{tf}_adx_weak"].iloc[0] == h[f"{tf}_adx_weak"].iloc[1]
        assert h[f"{tf}_vol_expand"].iloc[0] == h[f"{tf}_vol_expand"].iloc[1]
        # directional hints flip sign between long and short
        assert h[f"{tf}_supertrend"].iloc[0] == -h[f"{tf}_supertrend"].iloc[1]


def test_level_hints_use_only_confirmed_swings():
    from bot.study.levels import level_hints
    eth = _synthetic_5m(days=200, seed=9)
    trades = pd.DataFrame({"entry_time": pd.to_datetime(["2024-05-01", "2024-06-15"], utc=True),
                           "direction": [-1, 1], "entry": [100.0, 100.0], "atr14": [3.0, 3.0]})
    for col in ("entry",):
        trades[col] = [float(eth.loc[eth["open_time"] == t, "open"].iloc[0]) for t in trades["entry_time"]]
    full = level_hints(trades, eth)
    for k in range(2):
        cut = eth[eth["open_time"] < trades["entry_time"][k]]
        one = trades.iloc[[k]].reset_index(drop=True)
        assert level_hints(one, cut).iloc[0].tolist() == full.iloc[k].tolist()


def test_sr_label_trades():
    from bot.study.sr_study import label_trades
    b = pd.DataFrame({"open": [100, 100, 101, 103, 104.5], "high": [100, 101, 103, 105, 105],
                      "low": [99, 99.5, 100.5, 102.5, 104], "close": [100, 101, 103, 104.5, 104.5]})
    ev = pd.DataFrame({"j": [0], "direction": [1], "stop": [98.0]})
    r = label_trades(b, ev).iloc[0]
    assert r.entry == 100 and r.risk == 2 and r.outcome == "win" and r.r == 2  # target 104 hit on candle 3
    ev2 = pd.DataFrame({"j": [0], "direction": [-1], "stop": [101.5]})
    assert label_trades(b, ev2).iloc[0].outcome == "loss"  # short: high 103 on candle 2 > stop


def test_sr_touch_features_no_lookahead():
    from bot.study.sr_study import find_touches
    eth = _synthetic_5m(days=260, seed=21)
    full = find_touches(eth, "4h", None)
    assert len(full) > 5
    cut_t = full["time"].iloc[len(full) // 2]
    part = find_touches(eth[eth["open_time"] < cut_t], "4h", None)
    cols = ["time", "kind", "level", "held_at_close", "stop", "vol_touch", "vol_approach", "vol_slope", "vol_div",
            "wick", "sweep", "rsi", "rsi_div", "macd_turn", "ema50_with", "ema200_with", "structure", "speed",
            "zone_weekly", "zone_touches", "weekly_trend_vs", "daily_trend_vs"]
    a = full[full["time"] < cut_t][cols].reset_index(drop=True)
    b = part[part["time"] < cut_t][cols].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_sizing_risk_caps_leverage():
    from bot.study.sr_study import sequential_weekly
    t = pd.DataFrame({"time": pd.to_datetime(["2024-01-01", "2024-01-08"], utc=True), "r": [-1.0, 2.0],
                      "risk": [1.0, 1.0], "entry": [100.0, 100.0], "outcome": ["loss", "win"],
                      "bars": [1, 1], "bar_len": pd.Timedelta("4h")})
    out = sequential_weekly(t, 5, 0.0, sizing="risk", risk_frac=0.02)
    # 1% stop -> 2% risk needs 2x leverage: -2% then +4%
    assert out["final_equity"] == pytest.approx(0.98 * 1.04)


def test_sr2_label_multi():
    from bot.study.sr2 import label_multi
    o = np.array([100, 100, 101, 102.5, 104.5]); h = np.array([100, 101, 103, 105, 105])
    l = np.array([99, 99.5, 100.5, 102, 104]); c = np.array([100, 101, 103, 104.5, 104.5])
    r = label_multi(o, h, l, c, 1, 1, 98.0, max_bars=4)
    # risk 2: 1R=102 hit on candle 2, 1.5R=103 hit on candle 2 (high 103), 2R=104 on candle 3
    assert r["out_1"] == "win" and r["out_1.5"] == "win" and r["out_2"] == "win"
    r2 = label_multi(o, h, l, c, 1, -1, 101.5, max_bars=4)   # short, stop 101.5: candle 2 high 103 -> loss
    assert r2["out_1"] == "loss" and r2["r_1"] == -1


def test_sr2_features_no_lookahead():
    from bot.study.mtf import resample
    from bot.study.sr2 import build_events
    eth = _synthetic_5m(days=260, seed=23)
    full = build_events(eth, "4h", resample)
    assert len(full) > 5 and set(full["event"]) >= {"reversal_now"}
    cut_t = full["time"].iloc[len(full) // 2]
    part = build_events(eth[eth["open_time"] < cut_t], "4h", resample)
    fcols = [c for c in full.columns if c.startswith("f_")] + ["time", "event", "level", "touch_n", "direction"]
    a = full[full["decision_time"] < cut_t - pd.Timedelta("4h")][fcols].reset_index(drop=True)
    b = part[part["decision_time"] < cut_t - pd.Timedelta("4h")][fcols].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_concept_events_no_lookahead():
    from bot.study.concepts import add_confluence, detect_events
    from bot.study.mtf import resample
    eth = _synthetic_5m(days=300, seed=31)
    full = detect_events(eth, "4h", resample)
    assert len(full) > 10
    kinds = set(full["event"])
    assert {"bos", "zone_bounce"} & kinds
    cut_t = full["decision_time"].iloc[len(full) // 2]
    part = detect_events(eth[eth["open_time"] < cut_t], "4h", resample)
    cols = [c for c in full.columns if c.startswith("f_")] + ["event", "decision_time", "direction", "ref_level",
                                                               "structure"]
    lim = cut_t - pd.Timedelta("4h")
    a = full[full["decision_time"] < lim][cols].reset_index(drop=True)
    b = part[part["decision_time"] < lim][cols].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    ca, cb = add_confluence(full), add_confluence(part)
    cc = [c for c in ca.columns if c.startswith("c_")] + ["event", "decision_time"]
    pd.testing.assert_frame_equal(ca[ca["decision_time"] < lim][cc].reset_index(drop=True),
                                  cb[cb["decision_time"] < lim][cc].reset_index(drop=True))


def test_trendline_rules():
    from bot.study.concepts import Bars, best_trendline
    # rising lows at bars 10 and 30, price above the line afterwards -> valid support line
    n = 60
    c = np.r_[np.linspace(100, 95, 11), np.linspace(95.5, 110, 10), np.linspace(109, 99, 10), np.linspace(99.5, 115, 29)]
    b = pd.DataFrame({"open_time": pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC"),
                      "close_time": pd.date_range("2024-01-01 04:00", periods=n, freq="4h", tz="UTC"),
                      "open": c, "high": c + 0.3, "low": c - 0.3, "close": c, "volume": 1.0})
    bars = Bars(b)
    line = best_trendline([(10, 94.7), (30, 98.7)], "support", 55, bars)
    assert line is not None and line[0] == 10 and line[2] == 30
    # a close far below the line invalidates it
    b2 = b.copy()
    b2.loc[45, "close"] = 90.0
    assert best_trendline([(10, 94.7), (30, 98.7)], "support", 55, Bars(b2)) is None
