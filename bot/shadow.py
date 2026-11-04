"""
Paper-trading shadow on the shared Engine. No exchange orders.

Each strategy gets shadow_v2/<name>/ with:
  state.json   engine state + metadata (resumable)
  trades.csv   closed paper trades (fixed schema, `source` = backfill | forward)
  days.csv     one row per processed day (fixed schema)
And shadow_v2/latest.json summarises all strategies.

Rows for days that had already closed when the shadow was (re)started are tagged
`backfill`; only `forward` rows are real out-of-sample evidence.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import Config, StrategySpec, load_strategy_spec
from .engine import DAY_FIELDS, TRADE_FIELDS, Engine, EngineState, rows_ready
from .strategies import make_strategy

SHADOW_TRADE_FIELDS = TRADE_FIELDS + ["source"]
SHADOW_DAY_FIELDS = DAY_FIELDS + ["source"]


def _fingerprint(spec: StrategySpec, cfg: Config) -> str:
    blob = json.dumps(
        {"type": spec.type, "params": spec.params, "risk": spec.risk.__dict__,
         "costs": cfg.costs.__dict__, "regime_lag": cfg.regime_extra_lag},
        sort_keys=True, default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def _append(path: Path, fields: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def refresh_data(cfg: Config, days: int = 10) -> None:
    from .refresh import refresh_all

    refresh_all(cfg.data_dir, [cfg.symbol, cfg.btc_symbol], days)


def staleness_warnings(cfg: Config, bars: pd.DataFrame, today: str) -> list[str]:
    """Warn when the data the shadow relies on is out of date."""
    warns = []
    last_day = bars["day"].iloc[-1]
    gap = (pd.Timestamp(today) - pd.Timestamp(last_day)).days
    if gap > 1:
        warns.append(f"candles end {last_day}, {gap - 1} completed day(s) missing - refresh data")
    with_funding = bars[bars["funding"].str.len() > 0]
    if len(with_funding) and with_funding["day"].iloc[-1] < last_day:
        warns.append(f"funding data ends {with_funding['day'].iloc[-1]} - funding not charged after that")
    return warns


def run_strategy(
    spec: StrategySpec,
    cfg: Config,
    bars: pd.DataFrame,
    reset: bool = False,
    backfill_days: int = 0,
    today: str | None = None,
) -> dict:
    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = cfg.shadow_dir / spec.name
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "state.json"
    fp = _fingerprint(spec, cfg)

    strat = make_strategy(spec.type, spec.name, spec.params)
    eng = Engine(strat, spec.risk, cfg.costs)
    rows = rows_ready(strat, strat.prepare(bars))
    rows = [r for r in rows if r["day"] < today]  # completed days only
    if not rows:
        raise SystemExit("No completed daily bars available.")

    if reset or not state_path.exists():
        for f in ("trades.csv", "days.csv"):
            (out_dir / f).unlink(missing_ok=True)
        meta = {"created_at": datetime.now(timezone.utc).isoformat(), "forward_from": today, "fingerprint": fp}
        st = EngineState()
        todo = rows[-max(backfill_days, 1):]
    else:
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        meta = saved["meta"]
        if meta.get("fingerprint") != fp:
            raise SystemExit(
                f"{spec.name}: strategy/costs changed since this shadow started "
                f"({meta.get('fingerprint')} -> {fp}). Re-run with --reset to start a fresh shadow."
            )
        st = EngineState.from_dict(saved["engine"])
        todo = [r for r in rows if st.last_day is None or r["day"] > st.last_day]

    day_rows, trade_rows = [], []
    for row in todo:
        src = "forward" if row["day"] >= meta["forward_from"] else "backfill"
        rec, trades = eng.step(st, row)
        day_rows.append({**rec, "source": src})
        trade_rows.extend({**t, "source": src} for t in trades)

    _append(out_dir / "days.csv", SHADOW_DAY_FIELDS, day_rows)
    _append(out_dir / "trades.csv", SHADOW_TRADE_FIELDS, trade_rows)
    state_path.write_text(
        json.dumps({"meta": meta, "engine": st.to_dict(), "updated_at": datetime.now(timezone.utc).isoformat()},
                   indent=2, default=str),
        encoding="utf-8",
    )

    last = rows[-1]
    pos = st.position
    return {
        "strategy": spec.name,
        "processed_days": len(todo),
        "last_day": st.last_day,
        "close": last["close"],
        "regime": last["regime"],
        "side": pos.side if pos else None,
        "entry_day": pos.entry_day if pos else None,
        "entry_price": pos.entry_price if pos else None,
        "unrealized_pct": ((last["close"] / pos.entry_price - 1) * pos.dir) if pos else None,
        "pending_order": st.pending.__dict__ if st.pending else None,
        "equity_mtm": day_rows[-1]["equity_mtm"] if day_rows else None,
        "equity": st.equity,
        "n_trades": st.n_trades,
        "halted_days_left": st.halt_left,
        "cooldown_left": st.cooldown_left,
        "checklist": {k: (v.item() if hasattr(v, "item") else v) for k, v in strat.explain(last).items()},
        "forward_from": meta["forward_from"],
    }


def run_all(cfg: Config, reset: bool = False, backfill_days: int = 0, only: list[str] | None = None,
            bars: pd.DataFrame | None = None) -> dict:
    from .data import build_dataset

    bars = bars if bars is not None else build_dataset(cfg)
    summaries = []
    for path in cfg.shadow_strategies:
        spec = load_strategy_spec(path)
        if only and spec.name not in only:
            continue
        summaries.append(run_strategy(spec, cfg, bars, reset=reset, backfill_days=backfill_days))
    sides = {s["strategy"]: s["side"] for s in summaries}
    active = [v for v in sides.values() if v]
    agreement = (
        "all_flat" if not active
        else f"all_{active[0]}" if len(active) == len(sides) and len(set(active)) == 1
        else "disagree" if len(set(active)) > 1
        else f"partial_{active[0]}"
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    digest = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "warnings": staleness_warnings(cfg, bars, today),
        "mode": "SHADOW_PAPER_ONLY",
        "places_orders": False,
        "agreement": agreement,
        "sides": sides,
        "strategies": summaries,
    }
    cfg.shadow_dir.mkdir(parents=True, exist_ok=True)
    (cfg.shadow_dir / "latest.json").write_text(json.dumps(digest, indent=2, default=str), encoding="utf-8")
    with (cfg.shadow_dir / "run_history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: digest[k] for k in ("run_at_utc", "agreement", "sides", "warnings")}) + "\n")
    return digest
