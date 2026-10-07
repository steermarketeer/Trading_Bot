"""
Visibility helpers for SHADOW DESK — decision gates, ops health, open positions.
Does not place orders. Not used as model features.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SHADOW = ROOT / "shadow"
MODELS = ROOT / "models"
ORDERBOOK = ROOT / "data" / "orderbook"
KLINES_ETH = ROOT / "data" / "klines" / "ETHUSDT_5m.csv"

WINNERS = {
    "s1": MODELS / "htf_v4_winner.json",
    "s2": MODELS / "htf_v5_winner.json",
    "s3": MODELS / "htf_v6_s3_winner.json",
}

FOLDERS = {
    "s1": "s1_both_align_no_stop",
    "s2": "s2_both_cool7_stable7",
    "s3": "s3_both_btc_confirm",
}


def load_winner(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["winner"]


def build_market_daily() -> pd.DataFrame:
    """Completed daily bars with regime/SMA/BTC lags (same path as shadow)."""
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from strategy_htf_trend import build_daily, load_eth_5m
    from strategy_htf_v4_pass import enrich
    from strategy_htf_v5_search import enrich_with_btc

    daily = enrich_with_btc(enrich(build_daily(load_eth_5m())))
    today = pd.Timestamp(datetime.now(timezone.utc).date(), tz="UTC")
    daily = daily[daily["open_time"] < today].reset_index(drop=True)
    return daily


def last_signal_row(strategy_id: str) -> dict | None:
    path = SHADOW / FOLDERS[strategy_id] / "signals.csv"
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        try:
            df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return None
    if df.empty:
        return None
    return df.iloc[-1].to_dict()


def _gate(name: str, ok: bool, detail: str) -> dict:
    return {"gate": name, "ok": bool(ok), "detail": detail}


def evaluate_decision(cfg: dict, row: pd.Series, summary: dict) -> dict:
    """Explain why flat or what sustains an open side on the last processed day."""
    regime = str(row.get("regime_lag", "Neutral"))
    stable = int(row.get("regime_stable_days", 0))
    need_stable = int(cfg.get("regime_stable", 5))
    close_lag = float(row["close_lag"])
    entry_sma_n = int(cfg.get("entry_sma", 50))
    exit_sma_n = int(cfg.get("exit_sma", 30))
    sma_entry = float(row[f"sma{entry_sma_n}_lag"])
    sma_exit = float(row[f"sma{exit_sma_n}_lag"])
    sma20 = float(row["sma20_lag"])
    atr = float(row.get("atr_pct_lag", 0.0))
    btc_reg = str(row.get("btc_regime_lag", "Neutral"))
    btc_close = float(row["btc_close_lag"]) if "btc_close_lag" in row.index else close_lag
    btc_sma = float(row["btc_sma50_lag"]) if "btc_sma50_lag" in row.index else sma_entry
    align = bool(cfg.get("align", True))
    btc_confirm = bool(cfg.get("btc_confirm", False))
    atr_max = cfg.get("atr_max")
    atr_min = cfg.get("atr_min")

    side = summary.get("side")
    halted = bool(summary.get("halted"))
    cooldown = int(summary.get("cooldown_left") or 0)
    px = float(summary.get("entry_price") or row.get("close") or close_lag)

    gates: list[dict] = []
    gates.append(_gate("halted", not halted, "clear" if not halted else "DD halt active"))
    gates.append(_gate(
        "cooldown",
        cooldown <= 0 or side is not None,
        "ready" if cooldown <= 0 else f"{cooldown}d left",
    ))
    gates.append(_gate(
        "regime",
        regime in ("Bull", "Bear"),
        f"{regime} (need Bull or Bear)",
    ))
    gates.append(_gate(
        "regime_stable",
        stable >= need_stable,
        f"{stable}/{need_stable} days",
    ))
    if atr_max is not None:
        gates.append(_gate("atr_max", atr <= float(atr_max), f"{atr:.4f} <= {atr_max}"))
    if atr_min is not None:
        gates.append(_gate("atr_min", atr >= float(atr_min), f"{atr:.4f} >= {atr_min}"))

    long_setup = regime == "Bull" and close_lag > sma_entry
    short_setup = regime == "Bear" and close_lag < sma_entry
    if align:
        long_setup = long_setup and (sma20 > sma_entry)
        short_setup = short_setup and (sma20 < sma_entry)
    gates.append(_gate(
        "sma_setup",
        long_setup or short_setup,
        f"close_lag={close_lag:.2f} entrySMA{entry_sma_n}={sma_entry:.2f} sma20={sma20:.2f}",
    ))

    if btc_confirm:
        btc_long_ok = btc_close > btc_sma
        btc_short_ok = btc_close < btc_sma
        if long_setup:
            btc_ok = btc_long_ok
        elif short_setup:
            btc_ok = btc_short_ok
        else:
            btc_ok = False
        gates.append(_gate(
            "btc_confirm",
            btc_ok,
            f"btc_reg={btc_reg} btc_close={btc_close:.2f} btc_sma50={btc_sma:.2f}",
        ))
    else:
        gates.append(_gate("btc_confirm", True, "not required"))

    # Desired side if flat (mirrors want_side5 roughly)
    want = None
    if not halted and cooldown <= 0 and stable >= need_stable:
        if atr_max is not None and atr > float(atr_max):
            want = None
        elif atr_min is not None and atr < float(atr_min):
            want = None
        elif long_setup:
            want = "long"
            if btc_confirm and not (btc_close > btc_sma):
                want = None
        elif short_setup:
            want = "short"
            if btc_confirm and not (btc_close < btc_sma):
                want = None

    blocking = [g["gate"] for g in gates if not g["ok"]]
    if side:
        # exit pressure
        exit_regime = (side == "long" and regime != "Bull") or (side == "short" and regime != "Bear")
        exit_sma = (side == "long" and close_lag < sma_exit) or (side == "short" and close_lag > sma_exit)
        verdict = "IN_POSITION"
        reason = f"holding {side}"
        if exit_regime or exit_sma:
            verdict = "EXIT_PRESSURE"
            bits = []
            if exit_regime:
                bits.append(f"regime={regime}")
            if exit_sma:
                bits.append(f"vs exitSMA{exit_sma_n}")
            reason = "exit pressure: " + ", ".join(bits)
    elif want:
        verdict = "WOULD_ENTER"
        reason = f"setup allows {want}"
    elif blocking:
        verdict = "BLOCKED"
        reason = "blocked by " + ", ".join(blocking)
    else:
        verdict = "NO_SETUP"
        reason = "no directional setup"

    entry_px = summary.get("entry_price")
    unreal = summary.get("unrealized")
    if side and entry_px and row.get("close"):
        ep = float(entry_px)
        last = float(row["close"])
        if side == "long":
            unreal = (last - ep) / ep
        else:
            unreal = (ep - last) / ep

    days_held = None
    if side and summary.get("entry_time") and summary.get("last_processed_day"):
        try:
            a = pd.Timestamp(summary["entry_time"])
            b = pd.Timestamp(summary["last_processed_day"])
            days_held = int((b - a).days)
        except Exception:
            days_held = None

    return {
        "id": summary.get("id"),
        "strategy": cfg.get("name"),
        "verdict": verdict,
        "reason": reason,
        "side": side,
        "want": want,
        "gates": gates,
        "regime": regime,
        "stable": stable,
        "need_stable": need_stable,
        "close": float(row.get("close", close_lag)),
        "close_lag": close_lag,
        "sma_entry": sma_entry,
        "sma_exit": sma_exit,
        "sma20": sma20,
        "entry_price": entry_px,
        "entry_time": summary.get("entry_time"),
        "unrealized": unreal,
        "days_held": days_held,
        "exit_sma_n": exit_sma_n,
        "btc_confirm": btc_confirm,
        "blocking": blocking,
    }


def decisions_for_latest(latest: dict, daily: pd.DataFrame) -> list[dict]:
    if daily.empty or not latest:
        return []
    # map last_processed_day -> row; fallback last row
    out = []
    for s in latest.get("strategies", []):
        sid = s.get("id")
        if sid not in WINNERS or not WINNERS[sid].exists():
            continue
        cfg = load_winner(WINNERS[sid])
        day = s.get("last_processed_day")
        row = None
        if day:
            mask = daily["open_time"].dt.strftime("%Y-%m-%d") == str(day)
            if mask.any():
                row = daily.loc[mask].iloc[-1]
        if row is None:
            row = daily.iloc[-1]
        out.append(evaluate_decision(cfg, row, s))
    return out


def agreement_timeline(limit_days: int = 60) -> pd.DataFrame:
    """Build agreement-by-day from signal files."""
    frames = []
    for sid, folder in FOLDERS.items():
        path = SHADOW / folder / "signals.csv"
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            try:
                df = pd.read_csv(path, engine="python", on_bad_lines="skip")
            except Exception:
                continue
        if df.empty or "day" not in df.columns:
            continue
        tmp = df.copy()
        tmp["strategy_id"] = sid.upper()
        sort_col = "ts_utc" if "ts_utc" in tmp.columns else tmp.columns[0]
        tmp = tmp.sort_values(sort_col).groupby("day", as_index=False).tail(1)
        if "side" not in tmp.columns:
            tmp["side"] = None
        frames.append(tmp[["day", "strategy_id", "side", "action", "price", "regime"]])
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)
    long["side"] = long["side"].fillna("flat").astype(str).replace({"nan": "flat", "None": "flat"})
    sides = long.pivot_table(index="day", columns="strategy_id", values="side", aggfunc="last")

    def _agree(row):
        vals = [str(v).lower() for v in row.values if pd.notna(v) and str(v).lower() not in ("nan", "none", "")]
        active = [v for v in vals if v != "flat"]
        if not active:
            return "all_flat"
        if len(set(active)) == 1 and len(active) == len(vals):
            return f"all_agree_{active[0]}"
        if len(set(active)) == 1:
            return f"active_agree_{active[0]}"
        if len(active) == 1:
            return "one_active"
        return "disagree"

    regime = long.groupby("day")["regime"].last()
    close = long.groupby("day")["price"].last()
    out = sides.copy()
    out["agreement"] = sides.apply(_agree, axis=1)
    out["regime"] = regime
    out["close"] = close
    out = out.reset_index().sort_values("day", ascending=False).head(limit_days)
    return out


def regime_price_strip(limit_days: int = 45) -> pd.DataFrame:
    path = SHADOW / FOLDERS["s1"] / "signals.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except Exception:
        try:
            df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()
    if df.empty or "day" not in df.columns:
        return pd.DataFrame()
    sort_col = "ts_utc" if "ts_utc" in df.columns else df.columns[0]
    g = df.sort_values(sort_col).groupby("day", as_index=False).tail(1)
    cols = [c for c in ["day", "regime", "price", "action", "side"] if c in g.columns]
    return g[cols].sort_values("day", ascending=False).head(limit_days)


def scheduler_status() -> dict:
    """Best-effort Windows Task Scheduler probe for ETH Shadow HTF."""
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$i=Get-ScheduledTaskInfo -TaskName 'ETH Shadow HTF' -ErrorAction Stop; "
                "[pscustomobject]@{LastRun=$i.LastRunTime.ToString('s'); "
                "LastResult=('0x{0:X}' -f [uint32]$i.LastTaskResult); "
                "NextRun=$i.NextRunTime.ToString('s'); State=(Get-ScheduledTask -TaskName 'ETH Shadow HTF').State} "
                "| ConvertTo-Json -Compress"
            ),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if proc.returncode != 0 or not proc.stdout.strip():
            return {"available": False, "error": (proc.stderr or "task not found")[:200]}
        data = json.loads(proc.stdout)
        ok = str(data.get("LastResult", "")).lower() in ("0x0", "0")
        return {
            "available": True,
            "ok": ok,
            "last_run": data.get("LastRun"),
            "last_result": data.get("LastResult"),
            "next_run": data.get("NextRun"),
            "state": data.get("State"),
        }
    except Exception as e:
        return {"available": False, "error": str(e)[:200]}


def orderbook_age_seconds() -> float | None:
    if not ORDERBOOK.exists():
        return None
    files = list(ORDERBOOK.glob("*_depth*_*.csv.gz"))
    if not files:
        return None
    newest = max(files, key=lambda p: p.stat().st_mtime)
    # prefer parsing last ts from newest file; fallback mtime
    try:
        df = pd.read_csv(newest, compression="gzip", usecols=["ts_utc"])
        if not df.empty:
            last = pd.to_datetime(df["ts_utc"].iloc[-1], utc=True)
            return max(0.0, (pd.Timestamp.now(tz="UTC") - last).total_seconds())
    except Exception:
        pass
    mtime = datetime.fromtimestamp(newest.stat().st_mtime, tz=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - mtime).total_seconds())


def ops_health(latest: dict | None) -> dict:
    runs_path = SHADOW / "run_history.jsonl"
    last_run_ok = None
    last_run_at = None
    if runs_path.exists():
        lines = [ln for ln in runs_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            try:
                rec = json.loads(lines[-1])
                last_run_ok = rec.get("ok")
                last_run_at = rec.get("run_at_utc")
            except json.JSONDecodeError:
                pass
    if latest and not last_run_at:
        last_run_at = latest.get("run_at_utc")

    klines_age = None
    if KLINES_ETH.exists():
        mtime = datetime.fromtimestamp(KLINES_ETH.stat().st_mtime, tz=timezone.utc)
        klines_age = max(0.0, (datetime.now(timezone.utc) - mtime).total_seconds())

    ob_age = orderbook_age_seconds()
    sched = scheduler_status()

    def _age_label(sec: float | None) -> str:
        if sec is None:
            return "—"
        if sec < 120:
            return f"{sec:.0f}s"
        if sec < 3600:
            return f"{sec/60:.1f}m"
        if sec < 86400:
            return f"{sec/3600:.1f}h"
        return f"{sec/86400:.1f}d"

    return {
        "shadow_last_run": last_run_at,
        "shadow_last_ok": last_run_ok,
        "scheduler": sched,
        "orderbook_age_s": ob_age,
        "orderbook_age": _age_label(ob_age),
        "klines_age_s": klines_age,
        "klines_age": _age_label(klines_age),
        "last_processed": (
            max((s.get("last_processed_day") or "" for s in (latest or {}).get("strategies", [])), default="")
            or None
        ),
    }
