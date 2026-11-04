"""Load config.yaml and strategy YAML files."""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Costs:
    taker_fee: float = 0.0004
    slippage_bps: float = 5.0
    funding: bool = True
    maintenance_margin: float = 0.005


@dataclass
class Risk:
    size_frac: float = 1.0          # fraction of equity used as margin per trade
    leverage: float = 1.0
    stop_pct: float | None = None   # protective stop, fraction of entry price (checked intraday)
    cooldown_days: int = 0          # daily closes after an exit with no new entry
    dd_halt: float | None = None    # halt new entries (and exit) when mark-to-market drawdown hits this
    halt_days: int = 30             # how long a halt lasts; peak resets when it ends
    dd_basis: str = "closed"        # "closed": drawdown of closed-trade equity (checked when flat)
                                    # "mtm": mark-to-market incl. open profit (checked daily, exits)


@dataclass
class StrategySpec:
    name: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    risk: Risk = field(default_factory=Risk)
    path: Path | None = None


@dataclass
class Config:
    data_dir: Path
    symbol: str = "ETHUSDT"
    btc_symbol: str = "BTCUSDT"
    costs: Costs = field(default_factory=Costs)
    regime_extra_lag: int = 1
    shadow_dir: Path = ROOT / "shadow_v2"
    shadow_strategies: list[Path] = field(default_factory=list)


def _only_known(cls, raw: dict | None, where: str) -> dict:
    raw = raw or {}
    known = {f.name for f in fields(cls)}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"{where}: unknown keys {sorted(unknown)}; allowed: {sorted(known)}")
    return raw


def _resolve(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def load_config(path: str | Path = "config.yaml") -> Config:
    path = _resolve(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    shadow = raw.get("shadow") or {}
    return Config(
        data_dir=_resolve(raw.get("data_dir", "data")),
        symbol=raw.get("symbol", "ETHUSDT"),
        btc_symbol=raw.get("btc_symbol", "BTCUSDT"),
        costs=Costs(**_only_known(Costs, raw.get("costs"), f"{path.name}: costs")),
        regime_extra_lag=int((raw.get("regime") or {}).get("extra_lag_periods", 1)),
        shadow_dir=_resolve(shadow.get("dir", "shadow_v2")),
        shadow_strategies=[_resolve(p) for p in shadow.get("strategies", [])],
    )


def load_strategy_spec(path: str | Path) -> StrategySpec:
    path = _resolve(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key in ("name", "type"):
        if key not in raw:
            raise ValueError(f"{path.name}: missing '{key}'")
    extra = set(raw) - {"name", "type", "params", "risk", "description"}
    if extra:
        raise ValueError(f"{path.name}: unknown top-level keys {sorted(extra)}")
    return StrategySpec(
        name=raw["name"],
        type=raw["type"],
        params=raw.get("params") or {},
        risk=Risk(**_only_known(Risk, raw.get("risk"), f"{path.name}: risk")),
        path=path,
    )
