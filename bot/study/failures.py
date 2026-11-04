"""
Why did trades fail? Multi-timeframe autopsy of every study trade + a reality check of the
"20% per week" goal. Writes reports/failure_analysis.md and charts in reports/failures/.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data import load_klines_5m
from .mtf import HINTS, TIMEFRAMES, hint_columns, hints_at, resample

MIN_N = 30


def unique_trades(events: pd.DataFrame) -> pd.DataFrame:
    """Signals firing on the same day in the same direction are ONE trade (same entry, same outcome)."""
    ev = events[events["outcome"].isin(["win", "loss", "timeout"])].copy()
    sigs = ev.groupby(["day", "direction"])["signal"].apply(lambda s: ",".join(sorted(set(s))))
    t = ev.drop_duplicates(["day", "direction"]).set_index(["day", "direction"])
    t["signals"] = sigs
    t = t.reset_index()
    t["entry_time"] = pd.to_datetime(t["day"], utc=True) + pd.Timedelta(days=1)
    return t


def _pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.0%}"


def _table(df: pd.DataFrame, cols) -> str:
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(f(r[c]) for c, _, f in cols) + " |" for _, r in df.iterrows()]
    return "\n".join([head, sep, *body])


def opposition_table(t: pd.DataFrame, hint: str = "trend") -> pd.DataFrame:
    cols = [f"{tf}_{hint}" for tf in TIMEFRAMES]
    opp = (t[cols] < 0).sum(axis=1)
    g = t.assign(opp=opp).groupby("opp")
    return pd.DataFrame({
        "trades": g.size(), "fail_rate": g["outcome"].apply(lambda s: (s == "loss").mean()),
        "win_rate": g["outcome"].apply(lambda s: (s == "win").mean()), "avg_r": g["r"].mean(),
    }).reset_index()


def hint_table(res: pd.DataFrame, hold: pd.DataFrame) -> pd.DataFrame:
    base_fail = (res["outcome"] == "loss").mean()
    rows = []
    for col in hint_columns():
        warn = res[col] < 0
        n = int(warn.sum())
        if n < MIN_N:
            continue
        fail_when = (res.loc[warn, "outcome"] == "loss").mean()
        fail_else = (res.loc[~warn, "outcome"] == "loss").mean()
        hw = hold[col] < 0
        rows.append({
            "timeframe": col.split("_", 1)[0], "hint": col.split("_", 1)[1], "n_warned": n,
            "share_of_losses": (res.loc[res["outcome"] == "loss", col] < 0).mean(),
            "share_of_wins": (res.loc[res["outcome"] == "win", col] < 0).mean(),
            "fail_when_warned": fail_when, "fail_otherwise": fail_else, "lift": fail_when - base_fail,
            "avg_r_when_warned": res.loc[warn, "r"].mean(), "avg_r_otherwise": res.loc[~warn, "r"].mean(),
            "hold_n": int(hw.sum()),
            "hold_fail_when_warned": (hold.loc[hw, "outcome"] == "loss").mean() if hw.any() else math.nan,
            "hold_fail_otherwise": (hold.loc[~hw, "outcome"] == "loss").mean() if (~hw).any() else math.nan,
        })
    return pd.DataFrame(rows).sort_values("lift", ascending=False)


def weekly_reality(df5: pd.DataFrame, leverage: float, goal: float = 0.20) -> dict:
    w = resample(df5, "W-MON")
    ret = w["close"] / w["open"] - 1
    best_move = np.maximum(w["high"] / w["open"] - 1, 1 - w["low"] / w["open"])  # perfect hindsight
    need = goal / leverage
    return {
        "weeks": len(w),
        "need_move": need,
        "share_close_move": float((ret.abs() >= need).mean()),
        "share_best_move": float((best_move >= need).mean()),
        "median_abs_week": float(ret.abs().median()),
        "goal_year_multiple": (1 + goal) ** 52,
    }


def plot_trade(df5: pd.DataFrame, trade: pd.Series, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    et = trade["entry_time"]
    # (label, resample rule, candles before entry, candles after entry ~ the 20-day trade window)
    panels = [("4h", "4h", 60, 126), ("1D", "1D", 60, 21), ("1W", "W-MON", 40, 4)]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))
    for ax, (label, rule, n_before, after) in zip(axes, panels):
        b = resample(df5, rule)
        i = int((b["close_time"] <= et).sum())  # candles fully closed at entry
        seg = b.iloc[max(0, i - n_before): i + after]
        x = np.arange(len(seg))
        up = seg["close"] >= seg["open"]
        ax.vlines(x, seg["low"], seg["high"], color="#888", linewidth=0.8)
        ax.bar(x[up], (seg["close"] - seg["open"])[up], bottom=seg["open"][up], color="#2a9d8f", width=0.7)
        ax.bar(x[~up], (seg["close"] - seg["open"])[~up], bottom=seg["open"][~up], color="#e76f51", width=0.7)
        ema50 = seg["close"].ewm(span=50, adjust=False).mean()
        ax.plot(x, ema50, color="#264653", linewidth=1, label="EMA50")
        k = i - max(0, i - n_before)
        ax.axvline(k - 0.5, color="black", linestyle="--", linewidth=1)
        ax.axhline(trade["entry"], color="#457b9d", linewidth=0.8)
        d = trade["direction"]
        ax.axhline(trade["entry"] + d * 2 * trade["atr14"], color="#2a9d8f", linestyle=":", linewidth=1)
        ax.axhline(trade["entry"] - d * 1 * trade["atr14"], color="#e76f51", linestyle=":", linewidth=1)
        ax.set_title(f"{label} (dashed line = entry; dotted = target/stop)", fontsize=9)
        ax.set_xticks([])
    side = "LONG" if trade["direction"] > 0 else "SHORT"
    fig.suptitle(f"{trade['day']}  {side}  {trade['signals']}  -> {trade['outcome']}  "
                 f"(weekly trend {trade['weekly_trend']})", fontsize=10)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=90)
    plt.close(fig)


def run_failures(cfg: Config, events_csv: Path, out_dir: Path, holdout_start: str = "2025-11-01",
                 max_days: int = 20, leverage: float = 5.0, n_charts: int = 8) -> Path:
    events = pd.read_csv(events_csv)
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    trades = hints_at(df5, unique_trades(events))
    cut = (pd.Timestamp(holdout_start) - pd.Timedelta(days=max_days)).strftime("%Y-%m-%d")
    res = trades[trades["day"] < cut]
    hold = trades[trades["day"] >= holdout_start]
    trades.to_csv(out_dir / "trades_with_hints.csv", index=False)

    n, fails = len(trades), int((trades["outcome"] == "loss").sum())
    by_year = trades.groupby(trades["day"].str[:4])["outcome"].value_counts().unstack(fill_value=0)
    by_year["fail_rate"] = by_year.get("loss", 0) / by_year.sum(axis=1)

    losses = res[res["outcome"] == "loss"]
    fast = (losses["days_to_exit"] <= 2).mean()
    right_first = (losses["mfe_r"] >= 1.0).mean()

    opp_trend = opposition_table(res, "trend")
    warn_cols = hint_columns()
    res = res.assign(n_warnings=(res[warn_cols] < 0).sum(axis=1))
    wq = pd.qcut(res["n_warnings"], 4, duplicates="drop")
    warn_tbl = res.groupby(wq, observed=True).agg(
        trades=("r", "size"), fail_rate=("outcome", lambda s: (s == "loss").mean()),
        avg_r=("r", "mean")).reset_index()
    warn_tbl["n_warnings"] = [f"{int(math.floor(iv.left)) + 1}-{int(iv.right)}" for iv in warn_tbl["n_warnings"]]
    hints = hint_table(res, hold)
    reality = weekly_reality(df5, leverage)

    chart_dir = out_dir / "failures"
    sample = losses.assign(n_warnings=(losses[warn_cols] < 0).sum(axis=1)).sort_values(
        "n_warnings", ascending=False).head(n_charts)
    chart_files = []
    for _, tr in sample.iterrows():
        f = chart_dir / f"{tr['day']}_{'long' if tr['direction'] > 0 else 'short'}.png"
        plot_trade(df5, tr, f)
        chart_files.append(f.name)

    L = [
        "# Failure analysis - why did trades fail?",
        "",
        "Trades = the signal-study entries (next-day open, +2 ATR target, -1 ATR stop, 20 days). "
        "Signals that fired on the same day in the same direction are counted as **one** trade.",
        "",
        "## 1. How many failed",
        "",
        f"**{fails} of {n} trades failed ({fails / n:.0%})**, {int((trades['outcome'] == 'win').sum())} won, "
        f"{int((trades['outcome'] == 'timeout').sum())} timed out. With a 2:1 target the break-even fail rate is about 67%.",
        "",
        _table(by_year.reset_index().rename(columns={"day": "year"}), [
            ("year", "year", str), ("loss", "failed", lambda x: str(int(x))), ("win", "won", lambda x: str(int(x))),
            ("timeout", "timeout", lambda x: str(int(x))), ("fail_rate", "fail rate", _pct)]),
        "",
        f"How the failures happened (research period, {len(losses)} failures):",
        f"- **{fast:.0%} failed within 2 days** of entry: the move against us started almost immediately.",
        f"- **{right_first:.0%} were right first**: price went at least +1 ATR our way before turning and hitting the stop.",
        "",
        "## 2. Were the other timeframes pointing the other way?",
        "",
        "For each trade: on how many of the 10 timeframes (15m ... 1W) was price on the **wrong side of its EMA50**?",
        "",
        _table(opp_trend, [("opp", "timeframes against", lambda x: str(int(x))), ("trades", "trades", lambda x: str(int(x))),
                           ("fail_rate", "fail rate", _pct), ("win_rate", "win rate", _pct),
                           ("avg_r", "avg R", lambda x: f"{x:+.2f}")]),
        "",
        "All 90 hints together (9 hints x 10 timeframes), trades grouped by how many warned against them:",
        "",
        _table(warn_tbl, [("n_warnings", "warnings against the trade", str), ("trades", "trades", str),
                          ("fail_rate", "fail rate", _pct), ("avg_r", "avg R", lambda x: f"{x:+.2f}")]),
        "",
        "## 3. Which warnings came before failures?",
        "",
        f"Each row: when this hint pointed **against** the trade, how often did it fail, vs when it didn't? "
        f"Research period, warnings present in at least {MIN_N} trades. **Holdout** columns are later, unseen data: "
        "a warning is only believable if it also shows up there.",
        "",
        _table(hints.head(20), [
            ("timeframe", "TF", str), ("hint", "hint", str), ("n_warned", "trades warned", str),
            ("fail_when_warned", "fail if warned", _pct), ("fail_otherwise", "fail if not", _pct),
            ("avg_r_when_warned", "R if warned", lambda x: f"{x:+.2f}"),
            ("avg_r_otherwise", "R if not", lambda x: f"{x:+.2f}"),
            ("hold_n", "holdout n", str), ("hold_fail_when_warned", "holdout fail if warned", _pct),
            ("hold_fail_otherwise", "holdout fail if not", _pct)]),
        "",
        "Hint meanings: **trend** close vs EMA50 · **slope** EMA20 direction · **macd** histogram sign · "
        "**macd_fade** histogram shrinking 2 candles · **rsi_ext** RSI >70 (long) / <30 (short) · "
        "**cloud** Ichimoku cloud side · **bb_ext** close outside Bollinger band · **stretch** >2 ATR from EMA20 · "
        "**diverge** price at 20-candle extreme while RSI isn't.",
        "",
        "With 90 hints tested, a few will look meaningful by chance. Trust a hint only if the holdout agrees.",
        "",
        f"## 4. Reality check: 20% per week at {leverage:g}x",
        "",
        f"- 20% a week compounds to **{reality['goal_year_multiple']:,.0f}x per year**.",
        f"- At {leverage:g}x you need ETH to move **{reality['need_move']:.1%}** your way *every week*, after costs.",
        f"- Weeks where ETH's open-to-close move was that big (either direction): **{reality['share_close_move']:.0%}** "
        f"of {reality['weeks']} weeks. Median weekly move: {reality['median_abs_week']:.1%}.",
        f"- Even with perfect hindsight, picking the best point in each week: **{reality['share_best_move']:.0%}** of weeks.",
        "- So even a trader who always knew the direction would miss the target in many weeks. A strategy that needs "
        "20% *every* week has to risk liquidation to chase it.",
        "",
        "## 5. Example failed trades (most warnings ignored)",
        "",
        *[f"![{f}](failures/{f})" for f in chart_files],
        "",
        "Raw data with every hint per trade: `trades_with_hints.csv`.",
    ]
    path = out_dir / "failure_analysis.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
