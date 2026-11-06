"""
Circuit breaker: a small state machine that decides whether the bot may trade, must stop entering, or must flatten.
Pure logic (the caller feeds it events: candles, API results, heartbeats, the kill-switch file state). Manual reset only.

States: RUN -> HALT (no new entries, open positions keep their stops) -> FLATTEN (close everything at market).
Trips to HALT: stale data (>= 2 missed 5m candles), repeated API errors, a daily / weekly risk stop.
Trips to FLATTEN: a flash move (5m range > k x ATR_5m, or a gap > g%), the kill switch, a lost heartbeat.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

RUN, HALT, FLATTEN = "RUN", "HALT", "FLATTEN"


@dataclass(frozen=True)
class BreakerLimits:
    stale_candles: int = 2            # missed 5m candles before HALT
    api_errors: int = 3               # errors within api_window before HALT
    api_window: timedelta = timedelta(minutes=5)
    flash_atr_mult: float = 6.0       # 5m range > 6 x ATR_5m -> FLATTEN
    flash_gap_pct: float = 0.03       # |open - previous close| > 3% -> FLATTEN
    heartbeat_timeout: timedelta = timedelta(minutes=3)


@dataclass
class CircuitBreaker:
    lim: BreakerLimits = field(default_factory=BreakerLimits)
    state: str = RUN
    reason: str = ""
    last_candle_close: datetime | None = None
    last_heartbeat: datetime | None = None
    _errors: deque = field(default_factory=deque)
    log: list = field(default_factory=list)

    # ------------------------------------------------------------------ transitions
    def _trip(self, state: str, reason: str, now: datetime) -> None:
        order = {RUN: 0, HALT: 1, FLATTEN: 2}
        if order[state] > order[self.state]:                             # never loosen automatically
            self.state, self.reason = state, reason
            self.log.append((now, state, reason))

    def reset(self, now: datetime, who: str) -> None:
        """Manual reset only (an operator action, logged)."""
        self.state, self.reason = RUN, ""
        self._errors.clear()
        self.log.append((now, RUN, f"manual reset by {who}"))

    # ------------------------------------------------------------------ events
    def on_candle(self, close_time: datetime, o: float, h: float, l: float, prev_close: float, atr_5m: float) -> None:
        """A closed 5m candle. atr_5m = ATR(14) of the 14 closed candles BEFORE this one (not including it);
        prev_close = the previous candle's close. Flash move / gap -> FLATTEN; a data gap of >= 2 missed candles -> HALT."""
        now = close_time
        if self.last_candle_close is not None:
            missed = int((close_time - self.last_candle_close) / timedelta(minutes=5)) - 1
            if missed >= self.lim.stale_candles:
                self._trip(HALT, f"stale data: {missed} candles missed before {close_time:%Y-%m-%d %H:%M}", now)
        self.last_candle_close = close_time
        if atr_5m > 0 and (h - l) > self.lim.flash_atr_mult * atr_5m:
            self._trip(FLATTEN, f"flash move: 5m range {(h - l) / atr_5m:.1f} x ATR at {close_time:%H:%M}", now)
        if prev_close > 0 and abs(o / prev_close - 1) > self.lim.flash_gap_pct:
            self._trip(FLATTEN, f"price gap {o / prev_close - 1:+.1%} at {close_time:%H:%M}", now)

    def on_api_error(self, now: datetime, what: str) -> None:
        self._errors.append(now)
        while self._errors and now - self._errors[0] > self.lim.api_window:
            self._errors.popleft()
        if len(self._errors) >= self.lim.api_errors:
            self._trip(HALT, f"{len(self._errors)} API errors in {self.lim.api_window}: {what}", now)

    def on_heartbeat(self, now: datetime) -> None:
        self.last_heartbeat = now

    def on_risk_stop(self, now: datetime, reason: str) -> None:
        self._trip(HALT, reason, now)

    def on_kill_switch(self, now: datetime) -> None:
        self._trip(FLATTEN, "kill switch", now)

    def check_clock(self, now: datetime) -> None:
        """Call every loop: a lost heartbeat (the data / exchange connection) flattens."""
        if self.last_heartbeat is not None and now - self.last_heartbeat > self.lim.heartbeat_timeout:
            self._trip(FLATTEN, f"no heartbeat for {now - self.last_heartbeat}", now)

    # ------------------------------------------------------------------ queries
    @property
    def may_enter(self) -> bool:
        return self.state == RUN

    @property
    def must_flatten(self) -> bool:
        return self.state == FLATTEN


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
