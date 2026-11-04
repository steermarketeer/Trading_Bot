"""
The single trading engine. Backtest, shadow and (later) live all call `Engine.step()`
once per completed daily bar, so they can never disagree about the rules.

Order of events inside one daily bar:
  1. 00:00 UTC funding settlement for a position held overnight
  2. pending order from yesterday's close fills at today's OPEN (+ slippage)
  3. intraday: liquidation / protective stop from today's HIGH/LOW
     (if the open already gapped through the level, fill at the open)
  4. 08:00 and 16:00 UTC funding settlements if still in a position
  5. mark-to-market at the close, drawdown check
  6. strategy decides at the close -> order for tomorrow's open
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import Costs, Risk
from .strategies.base import PositionView, Strategy


@dataclass
class Position:
    side: str
    signal_day: str
    entry_day: str
    entry_price: float
    qty: float              # units of the coin
    margin: float           # equity committed (isolated margin)
    notional: float         # at entry
    equity_before: float
    fees: float = 0.0
    funding: float = 0.0
    days_held: int = 0

    @property
    def dir(self) -> int:
        return 1 if self.side == "long" else -1

    def upnl(self, px: float) -> float:
        return self.qty * (px - self.entry_price) * self.dir


@dataclass
class Pending:
    action: str             # "enter" | "exit"
    side: str | None
    reason: str
    signal_day: str


@dataclass
class EngineState:
    equity: float = 1.0     # realised equity (fees and funding already deducted)
    peak: float = 1.0       # mark-to-market peak, for drawdown halts
    position: Position | None = None
    pending: Pending | None = None
    cooldown_left: int = 0
    halt_left: int = 0
    last_day: str | None = None
    n_trades: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EngineState":
        d = dict(d)
        if d.get("position"):
            d["position"] = Position(**d["position"])
        if d.get("pending"):
            d["pending"] = Pending(**d["pending"])
        return cls(**d)


TRADE_FIELDS = [
    "strategy", "side", "signal_day", "entry_day", "entry_price", "exit_day", "exit_price",
    "exit_reason", "days_held", "leverage", "margin", "notional", "gross_pnl", "fees",
    "funding", "net_pnl", "net_return", "equity_after",
]

DAY_FIELDS = [
    "day", "close", "regime", "side", "equity", "equity_mtm", "drawdown", "actions", "detail",
]


class Engine:
    def __init__(self, strategy: Strategy, risk: Risk, costs: Costs):
        if risk.dd_basis not in ("closed", "mtm"):
            raise ValueError(f"risk.dd_basis must be 'closed' or 'mtm', got {risk.dd_basis!r}")
        self.s = strategy
        self.risk = risk
        self.costs = costs
        self.slip = costs.slippage_bps / 10_000.0

    # ---------------------------------------------------------------- helpers
    def _liq_price(self, pos: Position) -> float | None:
        lev, mmr = self.risk.leverage, self.costs.maintenance_margin
        if lev <= 1.0 and pos.side == "long":
            return None  # 1x long can't be liquidated
        e = pos.entry_price
        if pos.side == "long":
            return e * (1 - 1 / lev) / (1 - mmr)
        return e * (1 + 1 / lev) / (1 + mmr)

    def _stop_price(self, pos: Position) -> float | None:
        sp = self.risk.stop_pct
        if sp is None:
            return None
        return pos.entry_price * (1 - sp * pos.dir)

    def _charge_funding(self, st: EngineState, rate: float, px: float) -> None:
        pos = st.position
        amt = pos.qty * px * rate * pos.dir  # long pays a positive rate
        st.equity -= amt
        pos.funding += amt

    def _open(self, st: EngineState, side: str, px: float, day: str, signal_day: str) -> Position:
        d = 1 if side == "long" else -1
        fill = px * (1 + d * self.slip)
        margin = st.equity * self.risk.size_frac
        notional = margin * self.risk.leverage
        fee = notional * self.costs.taker_fee
        pos = Position(
            side=side, signal_day=signal_day, entry_day=day, entry_price=fill,
            qty=notional / fill, margin=margin, notional=notional,
            equity_before=st.equity, fees=fee,
        )
        st.equity -= fee
        st.position = pos
        return pos

    def _close(self, st: EngineState, px: float, day: str, reason: str, liquidated: bool = False) -> dict:
        pos = st.position
        if liquidated:
            fill = px
            gross = -pos.margin
            fee = 0.0
        else:
            fill = px * (1 - pos.dir * self.slip)
            gross = pos.upnl(fill)
            fee = pos.qty * fill * self.costs.taker_fee
        st.equity += gross - fee
        pos.fees += fee
        net = gross - pos.fees - pos.funding
        st.position = None
        st.cooldown_left = self.risk.cooldown_days
        st.n_trades += 1
        return {
            "strategy": self.s.name, "side": pos.side, "signal_day": pos.signal_day,
            "entry_day": pos.entry_day, "entry_price": pos.entry_price, "exit_day": day,
            "exit_price": fill, "exit_reason": reason, "days_held": pos.days_held,
            "leverage": self.risk.leverage, "margin": pos.margin, "notional": pos.notional,
            "gross_pnl": gross, "fees": pos.fees, "funding": pos.funding, "net_pnl": net,
            "net_return": net / pos.equity_before if pos.equity_before else 0.0,
            "equity_after": st.equity,
        }

    def _intraday_exit(self, st: EngineState, o: float, h: float, l: float, day: str) -> dict | None:
        pos = st.position
        stop, liq = self._stop_price(pos), self._liq_price(pos)
        # whichever level is closer to entry is hit first by an adverse move
        levels = [(p, kind) for p, kind in ((stop, "stop"), (liq, "liquidation")) if p is not None]
        if not levels:
            return None
        if pos.side == "long":
            px, kind = max(levels)
            if l > px:
                return None
            fill = min(o, px)
        else:
            px, kind = min(levels)
            if h < px:
                return None
            fill = max(o, px)
        gap = fill != px
        reason = kind + ("_gap" if gap else "")
        return self._close(st, fill, day, reason, liquidated=(kind == "liquidation"))

    # ------------------------------------------------------------------- step
    def step(self, st: EngineState, row: dict) -> tuple[dict, list[dict]]:
        day = row["day"]
        o, h, l, c = (float(row[k]) for k in ("open", "high", "low", "close"))
        funding = (row.get("funding") or []) if self.costs.funding else []
        actions: list[str] = []
        detail: list[str] = []
        trades: list[dict] = []

        # 1. overnight funding
        if st.position is not None:
            for hr, rate in funding:
                if hr < 0.5:
                    self._charge_funding(st, rate, o)

        # 2. fill yesterday's order at the open
        if st.pending is not None:
            p, st.pending = st.pending, None
            if p.action == "exit" and st.position is not None:
                trades.append(self._close(st, o, day, p.reason))
                actions.append("EXIT")
                detail.append(p.reason)
            elif p.action == "enter" and st.position is None:
                self._open(st, p.side, o, day, p.signal_day)
                actions.append(f"ENTER_{p.side.upper()}")

        # 3. intraday stop / liquidation
        if st.position is not None:
            t = self._intraday_exit(st, o, h, l, day)
            if t is not None:
                trades.append(t)
                actions.append("STOP" if t["exit_reason"].startswith("stop") else "LIQUIDATED")
                detail.append(t["exit_reason"])

        # 4. intraday funding
        if st.position is not None:
            for hr, rate in funding:
                if hr >= 0.5:
                    self._charge_funding(st, rate, c)
            st.position.days_held += 1

        # 5. mark to market + drawdown halt
        pos = st.position
        eq_mtm = st.equity + (pos.upnl(c) if pos else 0.0)
        mtm_basis = self.risk.dd_basis == "mtm"
        if mtm_basis or pos is None:
            st.peak = max(st.peak, eq_mtm)
        dd = eq_mtm / st.peak - 1.0 if st.peak > 0 else 0.0
        if st.halt_left > 0:
            st.halt_left -= 1
            if st.halt_left == 0:
                st.peak = eq_mtm
                actions.append("RESUME")
        elif (
            self.risk.dd_halt is not None
            and (mtm_basis or pos is None)
            and dd <= -abs(self.risk.dd_halt)
        ):
            st.halt_left = max(1, self.risk.halt_days)
            actions.append("HALT")
            detail.append(f"drawdown {dd:.1%}")
            if pos is not None:
                st.pending = Pending("exit", None, "dd_halt", day)

        # 6. strategy decision at the close
        if st.position is not None and st.pending is None:
            pv = PositionView(
                side=pos.side, entry_day=pos.entry_day, entry_price=pos.entry_price,
                days_held=pos.days_held, unrealized_pct=(c / pos.entry_price - 1) * pos.dir,
            )
            reason = self.s.exit_signal(row, pv)
            if reason:
                st.pending = Pending("exit", None, reason, day)
                actions.append("EXIT_ORDER")
                detail.append(reason)
        elif st.position is None and st.pending is None:
            if st.halt_left > 0:
                detail.append(f"halted:{st.halt_left}d")
            elif st.cooldown_left > 0:
                st.cooldown_left -= 1
                detail.append(f"cooldown:{st.cooldown_left + 1}d")
            else:
                side = self.s.entry_signal(row)
                if side:
                    st.pending = Pending("enter", side, "signal", day)
                    actions.append(f"ENTRY_ORDER_{side.upper()}")

        st.last_day = day
        rec = {
            "day": day, "close": c, "regime": row.get("regime"),
            "side": st.position.side if st.position else None,
            "equity": st.equity, "equity_mtm": eq_mtm, "drawdown": dd,
            "actions": "|".join(actions) or ("HOLD" if st.position else "FLAT"),
            "detail": "|".join(detail),
        }
        return rec, trades

    def force_close(self, st: EngineState, row: dict, reason: str = "end_of_data") -> dict | None:
        """Close at this bar's close (backtest end only)."""
        if st.position is None:
            return None
        return self._close(st, float(row["close"]), row["day"], reason)


def rows_ready(strategy: Strategy, bars) -> "list[dict]":
    """Prepared bars as dicts, dropping indicator warm-up rows."""
    req = strategy.required_columns()
    if req:
        bars = bars.dropna(subset=req)
    recs = bars.to_dict("records")
    for r in recs:
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                r[k] = None
    return recs


__all__ = ["Engine", "EngineState", "Position", "Pending", "TRADE_FIELDS", "DAY_FIELDS", "rows_ready", "field"]
