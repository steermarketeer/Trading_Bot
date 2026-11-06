"""
Risk manager: the non-negotiable layer between a signal and an order. Pure logic, no I/O, unit-tested.

Sizing is fixed-fractional on the price-action stop (q = r * E / |entry - stop|), capped by leverage; the stop is the
setup's own stop (never a fixed % or an ATR multiple). Limits: daily / weekly loss stops, total exposure, 1-day VaR,
one position per move. The Chandelier trailing stop is implemented but OFF by default (see docs/architecture.md 2):
every early exit tested so far lowered the average R; it must pass the 2022 - 25 test before it is switched on.
"""
from __future__ import annotations

from dataclasses import dataclass, field

Z_99 = 2.326                       # one-sided 99% normal quantile


@dataclass(frozen=True)
class RiskLimits:
    risk_frac: dict = field(default_factory=lambda: {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02})
    default_risk_frac: float = 0.02
    lev_cap: float = 5.0           # q * entry <= lev_cap * equity
    daily_stop: float = 0.04       # halt new entries when today's loss >= 4% of the day's opening equity
    weekly_stop: float = 0.08
    max_exposure: float = 5.0      # sum of open notional <= max_exposure * equity
    var_cap: float = 0.35          # 1-day VaR(99%) of the open book <= var_cap * equity. At ETH's usual daily
                                   # volatility (~3%) this equals the 5x leverage cap; in higher volatility it bites
                                   # first and cuts size (2.326 * 6% * 5x would be 70%)
    min_stop_pct: float = 0.006    # strategy rule: stop at least 0.6% away
    chandelier_on: bool = False
    chandelier_k: float = 3.0
    chandelier_arm_r: float = 1.0  # trail only after the trade reached +1R


@dataclass(frozen=True)
class Signal:
    setup: str
    side: str                      # "long" / "short"
    entry: float
    stop: float
    target: float
    tf: str
    decision_time: object = None   # pd.Timestamp of the closing candle

    @property
    def d(self) -> int:
        return 1 if self.side == "long" else -1

    @property
    def stop_pct(self) -> float:
        return abs(self.entry - self.stop) / self.entry


@dataclass
class OpenPosition:
    key: str                       # "<decision_time>|<side>": one position per move
    side: str
    qty: float
    entry: float
    stop: float
    target: float
    sigma_daily: float             # ATR_1D / price at entry (for VaR)
    best_r: float = 0.0            # best open R reached (for Chandelier arming)


@dataclass
class AccountState:
    equity: float                  # realised + unrealised (mark-to-market), supplied by the live loop every candle
    day_open_equity: float
    week_open_equity: float
    positions: dict = field(default_factory=dict)     # key -> OpenPosition
    halted_reason: str | None = None                  # daily latch (cleared by roll_day)
    weekly_halt: str | None = None                    # weekly latch (cleared by roll_week); independent of the daily


@dataclass(frozen=True)
class Decision:
    ok: bool
    reason: str
    qty: float = 0.0
    notional: float = 0.0


class RiskManager:
    def __init__(self, limits: RiskLimits = RiskLimits()):
        self.lim = limits

    # ------------------------------------------------------------------ sizing
    def size(self, sig: Signal, equity: float) -> tuple[float, float]:
        """Quantity and notional for the signal: risk fraction of equity over the stop distance, leverage-capped."""
        dist = abs(sig.entry - sig.stop)
        if dist <= 0 or equity <= 0:
            return 0.0, 0.0
        r = self.lim.risk_frac.get(sig.setup, self.lim.default_risk_frac)
        qty = r * equity / dist
        notional = qty * sig.entry
        cap = self.lim.lev_cap * equity
        if notional > cap:
            qty, notional = cap / sig.entry, cap
        return qty, notional

    # ------------------------------------------------------------------ checks
    def check(self, sig: Signal, st: AccountState, sigma_daily: float) -> Decision:
        """Evaluate a signal against every limit. sigma_daily = ATR_1D / price (for VaR)."""
        self.mark(st)                                                     # evaluate both latches first
        if st.weekly_halt:
            return Decision(False, f"halted: {st.weekly_halt}")
        if st.halted_reason:
            return Decision(False, f"halted: {st.halted_reason}")
        if (sig.entry - sig.stop) * sig.d <= 0:
            return Decision(False, "stop is not beyond the entry")
        if (sig.target - sig.entry) * sig.d <= 0:
            return Decision(False, "target is not beyond the entry")
        if sig.setup != "1D bounce" and sig.stop_pct < self.lim.min_stop_pct:   # strategy rule: breakouts only
            return Decision(False, f"stop {sig.stop_pct:.2%} < minimum {self.lim.min_stop_pct:.2%}")
        key = f"{sig.decision_time}|{sig.side}"
        if key in st.positions:
            return Decision(False, "one position per move: already in this move")
        qty, notional = self.size(sig, st.equity)
        if qty <= 0:
            return Decision(False, "zero size")
        # exposure and VaR caps cut the size (never raise it); a cut below 25% of the planned size is a rejection
        planned = notional
        room = self.lim.max_exposure * st.equity - sum(p.qty * p.entry for p in st.positions.values())
        notional = min(notional, max(0.0, room))
        var_room = self.lim.var_cap * st.equity - self.var_99(st)
        if sigma_daily > 0:
            notional = min(notional, max(0.0, var_room) / (Z_99 * sigma_daily))
        if notional < 0.25 * planned:
            return Decision(False, f"caps leave {notional / planned:.0%} of the planned size (exposure / VaR)")
        qty = notional / sig.entry
        note = "ok" if notional == planned else f"ok (size cut to {notional / planned:.0%} by the exposure / VaR caps)"
        return Decision(True, note, qty, notional)

    def var_99(self, st: AccountState) -> float:
        """1-day 99% VaR of the open book (positions treated as fully correlated: one coin)."""
        return sum(p.qty * p.entry * Z_99 * p.sigma_daily for p in st.positions.values())

    # ------------------------------------------------------------------ stops while open
    def update_stop(self, pos: OpenPosition, bar_high: float, bar_low: float, bar_close: float, atr_daily: float,
                    hh: float, ll: float) -> float:
        """The stop to use after a closed candle. Chandelier (if on and armed) only ever tightens the stop.
        hh / ll = highest high / lowest low since entry (closed candles)."""
        d = 1 if pos.side == "long" else -1
        risk = abs(pos.entry - pos.stop)
        if risk > 0:
            r_now = (bar_high - pos.entry) / risk if d > 0 else (pos.entry - bar_low) / risk
            pos.best_r = max(pos.best_r, r_now)
        if not self.lim.chandelier_on or pos.best_r < self.lim.chandelier_arm_r or atr_daily <= 0:
            return pos.stop
        trail = hh - self.lim.chandelier_k * atr_daily if d > 0 else ll + self.lim.chandelier_k * atr_daily
        new = max(pos.stop, trail) if d > 0 else min(pos.stop, trail)
        pos.stop = new
        return new

    # ------------------------------------------------------------------ day / week roll
    @staticmethod
    def roll_day(st: AccountState) -> None:
        st.day_open_equity = st.equity
        st.halted_reason = None                                           # the daily latch only

    @staticmethod
    def roll_week(st: AccountState) -> None:
        st.week_open_equity = st.equity
        st.weekly_halt = None                                             # the weekly latch only

    def mark(self, st: AccountState) -> None:
        """Call after every equity update (equity = realised + unrealised): trips the daily and the weekly latch
        independently, even when no signal arrives. A latch stays until its own roll (not on a recovery)."""
        day_loss = 1 - st.equity / st.day_open_equity if st.day_open_equity > 0 else 0.0
        week_loss = 1 - st.equity / st.week_open_equity if st.week_open_equity > 0 else 0.0
        if day_loss >= self.lim.daily_stop and not st.halted_reason:
            st.halted_reason = f"daily stop: down {day_loss:.1%} today"
        if week_loss >= self.lim.weekly_stop and not st.weekly_halt:
            st.weekly_halt = f"weekly stop: down {week_loss:.1%} this week"
