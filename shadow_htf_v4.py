"""
Triple HTF shadow logger — PAPER only (NO Binance orders).

Runs three walk-forward PASS strategies independently:
  S1: both_align_no_stop   (models/htf_v4_winner.json)
  S2: both_cool7_stable7   (models/htf_v5_winner.json)
  S3: both_btc_confirm     (models/htf_v6_s3_winner.json)

Stateless policy: closed trades logged for humans, never as pattern memory.

Usage:
    .\\.venv\\Scripts\\python.exe shadow_htf_v4.py
    .\\.venv\\Scripts\\python.exe shadow_htf_v4.py --bootstrap-s3-only --bootstrap-days 90
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from model_policy import policy_dict
from strategy_htf_trend import FEE, build_daily, load_eth_5m
from strategy_htf_v4_pass import enrich, should_exit
from strategy_htf_v5_search import Cfg5, enrich_with_btc, want_side5

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"
SHADOW_DIR = ROOT / "shadow"
LATEST_PATH = SHADOW_DIR / "latest.json"
RUN_HISTORY_PATH = SHADOW_DIR / "run_history.jsonl"

STRATEGIES = [
    {
        "id": "s1",
        "label": "strategy_1",
        "winner_path": MODELS_DIR / "htf_v4_winner.json",
        "dir_name": "s1_both_align_no_stop",
    },
    {
        "id": "s2",
        "label": "strategy_2",
        "winner_path": MODELS_DIR / "htf_v5_winner.json",
        "dir_name": "s2_both_cool7_stable7",
    },
    {
        "id": "s3",
        "label": "strategy_3",
        "winner_path": MODELS_DIR / "htf_v6_s3_winner.json",
        "dir_name": "s3_both_btc_confirm",
    },
]


def load_cfg(path: Path) -> Cfg5:
    raw = json.loads(path.read_text(encoding="utf-8"))["winner"]
    return Cfg5(
        name=raw["name"],
        mode=raw["mode"],
        entry_sma=int(raw.get("entry_sma", 50)),
        exit_sma=int(raw["exit_sma"]),
        align=bool(raw.get("align", True)),
        regime_stable=int(raw.get("regime_stable", 5)),
        stop_pct=raw.get("stop_pct"),
        dd_halt=raw.get("dd_halt"),
        cooldown=int(raw.get("cooldown", 5)),
        atr_max=raw.get("atr_max"),
        atr_min=raw.get("atr_min"),
        btc_confirm=bool(raw.get("btc_confirm", False)),
    )


def default_state(cfg: Cfg5) -> dict:
    return {
        "strategy": cfg.name,
        "mode": "SHADOW_PAPER_ONLY",
        "places_orders": False,
        "model_policy": policy_dict()["name"],
        "side": None,
        "entry_price": None,
        "entry_time": None,
        "equity": 1.0,
        "peak": 1.0,
        "halted": False,
        "cooldown_left": 0,
        "last_processed_day": None,
        "n_signals": 0,
        "n_trades_closed": 0,
        "updated_at": None,
    }


def load_state(path: Path, cfg: Cfg5) -> dict:
    if path.exists():
        st = json.loads(path.read_text(encoding="utf-8"))
        for k in list(st.keys()):
            if any(tok in k.lower() for tok in ("pattern", "streak", "last_50", "profile")):
                del st[k]
        return st
    return default_state(cfg)


def save_state(path: Path, st: dict) -> None:
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(st, indent=2), encoding="utf-8")


def append_csv(path: Path, row: dict) -> None:
    df = pd.DataFrame([row])
    if path.exists():
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)


def refresh_data(days: int) -> None:
    cmd = [sys.executable, str(ROOT / "refresh_recent_data.py"), "--days", str(days)]
    print("Refreshing recent klines...")
    subprocess.check_call(cmd, cwd=str(ROOT))


def unrealized(side: str | None, entry: float | None, px: float) -> float | None:
    if side is None or entry is None or entry <= 0:
        return None
    if side == "long":
        return (px - entry) / entry
    return (entry - px) / entry


def migrate_legacy_s1(s1_dir: Path) -> None:
    s1_dir.mkdir(parents=True, exist_ok=True)
    for name in ("state.json", "signals.csv", "trades.csv"):
        src = SHADOW_DIR / name
        dest = s1_dir / name
        if src.exists() and not dest.exists():
            shutil.move(str(src), str(dest))
            print(f"Migrated {name} -> {dest.relative_to(SHADOW_DIR)}")


def process_bar(
    st: dict,
    cfg: Cfg5,
    row: pd.Series,
    signals_path: Path,
    trades_path: Path,
    fee: float = FEE,
) -> list[dict]:
    events = []
    day = pd.Timestamp(row["open_time"]).strftime("%Y-%m-%d")
    px = float(row["close"])
    regime = str(row["regime_lag"])
    close_lag = float(row["close_lag"])
    sma_entry = float(row[f"sma{cfg.entry_sma}_lag"])
    sma_exit = float(row[f"sma{cfg.exit_sma}_lag"])
    sma20 = float(row["sma20_lag"])
    atr_pct = float(row["atr_pct_lag"])
    stable = int(row["regime_stable_days"])
    btc_regime = str(row.get("btc_regime_lag", "Neutral"))
    btc_close_lag = float(row["btc_close_lag"]) if "btc_close_lag" in row.index else close_lag
    btc_sma50_lag = float(row["btc_sma50_lag"]) if "btc_sma50_lag" in row.index else sma_entry

    if st["halted"] and cfg.dd_halt is not None and st["peak"] > 0:
        dd = (st["equity"] - st["peak"]) / st["peak"]
        if dd > -0.5 * abs(cfg.dd_halt):
            st["halted"] = False
            events.append({"day": day, "action": "RESUME", "detail": "dd_halt cleared", "price": px})

    if st["cooldown_left"] > 0 and st["side"] is None:
        st["cooldown_left"] -= 1

    side = st["side"]

    if side is not None:
        entry_px = float(st["entry_price"])
        stopped = False
        if cfg.stop_pct is not None:
            if side == "long" and px <= entry_px * (1.0 - cfg.stop_pct):
                stopped = True
            if side == "short" and px >= entry_px * (1.0 + cfg.stop_pct):
                stopped = True
        exit_now = stopped or should_exit(side, regime, close_lag, sma_exit)
        if exit_now:
            reason = "stop" if stopped else "rule"
            gross = ((px - entry_px) / entry_px) if side == "long" else ((entry_px - px) / entry_px)
            net = gross - 2.0 * fee
            append_csv(trades_path, {
                "entry_time": st["entry_time"],
                "exit_time": day,
                "side": side,
                "entry_price": entry_px,
                "exit_price": px,
                "net_return": net,
                "exit_reason": reason,
                "strategy": cfg.name,
                "mode": "SHADOW_PAPER",
            })
            st["equity"] *= (1.0 + net)
            st["peak"] = max(st["peak"], st["equity"])
            st["n_trades_closed"] = int(st.get("n_trades_closed", 0)) + 1
            if cfg.dd_halt is not None and st["peak"] > 0:
                dd = (st["equity"] - st["peak"]) / st["peak"]
                if dd <= -abs(cfg.dd_halt):
                    st["halted"] = True
            events.append({
                "day": day, "action": "EXIT", "side": side, "reason": reason,
                "price": px, "net_return": net, "equity": st["equity"],
            })
            st["side"] = None
            st["entry_price"] = None
            st["entry_time"] = None
            st["cooldown_left"] = cfg.cooldown
            side = None

    if side is None:
        skip = None
        if st["halted"]:
            skip = "dd_halt"
        elif st["cooldown_left"] > 0:
            skip = f"cooldown:{st['cooldown_left']}"
        elif stable < cfg.regime_stable:
            skip = f"regime_stable:{stable}<{cfg.regime_stable}"
        elif cfg.atr_max is not None and atr_pct > cfg.atr_max:
            skip = "atr_high"
        elif cfg.atr_min is not None and atr_pct < cfg.atr_min:
            skip = "atr_low"
        else:
            w = want_side5(
                cfg, regime, close_lag, sma_entry, sma20,
                btc_regime, btc_close_lag, btc_sma50_lag,
            )
            if w is not None:
                st["side"] = w
                st["entry_price"] = px
                st["entry_time"] = day
                events.append({
                    "day": day, "action": "ENTER", "side": w,
                    "price": px, "regime": regime, "equity": st["equity"],
                })
            else:
                skip = "no_setup"
        if skip and not events:
            events.append({
                "day": day, "action": "HOLD_FLAT",
                "detail": skip, "price": px, "regime": regime,
                "side": None, "equity": st["equity"],
            })
    else:
        if not events:
            u = unrealized(st["side"], st["entry_price"], px)
            events.append({
                "day": day, "action": "HOLD", "side": st["side"],
                "price": px, "unrealized": u, "regime": regime, "equity": st["equity"],
            })

    st["last_processed_day"] = day
    st["n_signals"] = int(st.get("n_signals", 0)) + len(events)
    for ev in events:
        append_csv(signals_path, {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "strategy": cfg.name,
            "day": ev.get("day"),
            "action": ev.get("action"),
            "side": ev.get("side"),
            "price": ev.get("price"),
            "regime": ev.get("regime"),
            "detail": ev.get("detail") or ev.get("reason"),
            "net_return": ev.get("net_return"),
            "unrealized": ev.get("unrealized"),
            "equity": ev.get("equity", st["equity"]),
            "mode": "SHADOW_PAPER_ONLY",
        })
    return events


def run_one_strategy(
    meta: dict,
    daily: pd.DataFrame,
    bootstrap_days: int,
    force_bootstrap: bool,
) -> dict:
    cfg = load_cfg(meta["winner_path"])
    out_dir = SHADOW_DIR / meta["dir_name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "state.json"
    signals_path = out_dir / "signals.csv"
    trades_path = out_dir / "trades.csv"

    print("-" * 60)
    print(f"{meta['label'].upper()}  ({cfg.name})" + (" [BTC confirm]" if cfg.btc_confirm else ""))
    print("-" * 60)

    st = load_state(state_path, cfg)
    st["strategy"] = cfg.name
    st["mode"] = "SHADOW_PAPER_ONLY"
    st["places_orders"] = False

    last = st.get("last_processed_day")
    if last is None or force_bootstrap:
        if bootstrap_days > 0 or force_bootstrap:
            n = max(bootstrap_days, 1)
            start_idx = max(0, len(daily) - n)
            todo = daily.iloc[start_idx:].copy()
            st = default_state(cfg)
            print(f"  Bootstrap: last {len(todo)} days")
        else:
            todo = daily.iloc[[-1]].copy()
            print(f"  First run: latest day {todo['open_time'].iloc[0].date()}")
    else:
        last_ts = pd.Timestamp(last, tz="UTC")
        todo = daily[daily["open_time"] > last_ts].copy()
        print(f"  New days since {last}: {len(todo)}")

    latest_px = float(daily.iloc[-1]["close"])
    if todo.empty:
        save_state(state_path, st)
        return {
            "id": meta["id"],
            "label": meta["label"],
            "strategy": cfg.name,
            "btc_confirm": cfg.btc_confirm,
            "status": "UP_TO_DATE",
            "last_processed_day": st.get("last_processed_day"),
            "side": st.get("side"),
            "entry_price": st.get("entry_price"),
            "entry_time": st.get("entry_time"),
            "equity": st.get("equity"),
            "peak": st.get("peak"),
            "halted": st.get("halted"),
            "cooldown_left": st.get("cooldown_left"),
            "n_trades_closed": st.get("n_trades_closed"),
            "unrealized": unrealized(st.get("side"), st.get("entry_price"), latest_px),
            "processed_days": 0,
            "events_count": 0,
            "dir": str(out_dir),
        }

    all_events = []
    for _, row in todo.iterrows():
        evs = process_bar(st, cfg, row, signals_path, trades_path)
        all_events.extend(evs)
        for e in evs:
            if e.get("action") in ("ENTER", "EXIT", "RESUME"):
                print(
                    f"  {e.get('day')} {e.get('action'):10s} "
                    f"side={e.get('side')} px={e.get('price')} "
                    f"{e.get('detail') or e.get('reason') or ''}"
                )

    save_state(state_path, st)
    last_row = todo.iloc[-1]
    return {
        "id": meta["id"],
        "label": meta["label"],
        "strategy": cfg.name,
        "btc_confirm": cfg.btc_confirm,
        "status": "UPDATED",
        "last_processed_day": st.get("last_processed_day"),
        "side": st.get("side"),
        "entry_price": st.get("entry_price"),
        "entry_time": st.get("entry_time"),
        "equity": st.get("equity"),
        "peak": st.get("peak"),
        "halted": st.get("halted"),
        "cooldown_left": st.get("cooldown_left"),
        "n_trades_closed": st.get("n_trades_closed"),
        "unrealized": unrealized(st.get("side"), st.get("entry_price"), float(last_row["close"])),
        "processed_days": int(len(todo)),
        "events_count": len(all_events),
        "regime": str(last_row["regime_lag"]),
        "dir": str(out_dir),
    }


def agreement(summaries: list[dict]) -> dict:
    sides = {s["id"]: s.get("side") for s in summaries}
    active = {k: v for k, v in sides.items() if v is not None}
    if not active:
        label = "all_flat"
    elif len(set(active.values())) == 1 and len(active) == len(sides):
        label = f"all_agree_{next(iter(active.values()))}"
    elif len(set(active.values())) == 1:
        label = f"active_agree_{next(iter(active.values()))}"
    elif len(active) == 1:
        label = "one_active"
    else:
        label = "disagree"
    return {"label": label, "sides": sides, "n_active": len(active)}


def append_run_history(record: dict) -> None:
    """Append one JSON line per shadow invocation (success or failure)."""
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    with RUN_HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Triple HTF shadow logger (paper only)")
    ap.add_argument("--no-refresh", action="store_true")
    ap.add_argument("--refresh-days", type=int, default=10)
    ap.add_argument("--bootstrap-days", type=int, default=0)
    ap.add_argument("--force-bootstrap", action="store_true")
    ap.add_argument("--bootstrap-s2-only", action="store_true")
    ap.add_argument("--bootstrap-s3-only", action="store_true",
                    help="bootstrap only strategy 3 (keep s1/s2 state)")
    args = ap.parse_args()
    started = datetime.now(timezone.utc).isoformat()

    try:
        SHADOW_DIR.mkdir(parents=True, exist_ok=True)
        for meta in STRATEGIES:
            if not meta["winner_path"].exists():
                raise SystemExit(f"Missing {meta['winner_path']}")

        migrate_legacy_s1(SHADOW_DIR / STRATEGIES[0]["dir_name"])

        print("=" * 60)
        print("TRIPLE HTF SHADOW — PAPER ONLY (no exchange orders)")
        print("S1: both_align_no_stop | S2: both_cool7_stable7 | S3: both_btc_confirm")
        print(f"Policy: {policy_dict()['name']} (patterns blank)")
        print("=" * 60)

        if not args.no_refresh:
            try:
                refresh_data(args.refresh_days)
            except Exception as e:
                print(f"WARN: refresh failed ({e}); continuing with on-disk data.")

        daily = enrich_with_btc(enrich(build_daily(load_eth_5m())))
        today = pd.Timestamp(datetime.now(timezone.utc).date(), tz="UTC")
        daily = daily[daily["open_time"] < today].reset_index(drop=True)
        if daily.empty:
            raise SystemExit("No completed daily bars available.")

        summaries = []
        for meta in STRATEGIES:
            force = args.force_bootstrap
            boot = args.bootstrap_days
            if args.bootstrap_s3_only:
                if meta["id"] == "s3":
                    force = True
                    boot = boot or 90
                else:
                    force = False
                    boot = 0
            elif args.bootstrap_s2_only:
                if meta["id"] == "s2":
                    force = True
                    boot = boot or 90
                else:
                    force = False
                    boot = 0
            summaries.append(run_one_strategy(meta, daily, boot, force))

        agree = agreement(summaries)
        run_at = datetime.now(timezone.utc).isoformat()
        digest = {
            "status": "TRIPLE_SHADOW",
            "run_at_utc": run_at,
            "places_orders": False,
            "mode": "SHADOW_PAPER_ONLY",
            "model_policy": policy_dict(),
            "agreement": agree,
            "latest_close": float(daily.iloc[-1]["close"]),
            "strategies": summaries,
            "how_to_read": {
                "s1": "shadow/s1_both_align_no_stop/",
                "s2": "shadow/s2_both_cool7_stable7/",
                "s3": "shadow/s3_both_btc_confirm/",
                "combined": "shadow/latest.json",
                "run_history": "shadow/run_history.jsonl",
            },
        }
        LATEST_PATH.write_text(json.dumps(digest, indent=2), encoding="utf-8")
        for s in summaries:
            (SHADOW_DIR / f"latest_{s['id']}.json").write_text(
                json.dumps(s, indent=2), encoding="utf-8"
            )

        append_run_history({
            "run_at_utc": run_at,
            "started_at_utc": started,
            "ok": True,
            "error": None,
            "places_orders": False,
            "mode": "SHADOW_PAPER_ONLY",
            "agreement": agree.get("label"),
            "sides": agree.get("sides"),
            "n_active": agree.get("n_active"),
            "latest_close": float(daily.iloc[-1]["close"]),
            "last_processed_day": max(
                (s.get("last_processed_day") or "" for s in summaries), default=""
            ) or None,
            "processed_days_total": int(sum(int(s.get("processed_days") or 0) for s in summaries)),
            "strategies": [
                {
                    "id": s.get("id"),
                    "strategy": s.get("strategy"),
                    "status": s.get("status"),
                    "side": s.get("side"),
                    "equity": s.get("equity"),
                    "n_trades_closed": s.get("n_trades_closed"),
                    "last_processed_day": s.get("last_processed_day"),
                    "processed_days": s.get("processed_days"),
                    "regime": s.get("regime"),
                    "btc_confirm": s.get("btc_confirm"),
                }
                for s in summaries
            ],
        })

        print("\n=== COMBINED DIGEST ===")
        print(f"agreement: {agree['label']}  sides={agree['sides']}")
        for s in summaries:
            print(
                f"  {s['id']} {s['strategy']}: side={s['side']} equity={s['equity']:.4f} "
                f"trades={s['n_trades_closed']} last={s['last_processed_day']} [{s['status']}]"
            )
        print(f"\nWrote {LATEST_PATH}")
        print(f"Appended {RUN_HISTORY_PATH}")
    except SystemExit as e:
        msg = str(e) if e.code not in (0, None) else None
        if msg:
            append_run_history({
                "run_at_utc": datetime.now(timezone.utc).isoformat(),
                "started_at_utc": started,
                "ok": False,
                "error": msg,
                "places_orders": False,
                "mode": "SHADOW_PAPER_ONLY",
            })
        raise
    except Exception as e:
        append_run_history({
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "started_at_utc": started,
            "ok": False,
            "error": str(e),
            "places_orders": False,
            "mode": "SHADOW_PAPER_ONLY",
        })
        raise


if __name__ == "__main__":
    main()
