"""
Command line:

  python -m bot check-data
  python -m bot backtest                         # every strategies/*.yaml, full history
  python -m bot backtest strategies/s3_btc_confirm.yaml --start 2022-01-01 --save results
  python -m bot backtest --no-funding --slippage-bps 0   # legacy-like costs, for comparison
  python -m bot shadow                           # daily paper run (refreshes data first)
  python -m bot shadow --reset --backfill-days 90
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from .backtest import buy_and_hold, run_backtest
from .config import ROOT, load_config, load_strategy_spec


def _fmt(v, pct=False):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:+.1%}" if pct else f"{v:.2f}"
    return str(v)


def cmd_check_data(args, cfg):
    from .data import build_dataset, load_klines_5m

    for sym in (cfg.symbol, cfg.btc_symbol):
        _, rep = load_klines_5m(cfg.data_dir, sym)
        print(rep.summary())
        if rep.incomplete_days:
            print("   days with missing 5m bars:", ", ".join(rep.incomplete_days[-10:]))
    bars = build_dataset(cfg)
    print(f"daily bars: {len(bars)}  {bars['day'].iloc[0]} -> {bars['day'].iloc[-1]}")
    print("regime counts:", bars["regime"].value_counts().to_dict())
    no_fund = (bars["funding"].str.len() == 0).sum()
    print(f"days without funding data: {no_fund}")


def cmd_backtest(args, cfg):
    from .data import build_dataset

    costs = cfg.costs
    if args.no_funding:
        costs = replace(costs, funding=False)
    if args.slippage_bps is not None:
        costs = replace(costs, slippage_bps=args.slippage_bps)
    if args.fee is not None:
        costs = replace(costs, taker_fee=args.fee)
    paths = args.strategies or sorted((ROOT / "strategies").glob("*.yaml"))
    bars = build_dataset(cfg)

    rows = []
    for p in paths:
        spec = load_strategy_spec(p)
        res = run_backtest(spec, bars, costs, start=args.start, end=args.end)
        m = res.metrics
        rows.append({"strategy": spec.name, **m})
        if args.save:
            out = Path(args.save) / spec.name
            out.mkdir(parents=True, exist_ok=True)
            res.trades.to_csv(out / "trades.csv", index=False)
            res.days.to_csv(out / "days.csv", index=False)
            (out / "metrics.json").write_text(json.dumps(m, indent=2, default=str))
    start = args.start or (rows[0].get("start") if rows else None)
    bh = buy_and_hold(bars, start, args.end)

    print(f"\ncosts: fee {costs.taker_fee:.4%}/side, slippage {costs.slippage_bps}bps, "
          f"funding {'on' if costs.funding else 'OFF'}")
    hdr = f"{'strategy':22s} {'trades':>6s} {'return':>8s} {'CAGR':>7s} {'maxDD':>7s} {'win':>6s} {'PF':>5s} {'sharpe':>6s} {'funding':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['strategy']:22s} {r['n_trades']:6d} {_fmt(r.get('total_return'), 1):>8s} "
              f"{_fmt(r.get('cagr'), 1):>7s} {_fmt(r.get('max_drawdown'), 1):>7s} "
              f"{_fmt(r.get('win_rate'), 1):>6s} {_fmt(r.get('profit_factor')):>5s} "
              f"{_fmt(r.get('sharpe')):>6s} {_fmt(r.get('funding_paid')):>8s}")
    print(f"{'buy_and_hold ETH':22s} {'':6s} {_fmt(bh['total_return'], 1):>8s} {'':7s} "
          f"{_fmt(bh['max_drawdown'], 1):>7s}   ({bh['start']} -> {bh['end']})")
    print("\nfunding = total funding paid in equity units (start equity = 1.0); negative = received.")
    if args.save:
        pd.DataFrame(rows).to_csv(Path(args.save) / "summary.csv", index=False)
        print(f"saved to {args.save}/")


def cmd_shadow(args, cfg):
    from .shadow import refresh_data, run_all

    if not args.no_refresh:
        try:
            refresh_data(cfg, args.refresh_days)
        except Exception as e:  # keep going on stale data, but say so
            print(f"WARN: data refresh failed ({e}); using data on disk.")
    d = run_all(cfg, reset=args.reset, backfill_days=args.backfill_days, only=args.only)
    print(f"SHADOW (paper only)  agreement: {d['agreement']}")
    for w in d["warnings"]:
        print(f"  WARNING: {w}")
    for s in d["strategies"]:
        pos = f"{s['side']} since {s['entry_day']} ({_fmt(s['unrealized_pct'], 1)})" if s["side"] else "flat"
        order = f"  order: {s['pending_order']['action']} {s['pending_order'].get('side') or ''}" if s["pending_order"] else ""
        print(f"  {s['strategy']:18s} last {s['last_day']}  regime {s['regime']:7s} {pos}  "
              f"equity {s['equity_mtm'] if s['equity_mtm'] is None else round(s['equity_mtm'], 4)}{order}")
    print(f"details: {cfg.shadow_dir / 'latest.json'}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m bot")
    ap.add_argument("--config", default="config.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check-data", help="data quality + coverage report")

    b = sub.add_parser("backtest", help="backtest strategy YAML files")
    b.add_argument("strategies", nargs="*", help="YAML files (default: all in strategies/)")
    b.add_argument("--start")
    b.add_argument("--end")
    b.add_argument("--no-funding", action="store_true")
    b.add_argument("--slippage-bps", type=float)
    b.add_argument("--fee", type=float)
    b.add_argument("--save", help="directory for trades/days/metrics per strategy")

    s = sub.add_parser("shadow", help="daily paper-trading run")
    s.add_argument("--reset", action="store_true", help="start the shadow fresh (deletes shadow_v2 state)")
    s.add_argument("--backfill-days", type=int, default=0)
    s.add_argument("--no-refresh", action="store_true")
    s.add_argument("--refresh-days", type=int, default=10)
    s.add_argument("--only", nargs="*", help="strategy names")

    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    {"check-data": cmd_check_data, "backtest": cmd_backtest, "shadow": cmd_shadow}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
