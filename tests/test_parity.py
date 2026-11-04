"""Backtest and shadow must produce identical trades on the same bars."""
import json

import pandas as pd
import pytest

from bot.backtest import run_backtest
from bot.config import Config, Costs, Risk, StrategySpec
from bot.engine import Engine, EngineState, rows_ready
from bot.shadow import run_strategy
from bot.strategies import make_strategy


@pytest.fixture
def bars(random_daily):
    d = random_daily.copy()
    d["btc_close"] = d["close"] * 20
    d["regime"] = ["Bull"] * 250 + ["Bear"] * 250 + ["Neutral"] * 100 + ["Bull"] * 300
    d["funding"] = [[(0.0, 0.0001), (8.0, 0.0002), (16.0, -0.0001)]] * len(d)
    return d


def spec():
    return StrategySpec(
        name="par", type="htf_trend", params={"btc_confirm": True, "regime_stable_days": 3},
        risk=Risk(stop_pct=0.08, cooldown_days=2, dd_halt=0.2, halt_days=10),
    )


def test_state_roundtrip_through_json_gives_same_trades(bars):
    costs = Costs()
    bt = run_backtest(spec(), bars, costs)
    s = make_strategy("htf_trend", "par", spec().params)
    eng = Engine(s, spec().risk, costs)
    rows = rows_ready(s, s.prepare(bars))
    st = EngineState()
    trades = []
    for i, row in enumerate(rows):
        if i % 7 == 0:  # save/load like the shadow does between daily runs
            st = EngineState.from_dict(json.loads(json.dumps(st.to_dict())))
        trades += eng.step(st, row)[1]
    t = eng.force_close(st, rows[-1])
    if t:
        trades.append(t)
    assert len(bt.trades) > 5
    pd.testing.assert_frame_equal(bt.trades.reset_index(drop=True), pd.DataFrame(trades)[bt.trades.columns])


def test_shadow_runner_matches_backtest(bars, tmp_path):
    cfg = Config(data_dir=tmp_path, costs=Costs(), shadow_dir=tmp_path / "shadow")
    sp = spec()
    days = list(bars["day"])
    first = days[400]
    # day 1: start shadow with a long backfill, then advance one day at a time
    run_strategy(sp, cfg, bars, reset=True, backfill_days=10_000, today=first)
    for today in days[401:]:
        run_strategy(sp, cfg, bars, today=today)
    sh = pd.read_csv(tmp_path / "shadow" / "par" / "trades.csv")
    bt = run_backtest(sp, bars[bars["day"] < days[-1]], Costs()).trades
    bt = bt[bt["exit_reason"] != "end_of_data"]
    assert len(sh) == len(bt) > 5
    for col in ("entry_day", "exit_day", "side", "exit_reason"):
        assert list(sh[col]) == list(bt[col])
    assert sh["net_pnl"].to_numpy() == pytest.approx(bt["net_pnl"].to_numpy())
    assert set(sh["source"]) == {"backfill", "forward"}


def test_shadow_refuses_changed_strategy(bars, tmp_path):
    cfg = Config(data_dir=tmp_path, costs=Costs(), shadow_dir=tmp_path / "shadow")
    run_strategy(spec(), cfg, bars, reset=True, today=bars["day"].iloc[500])
    changed = spec()
    changed.params["entry_sma"] = 40
    with pytest.raises(SystemExit):
        run_strategy(changed, cfg, bars, today=bars["day"].iloc[501])
