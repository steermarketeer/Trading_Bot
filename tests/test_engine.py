import pytest

from bot.config import Costs, Risk
from bot.engine import Engine, EngineState, rows_ready
from bot.strategies import make_strategy

from conftest import make_bars

NO_COSTS = Costs(taker_fee=0.0, slippage_bps=0.0, funding=True, maintenance_margin=0.005)


def run(bars, entries=None, exits=None, risk=None, costs=NO_COSTS):
    s = make_strategy("scripted", "t", {"entries": entries or {}, "exits": exits or {}})
    eng = Engine(s, risk or Risk(), costs)
    st = EngineState()
    days, trades = [], []
    for row in rows_ready(s, s.prepare(bars)):
        rec, tr = eng.step(st, row)
        days.append(rec)
        trades += tr
    return st, days, trades


def test_signal_at_close_fills_next_open():
    bars = make_bars([100, 110, 120, 130, 140], overrides={})
    bars.loc[2, "open"] = 115.0  # day 2 opens at 115
    st, days, trades = run(bars, entries={bars.day[1]: "long"}, exits={bars.day[3]: "rule"})
    assert len(trades) == 1
    t = trades[0]
    assert t["signal_day"] == bars.day[1]
    assert t["entry_day"] == bars.day[2] and t["entry_price"] == pytest.approx(115.0)
    assert t["exit_day"] == bars.day[4] and t["exit_price"] == pytest.approx(130.0)  # day4 open = day3 close
    assert t["net_return"] == pytest.approx(130 / 115 - 1)


def test_fees_and_slippage_are_charged_both_sides():
    bars = make_bars([100, 100, 100, 100])
    costs = Costs(taker_fee=0.001, slippage_bps=10, funding=False)
    _, _, trades = run(bars, entries={bars.day[0]: "long"}, exits={bars.day[1]: "x"}, costs=costs)
    t = trades[0]
    assert t["entry_price"] == pytest.approx(100.1)
    assert t["exit_price"] == pytest.approx(99.9)
    assert t["net_return"] < -0.003  # 2 x 0.1% fee + 2 x 0.1% slippage


def test_intraday_stop_uses_low_not_close():
    bars = make_bars([100, 100, 100, 100, 100])
    bars.loc[2, "low"] = 89.0  # wick through a 10% stop, closes back at 100
    _, days, trades = run(bars, entries={bars.day[0]: "long"}, risk=Risk(stop_pct=0.10))
    assert trades[0]["exit_reason"] == "stop"
    assert trades[0]["exit_day"] == bars.day[2]
    assert trades[0]["exit_price"] == pytest.approx(90.0)


def test_stop_gap_fills_at_open():
    bars = make_bars([100, 100, 100, 100])
    bars.loc[2, ["open", "low", "high", "close"]] = [80.0, 79.0, 81.0, 80.0]
    _, _, trades = run(bars, entries={bars.day[0]: "long"}, risk=Risk(stop_pct=0.10))
    assert trades[0]["exit_reason"] == "stop_gap"
    assert trades[0]["exit_price"] == pytest.approx(80.0)


def test_short_stop_uses_high():
    bars = make_bars([100, 100, 100, 100])
    bars.loc[2, "high"] = 111.0
    _, _, trades = run(bars, entries={bars.day[0]: "short"}, risk=Risk(stop_pct=0.10))
    assert trades[0]["exit_price"] == pytest.approx(110.0)
    assert trades[0]["net_return"] == pytest.approx(-0.10)


def test_liquidation_loses_margin_only():
    bars = make_bars([100, 100, 100, 100])
    bars.loc[2, "low"] = 70.0
    st, _, trades = run(bars, entries={bars.day[0]: "long"}, risk=Risk(leverage=5, size_frac=0.5))
    assert trades[0]["exit_reason"] == "liquidation"
    assert st.equity == pytest.approx(0.5)  # lost the 50% margin, kept the rest


def test_stop_before_liquidation_when_closer():
    bars = make_bars([100, 100, 100, 100])
    bars.loc[2, "low"] = 70.0
    _, _, trades = run(bars, entries={bars.day[0]: "long"}, risk=Risk(leverage=5, stop_pct=0.05))
    assert trades[0]["exit_reason"] == "stop"
    assert trades[0]["net_return"] == pytest.approx(-0.25)  # 5% move x 5x


def test_funding_long_pays_short_receives():
    fund = {i: [(0.0, 0.001), (8.0, 0.001), (16.0, 0.001)] for i in range(10)}
    bars = make_bars([100] * 6, funding=fund)
    _, _, tl = run(bars, entries={bars.day[0]: "long"}, exits={bars.day[2]: "x"})
    _, _, ts = run(bars, entries={bars.day[0]: "short"}, exits={bars.day[2]: "x"})
    # entered day1 open (skip day1 00:00), held day1 08/16, day2 00/08/16, exit day3 open (pays day3 00:00)
    assert tl[0]["funding"] == pytest.approx(6 * 0.001)
    assert tl[0]["net_return"] == pytest.approx(-0.006)
    assert ts[0]["net_return"] == pytest.approx(+0.006)


def test_funding_can_be_disabled():
    fund = {i: [(8.0, 0.01)] for i in range(10)}
    bars = make_bars([100] * 5, funding=fund)
    costs = Costs(taker_fee=0, slippage_bps=0, funding=False)
    _, _, t = run(bars, entries={bars.day[0]: "long"}, exits={bars.day[2]: "x"}, costs=costs)
    assert t[0]["funding"] == 0


def test_cooldown_blocks_entries():
    bars = make_bars([100] * 12)
    entries = {d: "long" for d in bars.day}
    _, days, trades = run(bars, entries=entries, exits={bars.day[1]: "x"}, risk=Risk(cooldown_days=3))
    # exit fills day2 open; closes of day2,3,4 are cooldown; signal on day5 -> enter day6
    assert trades[0]["exit_day"] == bars.day[2]
    enters = [d["day"] for d in days if "ENTER_LONG" in d["actions"]]
    assert enters[:2] == [bars.day[1], bars.day[6]]


def test_drawdown_halt_resumes():
    """Legacy bug: a halted strategy could never trade again. Now it resumes after halt_days."""
    prices = [100, 100, 70, 70] + [70] * 12
    bars = make_bars(prices)
    entries = {d: "long" for d in bars.day}
    risk = Risk(dd_halt=0.2, halt_days=5)
    _, days, trades = run(bars, entries=entries, exits={bars.day[2]: "x"}, risk=risk)
    acts = [d["actions"] for d in days]
    assert any("HALT" in a for a in acts)
    assert any("RESUME" in a for a in acts)
    later = [d for d in days if "ENTER_LONG" in d["actions"]]
    assert len(later) >= 2  # traded again after the halt


def test_mtm_drawdown_halt_exits_position():
    prices = [100, 100, 150, 100, 100, 100, 100]
    bars = make_bars(prices)
    risk = Risk(dd_halt=0.25, halt_days=3, dd_basis="mtm")
    _, days, trades = run(bars, entries={bars.day[0]: "long"}, risk=risk)
    assert trades and trades[0]["exit_reason"] == "dd_halt"


def test_bad_dd_basis_rejected():
    with pytest.raises(ValueError):
        run(make_bars([1, 1]), risk=Risk(dd_basis="nope"))
