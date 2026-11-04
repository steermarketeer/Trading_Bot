"""Market data: 5m klines -> completed daily bars, plus funding and data-quality checks."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config
from .regime import compute_daily_regime

BARS_PER_DAY = 288  # 5m bars


@dataclass
class QualityReport:
    symbol: str
    n_5m_bars: int
    first: str
    last: str
    dropped_bad_prints: int
    incomplete_days: list[str]   # days with fewer than 288 five-minute bars (kept, flagged)
    clipped_wicks: list[str] = None  # 5m bars whose wick was a bad print (clipped)

    def summary(self) -> str:
        return (
            f"{self.symbol}: {self.n_5m_bars:,} 5m bars {self.first} -> {self.last}, "
            f"bad prints dropped {self.dropped_bad_prints}, "
            f"days with gaps {len(self.incomplete_days)}, "
            f"bad wicks clipped {len(self.clipped_wicks or [])}"
        )


def load_klines_5m(data_dir: Path, symbol: str) -> tuple[pd.DataFrame, QualityReport]:
    path = Path(data_dir) / "klines" / f"{symbol}_5m.csv"
    df = pd.read_csv(path, usecols=["open_time", "open", "high", "low", "close", "volume"])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    bad = (
        (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
        | (df["high"] < df[["open", "close"]].max(axis=1))
        | (df["low"] > df[["open", "close"]].min(axis=1))
    )
    df = df[~bad].reset_index(drop=True)
    df, clipped = clip_bad_wicks(df)
    counts = df.groupby(df["open_time"].dt.floor("D")).size()
    incomplete = [d.strftime("%Y-%m-%d") for d, n in counts.items() if n < BARS_PER_DAY]
    rep = QualityReport(
        symbol=symbol,
        n_5m_bars=len(df),
        first=str(df["open_time"].iloc[0]),
        last=str(df["open_time"].iloc[-1]),
        dropped_bad_prints=int(bad.sum()),
        incomplete_days=incomplete,
        clipped_wicks=clipped,
    )
    return df, rep


WICK_LIMIT = 0.15  # a 5m wick >15% beyond its body AND both neighbours is treated as a bad print


def clip_bad_wicks(df: pd.DataFrame, limit: float = WICK_LIMIT) -> tuple[pd.DataFrame, list[str]]:
    """
    Clip single-bar spikes that the market never traded around (e.g. ETH 2020-03-13 02:35
    high 323 while price was ~110). The reference is the bar's body plus the previous close
    and the next open; real crash wicks are usually echoed by neighbouring bars and stay.
    """
    df = df.copy()
    o, c = df["open"], df["close"]
    prev_c, next_o = c.shift(1).fillna(o), o.shift(-1).fillna(c)
    ref_hi = pd.concat([o, c, prev_c, next_o], axis=1).max(axis=1)
    ref_lo = pd.concat([o, c, prev_c, next_o], axis=1).min(axis=1)
    bad_hi = df["high"] > ref_hi * (1 + limit)
    bad_lo = df["low"] < ref_lo * (1 - limit)
    df.loc[bad_hi, "high"] = ref_hi[bad_hi]
    df.loc[bad_lo, "low"] = ref_lo[bad_lo]
    hit = df.loc[bad_hi | bad_lo, "open_time"]
    return df, [str(t) for t in hit]


def to_daily(df5: pd.DataFrame) -> pd.DataFrame:
    """UTC daily bars. The final day is dropped if it is not finished yet."""
    x = df5.set_index("open_time")
    d = x.resample("1D", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    d["n_bars"] = x["close"].resample("1D", label="left", closed="left").count()
    d = d.dropna(subset=["close"]).reset_index().rename(columns={"open_time": "ts"})
    last_bar = df5["open_time"].iloc[-1]
    if last_bar < d["ts"].iloc[-1] + pd.Timedelta(hours=23, minutes=55):
        d = d.iloc[:-1]
    d["day"] = d["ts"].dt.strftime("%Y-%m-%d")
    return d.reset_index(drop=True)


def load_funding(data_dir: Path, symbol: str) -> dict[str, list[tuple[float, float]]]:
    """day -> [(hour_utc, rate), ...]. Positive rate: longs pay shorts."""
    path = Path(data_dir) / "funding" / f"{symbol}.csv"
    if not path.exists():
        return {}
    f = pd.read_csv(path)
    ts = pd.to_datetime(f["fundingTime"], unit="ms", utc=True).dt.round("min")
    out: dict[str, list[tuple[float, float]]] = {}
    for t, r in zip(ts, f["fundingRate"].astype(float)):
        out.setdefault(t.strftime("%Y-%m-%d"), []).append((t.hour + t.minute / 60.0, float(r)))
    return out


def build_dataset(cfg: Config, verbose: bool = False) -> pd.DataFrame:
    """
    One row per completed UTC day with ETH OHLCV, BTC OHLC (btc_*), regime columns
    (known at that day's close) and that day's funding settlements.
    """
    eth5, q_eth = load_klines_5m(cfg.data_dir, cfg.symbol)
    btc5, q_btc = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    if verbose:
        print(q_eth.summary())
        print(q_btc.summary())
    eth = to_daily(eth5)
    btc = to_daily(btc5)
    btc_cols = btc[["day", "open", "high", "low", "close", "volume"]].rename(
        columns={c: f"btc_{c}" for c in ("open", "high", "low", "close", "volume")}
    )
    d = eth.merge(btc_cols, on="day", how="left")
    reg = compute_daily_regime(eth, btc, extra_lag=cfg.regime_extra_lag)
    d = d.merge(reg, on="day", how="left")
    d["regime"] = d["regime"].fillna("Neutral")
    funding = load_funding(cfg.data_dir, cfg.symbol)
    d["funding"] = [funding.get(day, []) for day in d["day"]]
    d["data_gap"] = d["n_bars"] < BARS_PER_DAY
    return d


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


def run_length(s: pd.Series) -> pd.Series:
    """How many consecutive rows (including this one) have had the same value."""
    change = s.ne(s.shift(1)).cumsum()
    return s.groupby(change).cumcount() + 1


__all__ = ["build_dataset", "to_daily", "load_klines_5m", "load_funding", "sma", "atr", "run_length", "np"]
