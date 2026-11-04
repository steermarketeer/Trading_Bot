"""Run the full signal study and write a plain-English report."""
from __future__ import annotations

import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from .indicators import atr
from .outcomes import OutcomeParams, label_outcomes
from .patterns import PATTERN_INFO, PatternParams, detect_patterns
from .signals import SIGNAL_INFO, compute_signals
from .trend import add_weekly_trend, alignment

MIN_N = 30  # below this a success rate means very little


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    ph = k / n
    den = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def prepare_bars(raw: pd.DataFrame) -> pd.DataFrame:
    d = add_weekly_trend(raw)
    d["atr14"] = atr(d, 14)
    return d.reset_index(drop=True)


def build_events(bars: pd.DataFrame, pp: PatternParams, op: OutcomeParams, cost_frac: float) -> pd.DataFrame:
    ev = pd.concat([compute_signals(bars), detect_patterns(bars, pp)], ignore_index=True)
    ev = ev.drop(columns=[c for c in ("level",) if c in ev.columns])
    ev = ev.merge(bars[["day", "weekly_trend", "close", "atr14"]], on="day", how="left")
    ev["alignment"] = [alignment(dr, tr) for dr, tr in zip(ev["direction"], ev["weekly_trend"])]
    ev = label_outcomes(bars, ev, p=op)
    # round-trip fee + slippage expressed in R (ATR units); funding not included
    ev["cost_r"] = cost_frac * ev["entry"] / ev["atr14"]
    ev["r_after_costs"] = ev["r"] - ev["cost_r"]
    return ev.sort_values(["day", "signal"]).reset_index(drop=True)


def add_leverage(ev: pd.DataFrame, leverage: float, cost_frac: float, mmr: float) -> pd.DataFrame:
    """
    Result as a fraction of the margin used, at `leverage`, after fees+slippage (not funding).
    Liquidation (isolated margin) if the worst adverse move reached 1/leverage - maintenance
    before the trade ended -> -100% of margin.
    """
    ev = ev.copy()
    atr_pct = ev["atr14"] / ev["entry"]
    move = ev["r"] * atr_pct                       # price move in the trade's favour
    liq_dist = max(1.0 / leverage - mmr, 0.0)
    liquidated = (ev["mae_r"] * atr_pct) >= liq_dist
    ret = leverage * (move - cost_frac)
    ev["margin_ret"] = np.where(liquidated, -1.0, np.maximum(ret, -1.0))
    ev["liquidated"] = liquidated
    return ev


def build_baseline(bars: pd.DataFrame, op: OutcomeParams, cost_frac: float) -> pd.DataFrame:
    """Every day, both directions: what you'd get from a random entry in the same trend."""
    days = bars[["day"]].copy()
    ev = pd.concat([days.assign(direction=1), days.assign(direction=-1)], ignore_index=True)
    ev["signal"] = "baseline"
    ev = ev.merge(bars[["day", "weekly_trend", "atr14"]], on="day", how="left")
    ev = label_outcomes(bars, ev, p=op)
    ev["r_after_costs"] = ev["r"] - cost_frac * ev["entry"] / ev["atr14"]
    return ev


def _period(df: pd.DataFrame, holdout_start: str, which: str) -> pd.DataFrame:
    done = df[df["outcome"] != "incomplete"]
    return done[done["day"] < holdout_start] if which == "research" else done[done["day"] >= holdout_start]


def summarize(ev: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Per signal x direction x alignment, compared with the baseline in the same weekly trend."""
    b = base[base["weekly_trend"] != "Unknown"]
    bstats = b.groupby(["direction", "weekly_trend"]).agg(
        base_win=("outcome", lambda s: (s == "win").mean()), base_r=("r", "mean")).reset_index()
    rows = []
    for (sig, dr, al), g in ev.groupby(["signal", "direction", "alignment"]):
        n = len(g)
        wins = int((g["outcome"] == "win").sum())
        lo, hi = wilson(wins, n)
        # baseline weighted by where this signal's events actually were
        mix = g.merge(bstats, on=["direction", "weekly_trend"], how="left")
        base_win, base_r = mix["base_win"].mean(), mix["base_r"].mean()
        sd = g["r"].std(ddof=1) if n > 1 else math.nan
        t = (g["r"].mean() - base_r) / (sd / math.sqrt(n)) if n > 1 and sd and sd > 0 else math.nan
        rows.append({
            "signal": sig, "direction": "long" if dr > 0 else "short", "alignment": al, "n": n,
            "win_rate": wins / n, "win_ci_low": lo, "win_ci_high": hi,
            "loss_rate": (g["outcome"] == "loss").mean(), "timeout_rate": (g["outcome"] == "timeout").mean(),
            "avg_r": g["r"].mean(), "avg_r_after_costs": g["r_after_costs"].mean(),
            "baseline_win_rate": base_win, "baseline_avg_r": base_r,
            "edge_r": g["r"].mean() - base_r, "t_vs_baseline": t,
            "avg_days": g["days_to_exit"].mean(),
            "avg_margin_ret": g["margin_ret"].mean() if "margin_ret" in g else math.nan,
            "worst_margin_ret": g["margin_ret"].min() if "margin_ret" in g else math.nan,
            "n_liquidated": int(g["liquidated"].sum()) if "liquidated" in g else 0,
        })
    return pd.DataFrame(rows)


def alignment_summary(ev: pd.DataFrame) -> pd.DataFrame:
    g = ev[ev["alignment"] != "unknown"].groupby("alignment")
    return pd.DataFrame({
        "n": g.size(),
        "win_rate": g["outcome"].apply(lambda s: (s == "win").mean()),
        "avg_r": g["r"].mean(),
    }).reindex(["with", "sideways", "against"])


def baseline_table(base: pd.DataFrame) -> pd.DataFrame:
    b = base[base["weekly_trend"] != "Unknown"]
    g = b.groupby(["weekly_trend", "direction"])
    out = pd.DataFrame({
        "days": g.size(),
        "win_rate": g["outcome"].apply(lambda s: (s == "win").mean()),
        "avg_r": g["r"].mean(),
    }).reset_index()
    out["direction"] = out["direction"].map({1: "long", -1: "short"})
    return out


# ----------------------------------------------------------------------------- report
def _pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.0%}"


def _r(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.2f}"


def _verdict(row) -> str:
    if row["n"] < MIN_N:
        return "too few"
    t = row["t_vs_baseline"]
    if isinstance(t, float) and not math.isnan(t):
        if t >= 2 and row["avg_r_after_costs"] > 0:
            return "**promising**"
        if t <= -2:
            return "worse than random"
    return "no edge"


def _table(df: pd.DataFrame, cols: list[tuple[str, str, callable]]) -> str:
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(f(r[c]) if c else f(r) for c, _, f in cols) + " |" for _, r in df.iterrows()]
    return "\n".join([head, sep, *body])


def write_report(out_dir: Path, ev: pd.DataFrame, base: pd.DataFrame, holdout_start: str,
                 op: OutcomeParams, pp: PatternParams, cost_frac: float, leverage: float = 1.0) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    res_ev, hold_ev = _period(ev, holdout_start, "research"), _period(ev, holdout_start, "holdout")
    res_b, hold_b = _period(base, holdout_start, "research"), _period(base, holdout_start, "holdout")
    res = summarize(res_ev, res_b)
    hold = summarize(hold_ev, hold_b)
    res["verdict"] = res.apply(_verdict, axis=1)

    ev.to_csv(out_dir / "signal_events.csv", index=False)
    res.to_csv(out_dir / "signal_summary_research.csv", index=False)
    hold.to_csv(out_dir / "signal_summary_holdout.csv", index=False)

    s, e = res_ev["day"].min(), res_ev["day"].max()
    info = {**SIGNAL_INFO, **PATTERN_INFO}
    lines = [
        "# Signal study - ETHUSDT daily",
        "",
        f"Research period **{s} -> {e}**. Holdout **{holdout_start} ->** is shown separately and "
        "should only be looked at after choosing signals.",
        "",
        "## How to read this",
        f"- Every time a signal fires, we enter at the **next day's open** with a target of "
        f"**+{op.target_atr:g} ATR** and a stop of **-{op.stop_atr:g} ATR**, and wait up to **{op.max_days} days**.",
        f"- **Win rate** = target reached first. Because the target is {op.target_atr / op.stop_atr:g}x the stop, "
        f"roughly **{op.stop_atr / (op.stop_atr + op.target_atr):.0%} is break-even** (timeouts aside).",
        "- **Avg R** = average result in ATR units (+2 = full win, -1 = full loss). It's the best single measure of edge.",
        "- **Baseline** = entering on *every* day in the same weekly trend and direction. A signal is only useful if it beats this.",
        "- **t** = how far above the baseline, allowing for luck. Above 2 is notable. With this many rows a few will pass by chance, "
        "so confirm them on the holdout before trusting them.",
        f"- Costs: *after costs* subtracts {cost_frac:.2%} round-trip fees and slippage. Funding is not included (it adds about 0.1-0.3% per 20 days in calm markets, more in strong trends).",
        "- If target and stop are both inside the same daily candle, it's counted as a loss.",
        f"- **At {leverage:g}x**: *margin %* = result as a % of the margin used, after fees and slippage. "
        f"With ETH's daily ATR of about 4-5%, a full stop-out (-1 ATR) costs roughly **{leverage * 0.045:.0%} of the margin**, "
        f"and a win (+2 ATR) makes roughly **{leverage * 0.09:.0%}**. Liquidation (about -{1 / leverage:.0%} price move) is counted as -100%.",
        "",
        "## 1. Does the weekly trend matter?",
        "",
        "All signals and patterns together, by whether they agreed with the weekly trend (research period):",
        "",
        _table(alignment_summary(res_ev).reset_index(), [
            ("alignment", "vs weekly trend", str), ("n", "events", str),
            ("win_rate", "win rate", _pct), ("avg_r", "avg R", _r)]),
        "",
        "Baseline: entering on every day, by weekly trend and direction:",
        "",
        _table(baseline_table(res_b), [
            ("weekly_trend", "weekly trend", str), ("direction", "direction", str), ("days", "days", str),
            ("win_rate", "win rate", _pct), ("avg_r", "avg R", _r)]),
        "",
    ]

    promising = res[res["verdict"] == "**promising**"].sort_values("t_vs_baseline", ascending=False)
    lines += ["## 2. Promising (research period, n >= 30, beats baseline with t >= 2, positive after costs)", ""]
    if promising.empty:
        lines += ["Nothing cleared the bar. That's a real result too: these signals alone don't beat random entries.", ""]
    else:
        merged = promising.merge(hold[["signal", "direction", "alignment", "n", "win_rate", "avg_r"]],
                                 on=["signal", "direction", "alignment"], how="left", suffixes=("", "_hold"))
        lines += [_table(merged, [
            ("signal", "signal", str), ("direction", "dir", str), ("alignment", "trend", str),
            ("n", "n", str), ("win_rate", "win", _pct), ("avg_r", "avg R", _r),
            ("avg_r_after_costs", "after costs", _r), ("baseline_avg_r", "baseline R", _r),
            ("t_vs_baseline", "t", lambda x: f"{x:.1f}"),
            ("avg_margin_ret", f"avg margin % @{leverage:g}x", lambda x: f"{x:+.1%}"),
            ("n_hold", "holdout n", lambda x: "-" if pd.isna(x) else str(int(x))),
            ("win_rate_hold", "holdout win", _pct), ("avg_r_hold", "holdout R", _r)]), ""]

    lines += ["## 3. Every signal (research period)", "",
              "Sorted by signal, then direction and trend alignment.", ""]
    res_sorted = res.sort_values(["signal", "direction", "alignment"])
    lines += [_table(res_sorted, [
        ("signal", "signal", str), ("direction", "dir", str), ("alignment", "trend", str), ("n", "n", str),
        ("win_rate", "win", _pct), (None, "win 95% range", lambda r: f"{_pct(r['win_ci_low'])}-{_pct(r['win_ci_high'])}"),
        ("avg_r", "avg R", _r), ("avg_r_after_costs", "after costs", _r), ("baseline_avg_r", "baseline R", _r),
        ("t_vs_baseline", "t", lambda x: "-" if pd.isna(x) else f"{x:.1f}"),
        ("avg_margin_ret", f"margin % @{leverage:g}x", lambda x: f"{x:+.1%}"),
        ("worst_margin_ret", "worst", lambda x: f"{x:+.0%}"), ("verdict", "verdict", str)]), ""]

    lines += ["## 4. Signal definitions", ""]
    lines += [f"- **{k}**: {v}" for k, v in info.items()]
    lines += ["", "## Settings", "", f"- outcome: `{asdict(op)}`", f"- patterns: `{asdict(pp)}`",
              "- weekly trend: Up = weekly close > SMA20w > SMA50w and SMA20w rising over 3 weeks; Down = mirror; "
              "else Sideways (first 53 weeks: Unknown, excluded from trend tables)",
              "", "Raw data: `signal_events.csv` (every event with its outcome), `signal_summary_*.csv`."]
    path = out_dir / "signal_study.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_study(cfg: Config, out_dir: Path, holdout_start: str = "2025-11-01",
              op: OutcomeParams = OutcomeParams(), pp: PatternParams = PatternParams(),
              raw: pd.DataFrame | None = None, leverage: float = 5.0) -> Path:
    from ..data import build_dataset

    raw = raw if raw is not None else build_dataset(cfg)
    bars = prepare_bars(raw)
    cost_frac = 2 * (cfg.costs.taker_fee + cfg.costs.slippage_bps / 10_000)
    ev = add_leverage(build_events(bars, pp, op, cost_frac), leverage, cost_frac, cfg.costs.maintenance_margin)
    base = build_baseline(bars, op, cost_frac)
    return write_report(out_dir, ev, base, holdout_start, op, pp, cost_frac, leverage)


__all__ = ["run_study", "summarize", "wilson", "prepare_bars", "build_events", "build_baseline", "np"]
