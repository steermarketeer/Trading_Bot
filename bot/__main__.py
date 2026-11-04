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
        risk = replace(spec.risk, leverage=args.leverage) if args.leverage else None
        res = run_backtest(spec, bars, costs, start=args.start, end=args.end, risk=risk)
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
    if args.leverage:
        print(f"leverage override: {args.leverage:g}x")
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


def cmd_study(args, cfg):
    from .study.outcomes import OutcomeParams
    from .study.run import run_study

    op = OutcomeParams(target_atr=args.target_atr, stop_atr=args.stop_atr, max_days=args.max_days)
    path = run_study(cfg, Path(args.out), holdout_start=args.holdout_start, op=op, leverage=args.leverage)
    print(f"report: {path}")


def cmd_failures(args, cfg):
    from .study.failures import run_failures

    out = Path(args.out)
    path = run_failures(cfg, out / "signal_events.csv", out, holdout_start=args.holdout_start,
                        leverage=args.leverage)
    print(f"report: {path}")


def cmd_indicators(args, cfg):
    from .study.indicator_search import run_indicator_search

    path = run_indicator_search(cfg, Path(args.out), holdout_start=args.holdout_start)
    print(f"report: {path}")


def cmd_sr(args, cfg):
    from .study.sr_study import run_sr_study

    print(f"report: {run_sr_study(cfg, Path(args.out), leverage=args.leverage)}")


def cmd_sr2(args, cfg):
    from .study.sr2_run import run_sr2

    print(f"report: {run_sr2(cfg, Path(args.out), timeframes=tuple(args.tf))}")


def cmd_concepts(args, cfg):
    from .study.concepts_run import run_concepts

    rep = "concept_study.md" if tuple(args.tf) == ("4h", "1D") else f"concept_study_{'_'.join(args.tf)}.md"
    print(f"report: {run_concepts(cfg, Path(args.out), timeframes=tuple(args.tf), report=rep)}")


def cmd_scoring(args, cfg):
    from .study.scoring import run_scoring

    tfs = tuple(args.tf)
    tag = "" if tfs == ("4h", "1D") else "_" + "_".join(tfs)
    print(f"report: {run_scoring(cfg, Path(args.out), tfs=tfs, tag=tag)}")


def cmd_exits(args, cfg):
    from .study.exits import run_exits

    print(f"report: {run_exits(cfg, Path(args.out))}")


def cmd_smalltf(args, cfg):
    from .study.smalltf import run_smalltf

    print(f"report: {run_smalltf(cfg, Path(args.out))}")


def cmd_level_tests(args, cfg):
    from .study.level_tests import run_level_tests

    print(f"report: {run_level_tests(cfg, Path(args.out), timeframes=tuple(args.tf))}")


def cmd_strategy_eval(args, cfg):
    from .study.strategy_eval import run_strategy_eval

    print(f"report: {run_strategy_eval(cfg, Path(args.out))}")


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
    b.add_argument("--leverage", type=float, help="override every strategy's risk.leverage")

    s = sub.add_parser("shadow", help="daily paper-trading run")
    s.add_argument("--reset", action="store_true", help="start the shadow fresh (deletes shadow_v2 state)")
    s.add_argument("--backfill-days", type=int, default=0)
    s.add_argument("--no-refresh", action="store_true")
    s.add_argument("--refresh-days", type=int, default=10)
    s.add_argument("--only", nargs="*", help="strategy names")

    st = sub.add_parser("study", help="signal & pattern study vs the weekly trend")
    st.add_argument("--out", default="reports")
    st.add_argument("--holdout-start", default="2025-11-01")
    st.add_argument("--target-atr", type=float, default=2.0)
    st.add_argument("--stop-atr", type=float, default=1.0)
    st.add_argument("--max-days", type=int, default=20)
    st.add_argument("--leverage", type=float, default=5.0)

    fa = sub.add_parser("failures", help="multi-timeframe autopsy of study trades (run `study` first)")
    fa.add_argument("--out", default="reports")
    fa.add_argument("--holdout-start", default="2025-11-01")
    fa.add_argument("--leverage", type=float, default=5.0)

    ind = sub.add_parser("indicators", help="which indicators catch failures (run `study` and `failures` first)")
    ind.add_argument("--out", default="reports")
    ind.add_argument("--holdout-start", default="2025-11-01")

    sr = sub.add_parser("sr-study", help="support/resistance reversal study with volume & structure")
    sr.add_argument("--out", default="reports")
    sr.add_argument("--leverage", type=float, default=5.0)

    s2 = sub.add_parser("sr2", help="S/R v2: bounce, retests, breakouts, 1h/4h/1D, ML filter")
    s2.add_argument("--out", default="reports")
    s2.add_argument("--tf", nargs="*", default=["1h", "4h", "1D"])

    cc = sub.add_parser("concepts", help="structure / trendlines / liquidity / zones + indicator matrix")
    cc.add_argument("--out", default="reports")
    cc.add_argument("--tf", nargs="*", default=["4h", "1D"])

    sc = sub.add_parser("scoring", help="combined concept+indicator score with certainty 1-10 (run `concepts` first)")
    sc.add_argument("--out", default="reports")
    sc.add_argument("--tf", nargs="*", default=["4h", "1D"])

    ex = sub.add_parser("exits", help="exit-rule study on 5m data (run `concepts` and `scoring` first)")
    ex.add_argument("--out", default="reports")

    stf = sub.add_parser("smalltf", help="1h/2h/4h/1D certainty trades: 1:1 vs 1.5:1 vs 2:1, account sim")
    stf.add_argument("--out", default="reports")

    lt = sub.add_parser("level-tests", help="repeated tests of S/R: break vs massive reversal")
    lt.add_argument("--out", default="reports")
    lt.add_argument("--tf", nargs="*", default=["2h", "4h", "1D"])

    se = sub.add_parser("strategy-eval", help="2:1 fixes + combined strategy (breakouts + 1D 4th-test bounce)")
    se.add_argument("--out", default="reports")

    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    {"check-data": cmd_check_data, "backtest": cmd_backtest, "shadow": cmd_shadow, "study": cmd_study, "failures": cmd_failures, "indicators": cmd_indicators, "sr-study": cmd_sr, "sr2": cmd_sr2, "concepts": cmd_concepts, "scoring": cmd_scoring, "exits": cmd_exits, "smalltf": cmd_smalltf, "level-tests": cmd_level_tests, "strategy-eval": cmd_strategy_eval}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
