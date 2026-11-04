"""Backtest runner + performance metrics, built on the shared Engine."""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from .config import Costs, Risk, StrategySpec
from .engine import DAY_FIELDS, TRADE_FIELDS, Engine, EngineState, rows_ready
from .strategies import make_strategy


@dataclass
class BacktestResult:
    name: str
    trades: pd.DataFrame
    days: pd.DataFrame
    metrics: dict


def metrics(trades: pd.DataFrame, days: pd.DataFrame) -> dict:
    out: dict = {"n_trades": int(len(trades))}
    if days.empty:
        return out
    eq = days["equity_mtm"].to_numpy(float)
    start, end = days["day"].iloc[0], days["day"].iloc[-1]
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 1e-9)
    total = eq[-1] / 1.0 - 1.0
    out.update({
        "start": start,
        "end": end,
        "total_return": float(total),
        "cagr": float((eq[-1]) ** (1 / years) - 1) if eq[-1] > 0 else -1.0,
        "max_drawdown": float((eq / np.maximum.accumulate(eq) - 1).min()),
        "exposure": float(days["side"].notna().mean()),
    })
    daily_ret = pd.Series(eq).pct_change().dropna()
    out["sharpe"] = float(daily_ret.mean() / daily_ret.std() * np.sqrt(365)) if daily_ret.std() > 0 else 0.0
    if len(trades):
        r = trades["net_return"].to_numpy(float)
        wins, losses = r[r > 0].sum(), -r[r <= 0].sum()
        out.update({
            "win_rate": float((r > 0).mean()),
            "profit_factor": float(wins / losses) if losses > 0 else None,  # None = no losing trades
            "avg_trade": float(r.mean()),
            "best_trade": float(r.max()),
            "worst_trade": float(r.min()),
            "avg_days_held": float(trades["days_held"].mean()),
            "fees_paid": float(trades["fees"].sum()),
            "funding_paid": float(trades["funding"].sum()),
            "n_stops": int(trades["exit_reason"].str.startswith("stop").sum()),
            "n_liquidations": int(trades["exit_reason"].str.startswith("liquidation").sum()),
        })
    return out


def buy_and_hold(bars: pd.DataFrame, start: str | None = None, end: str | None = None) -> dict:
    b = bars
    if start:
        b = b[b["day"] >= start]
    if end:
        b = b[b["day"] <= end]
    eq = b["close"].to_numpy(float) / float(b["open"].iloc[0])
    return {
        "name": "buy_and_hold",
        "start": b["day"].iloc[0], "end": b["day"].iloc[-1],
        "total_return": float(eq[-1] - 1),
        "max_drawdown": float((eq / np.maximum.accumulate(eq) - 1).min()),
    }


def run_backtest(
    spec: StrategySpec,
    bars: pd.DataFrame,
    costs: Costs,
    start: str | None = None,
    end: str | None = None,
    risk: Risk | None = None,
    params: dict | None = None,
) -> BacktestResult:
    """`params` / `risk` override the YAML values (handy for parameter sweeps)."""
    strat = make_strategy(spec.type, spec.name, {**spec.params, **(params or {})})
    eng = Engine(strat, risk or spec.risk, costs)
    rows = rows_ready(strat, strat.prepare(bars))
    rows = [r for r in rows if (not start or r["day"] >= start) and (not end or r["day"] <= end)]
    st = EngineState()
    days, trades = [], []
    for row in rows:
        rec, tr = eng.step(st, row)
        days.append(rec)
        trades.extend(tr)
    if rows:
        t = eng.force_close(st, rows[-1])
        if t:
            trades.append(t)
            days[-1]["equity"] = st.equity
            days[-1]["equity_mtm"] = st.equity
    tdf = pd.DataFrame(trades, columns=TRADE_FIELDS)
    ddf = pd.DataFrame(days, columns=DAY_FIELDS)
    return BacktestResult(spec.name, tdf, ddf, metrics(tdf, ddf))


def with_costs(costs: Costs, **kw) -> Costs:
    return replace(costs, **kw)
