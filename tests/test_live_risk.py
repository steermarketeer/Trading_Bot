import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from bot.live.breaker import FLATTEN, HALT, RUN, BreakerLimits, CircuitBreaker
from bot.live.execution import Order, PaperExecution
from bot.live.risk import AccountState, OpenPosition, RiskLimits, RiskManager, Signal

T0 = datetime(2026, 1, 5, tzinfo=timezone.utc)


def sig(side="long", entry=2000.0, stop=1980.0, target=2040.0, setup="breakout"):
    return Signal(setup, side, entry, stop, target, "2h", decision_time="2026-01-05 02:00")


def test_sizing_is_fixed_fractional_and_lev_capped():
    rm = RiskManager()
    st = AccountState(10_000, 10_000, 10_000)
    qty, notional = rm.size(sig(), st.equity)
    assert qty == pytest.approx(0.02 * 10_000 / 20)                  # 2% of equity over a $20 stop
    assert notional == pytest.approx(qty * 2000)
    # a tiny stop would ask for 100x: capped at 5x equity
    qty2, notional2 = rm.size(sig(stop=1999.0), st.equity)
    assert notional2 == pytest.approx(5 * 10_000)
    assert qty2 == pytest.approx(notional2 / 2000)
    # A+ risks 4%
    qty3, _ = rm.size(sig(setup="A+ breakout"), st.equity)
    assert qty3 == pytest.approx(0.04 * 10_000 / 20)


def test_checks_reject_bad_geometry_and_small_stops():
    rm = RiskManager()
    st = AccountState(10_000, 10_000, 10_000)
    assert not rm.check(sig(stop=2010.0), st, 0.03).ok                 # stop above a long entry
    assert not rm.check(sig(target=1990.0), st, 0.03).ok               # target below a long entry
    assert not rm.check(sig(stop=1995.0), st, 0.03).ok                 # 0.25% stop < 0.6% minimum
    assert rm.check(sig(side="short", entry=2000, stop=2020, target=1960), st, 0.03).ok


def test_daily_and_weekly_stops_halt_entries_and_roll():
    rm = RiskManager()
    st = AccountState(9_500, 10_000, 10_000)                             # down 5% today
    d = rm.check(sig(), st, 0.03)
    assert not d.ok and d.reason.startswith("halted: daily stop")
    rm.roll_day(st)
    assert rm.check(sig(), st, 0.03).ok
    st = AccountState(9_100, 9_100, 10_000)                              # down 9% this week
    assert rm.check(sig(), st, 0.03).reason.startswith("halted: weekly stop")


def test_exposure_var_and_one_position_per_move():
    rm = RiskManager()
    st = AccountState(10_000, 10_000, 10_000)
    s = sig()
    d = rm.check(s, st, sigma_daily=0.03)
    assert d.ok and d.reason == "ok"                                       # 2x notional, VaR 14% < 35%
    st.positions["2026-01-05 02:00|long"] = OpenPosition("k", "long", d.qty, 2000, 1980, 2040, 0.03)
    assert "one position per move" in rm.check(s, st, 0.03).reason
    # VaR cut: a 5x trade at 6% daily volatility would be 70% VaR; it is cut to 35% -> half the size
    st.positions.clear()
    big = Signal("breakout", "long", 2000.0, 1988.0, 2024.0, "2h", decision_time="2026-01-05 04:00")   # 0.6% stop -> 3.33x
    r = rm.check(big, st, sigma_daily=0.06)
    assert r.ok and "cut" in r.reason
    assert r.notional == pytest.approx(0.35 * 10_000 / (2.326 * 0.06), rel=1e-6)
    # exposure cap: the book already holds 4.5x; the new 3.33x trade would be cut to 0.5x = 15% -> rejected
    st.positions["x|long"] = OpenPosition("x", "long", 4.5 * 10_000 / 2000, 2000, 1900, 2200, 0.03)
    r = rm.check(big, st, sigma_daily=0.03)
    assert not r.ok and r.reason.startswith("caps leave")


def test_chandelier_off_by_default_and_only_tightens_when_on():
    pos = OpenPosition("k", "long", 1.0, 2000, 1980, 2040, 0.03)
    rm = RiskManager()
    assert rm.update_stop(pos, 2100, 2050, 2090, atr_daily=20, hh=2100, ll=2050) == 1980   # off
    rm = RiskManager(RiskLimits(chandelier_on=True, chandelier_k=3.0, chandelier_arm_r=1.0))
    pos = OpenPosition("k", "long", 1.0, 2000, 1980, 2040, 0.03)
    assert rm.update_stop(pos, 2010, 1990, 2005, 20, 2010, 1990) == 1980                   # not armed (+0.5R)
    s1 = rm.update_stop(pos, 2100, 2050, 2090, 20, 2100, 2050)                              # armed: 2100 - 60
    assert s1 == 2040
    s2 = rm.update_stop(pos, 2080, 2030, 2060, 20, 2100, 2030)                              # never loosens
    assert s2 == 2040
    short = OpenPosition("s", "short", 1.0, 2000, 2020, 1960, 0.03)
    assert rm.update_stop(short, 1950, 1900, 1910, 20, 1950, 1900) == 1960                  # 1900 + 60


def test_breaker_trips_and_never_loosens_without_reset():
    cb = CircuitBreaker(BreakerLimits())
    t = T0
    cb.on_candle(t, 2000, 2005, 1995, 2000, atr_5m=4)
    assert cb.state == RUN
    cb.on_candle(t + timedelta(minutes=20), 2000, 2005, 1995, 2000, 4)   # 3 candles missed -> HALT
    assert cb.state == HALT and "stale" in cb.reason
    cb.on_candle(t + timedelta(minutes=25), 2000, 2040, 1990, 2000, 4)   # 12.5 x ATR -> FLATTEN
    assert cb.state == FLATTEN
    cb.on_candle(t + timedelta(minutes=30), 2000, 2001, 1999, 2000, 4)   # calm candle: stays FLATTEN
    assert cb.must_flatten
    cb.reset(t + timedelta(minutes=35), "operator")
    assert cb.may_enter


def test_breaker_api_errors_gap_heartbeat_and_kill():
    cb = CircuitBreaker(BreakerLimits())
    t = T0
    for i in range(3):
        cb.on_api_error(t + timedelta(seconds=10 * i), "timeout")
    assert cb.state == HALT
    cb = CircuitBreaker(BreakerLimits())
    cb.on_candle(t, 2000, 2005, 1995, 2000, 4)
    cb.on_candle(t + timedelta(minutes=5), 2070, 2075, 2065, 2000, 4)   # +3.5% gap
    assert cb.state == FLATTEN
    cb = CircuitBreaker(BreakerLimits())
    cb.on_heartbeat(t)
    cb.check_clock(t + timedelta(minutes=2))
    assert cb.state == RUN
    cb.check_clock(t + timedelta(minutes=4))
    assert cb.state == FLATTEN
    cb = CircuitBreaker(BreakerLimits())
    cb.on_kill_switch(t)
    assert cb.must_flatten


def test_paper_execution_fills_like_the_backtest():
    px = PaperExecution()
    o = Order("k", "long", 1.0, 2000.0, 1980.0, 2040.0)
    f = asyncio.run(px.submit(o, T0))
    assert f.price == pytest.approx(2001.0) and f.fee == pytest.approx(2001.0 * 0.0004)
    # stop and target in the same candle: stop first
    fills = px.on_candle(2000, 2045, 1975, 2010, T0)
    assert fills[0].kind == "stop" and fills[0].price == pytest.approx(1980 * (1 - 0.0005))
    # target needs 0.02% through the limit
    px = PaperExecution(); asyncio.run(px.submit(o, T0))
    assert px.on_candle(2000, 2040.2, 1990, 2030, T0) == []
    fills = px.on_candle(2000, 2040.5, 1990, 2030, T0)
    assert fills[0].kind == "target" and fills[0].price == 2040.0 and fills[0].fee == pytest.approx(2040 * 0.0002)
    # a candle opening through the stop fills at the open
    px = PaperExecution(); asyncio.run(px.submit(o, T0))
    fills = px.on_candle(1970, 1975, 1960, 1965, T0)
    assert fills[0].kind == "stop" and fills[0].price == pytest.approx(1970 * (1 - 0.0005))


def test_daily_stop_latches_until_the_roll():
    rm = RiskManager()
    st = AccountState(9_550, 10_000, 10_000)                             # down 4.5%
    assert not rm.check(sig(), st, 0.03).ok
    st.equity = 9_650                                                    # recovers to -3.5% the same day
    d = rm.check(sig(), st, 0.03)
    assert not d.ok and d.reason.startswith("halted: daily stop")
    rm.roll_day(st)
    assert rm.check(sig(), st, 0.03).ok
    # mark() trips the latch without a signal
    st = AccountState(9_100, 9_100, 10_000)
    rm.mark(st)
    assert st.halted_reason.startswith("weekly stop")
    rm.roll_week(st)
    assert st.halted_reason is None


def test_paper_time_exit_and_funding_match_the_backtest_model():
    px = PaperExecution()
    o = Order("k", "long", 1.0, 2000.0, 1980.0, 2040.0, expires_at=T0 + timedelta(hours=10))
    asyncio.run(px.submit(o, T0))
    # funding at 08:00: a long pays a positive rate on qty * price
    f = px.apply_funding(0.0001, 2010.0, T0 + timedelta(hours=8))
    assert f[0].kind == "funding" and f[0].fee == pytest.approx(1.0 * 2010.0 * 0.0001)
    # before the deadline nothing happens; at the deadline the trade exits at the close with market cost
    assert px.on_candle(2005, 2010, 2000, 2008, T0 + timedelta(hours=9, minutes=55)) == []
    fills = px.on_candle(2005, 2010, 2000, 2008, T0 + timedelta(hours=10))
    assert fills[0].kind == "time" and fills[0].price == pytest.approx(2008 * (1 - 0.0005))
    assert px.open == {}
    # a short receives funding
    px = PaperExecution(); asyncio.run(px.submit(Order("s", "short", 2.0, 2000.0, 2020.0, 1960.0), T0))
    f = px.apply_funding(0.0001, 2000.0, T0)
    assert f[0].fee == pytest.approx(-2.0 * 2000.0 * 0.0001)


def test_weekly_latch_is_independent_of_the_daily_latch():
    rm = RiskManager()
    st = AccountState(9_550, 10_000, 10_000)
    rm.mark(st)                                                          # -4.5% today -> daily latch
    st.equity = 9_100                                                    # -9% for the week
    rm.mark(st)
    assert st.halted_reason.startswith("daily stop") and st.weekly_halt.startswith("weekly stop")
    rm.roll_day(st)
    st.equity = 9_300                                                    # recovered to -7% for the week
    d = rm.check(sig(), st, 0.03)
    assert not d.ok and d.reason.startswith("halted: weekly stop")
    rm.roll_week(st)
    assert rm.check(sig(), st, 0.03).ok
