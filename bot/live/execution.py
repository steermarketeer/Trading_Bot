"""
Execution handlers. Paper execution fills on 5m candles with exactly the backtests' cost model, so paper results are
comparable with the research numbers. The exchange adapter is an interface with retry / backoff and a market fallback;
it is wired to nothing unless LIVE=1 is set and an adapter is passed in (no keys live in this repository).

Fill model (same as bot/ml/targets.py): market = taker 0.04% + 5 bps slippage per side; a limit target counts as
filled only when price trades LIMIT_BUFFER (0.02%) through it, at maker 0.02%; the stop is checked before the target
inside a candle; a candle that opens through the stop fills at the open.
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Protocol

C_MKT = 0.0009
C_LMT = 0.0002
LIMIT_BUFFER = 0.0002


@dataclass(frozen=True)
class Order:
    key: str
    side: str                      # "long" / "short"
    qty: float
    entry: float                   # the next open (reference price)
    stop: float
    target: float


@dataclass
class Fill:
    key: str
    kind: str                      # "entry" / "stop" / "target" / "flatten"
    price: float
    qty: float
    fee: float
    time: object


class ExecutionHandler(Protocol):
    async def submit(self, order: Order, now) -> Fill: ...
    async def flatten(self, key: str, price: float, now) -> Fill: ...


# ---------------------------------------------------------------------- paper
@dataclass
class PaperExecution:
    """Fills at the reference price with the market cost model; exits are decided by on_candle()."""
    open: dict = field(default_factory=dict)      # key -> Order
    fills: list = field(default_factory=list)

    async def submit(self, order: Order, now) -> Fill:
        d = 1 if order.side == "long" else -1
        px = order.entry * (1 + d * 0.0005)                                # 5 bps slippage against us
        fee = order.qty * px * 0.0004
        f = Fill(order.key, "entry", px, order.qty, fee, now)
        self.open[order.key] = order
        self.fills.append(f)
        return f

    async def flatten(self, key: str, price: float, now) -> Fill:
        o = self.open.pop(key)
        d = 1 if o.side == "long" else -1
        px = price * (1 - d * 0.0005)
        f = Fill(key, "flatten", px, o.qty, o.qty * px * 0.0004, now)
        self.fills.append(f)
        return f

    def on_candle(self, o: float, h: float, l: float, c: float, now) -> list[Fill]:
        """Check every open order against a closed 5m candle: stop first, then the limit target."""
        out = []
        for key, od in list(self.open.items()):
            d = 1 if od.side == "long" else -1
            gap = (o - od.stop) * d <= 0                                    # opened through the stop
            hit_s = gap or (l <= od.stop if d > 0 else h >= od.stop)
            hit_t = (h >= od.target * (1 + LIMIT_BUFFER)) if d > 0 else (l <= od.target * (1 - LIMIT_BUFFER))
            if hit_s:
                px = o if gap else od.stop
                px = px * (1 - d * 0.0005)
                out.append(Fill(key, "stop", px, od.qty, od.qty * px * 0.0004, now))
                self.open.pop(key)
            elif hit_t:
                out.append(Fill(key, "target", od.target, od.qty, od.qty * od.target * 0.0002, now))
                self.open.pop(key)
        self.fills.extend(out)
        return out


# ---------------------------------------------------------------------- exchange adapter (interface + retry logic)
class ExchangeClient(Protocol):
    async def post_only_limit(self, side: str, qty: float, price: float) -> str: ...
    async def market(self, side: str, qty: float) -> str: ...
    async def is_filled(self, order_id: str) -> bool: ...
    async def cancel(self, order_id: str) -> None: ...
    async def set_stop(self, side: str, qty: float, stop: float) -> str: ...


async def with_retry(fn, *args, attempts: int = 4, base: float = 0.5, on_error=None):
    """Exponential backoff with jitter. on_error(exc) is called on each failure (feeds the circuit breaker)."""
    for i in range(attempts):
        try:
            return await fn(*args)
        except Exception as exc:                                           # noqa: BLE001 (network errors of any kind)
            if on_error:
                on_error(exc)
            if i == attempts - 1:
                raise
            await asyncio.sleep(base * (2 ** i) * (1 + random.random() * 0.25))


@dataclass
class ExchangeExecution:
    """Post-only limit at the next open; if not filled within `wait_s`, cancel and take a market order (the backtests
    assume a market entry, so this can only improve on them). Stops are placed on the exchange at once."""
    client: ExchangeClient
    wait_s: float = 20.0
    on_error: object = None

    async def submit(self, order: Order, now) -> Fill:
        oid = await with_retry(self.client.post_only_limit, order.side, order.qty, order.entry, on_error=self.on_error)
        deadline = asyncio.get_event_loop().time() + self.wait_s
        while asyncio.get_event_loop().time() < deadline:
            if await with_retry(self.client.is_filled, oid, on_error=self.on_error):
                await with_retry(self.client.set_stop, order.side, order.qty, order.stop, on_error=self.on_error)
                return Fill(order.key, "entry", order.entry, order.qty, order.qty * order.entry * 0.0002, now)
            await asyncio.sleep(1.0)
        await with_retry(self.client.cancel, oid, on_error=self.on_error)
        await with_retry(self.client.market, order.side, order.qty, on_error=self.on_error)
        await with_retry(self.client.set_stop, order.side, order.qty, order.stop, on_error=self.on_error)
        return Fill(order.key, "entry", order.entry, order.qty, order.qty * order.entry * C_MKT, now)

    async def flatten(self, key: str, price: float, now) -> Fill:
        raise NotImplementedError("wired per adapter: close the position at market, cancel its stop")
