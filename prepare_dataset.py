"""
Prepare the first LightGBM training dataset and stop BEFORE model.fit().

Pipeline:
  1. Load ETHUSDT 5m klines + funding (+ BTC 5m as context features)
  2. Build a compact first-pass feature set (~40 features)
  3. Build Mode B (ATR-scaled 2:1) triple-barrier labels, net of taker fees
  4. Time-split into train / holdout
  5. Save parquet files under data/processed/ ready for training

Usage:
    .\\.venv\\Scripts\\python.exe prepare_dataset.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from model_policy import assert_features_allowed, policy_dict

# ---------------- CONFIG ----------------
DATA_DIR = Path("data")
OUT_DIR = DATA_DIR / "processed"
HOLDOUT_DAYS = 180  # last ~6 months untouched for final eval
ATR_WINDOW = 14
HORIZON_BARS = 48  # 48 * 5m = 4 hours (v2 longer-horizon labels)
PT_ATR_MULT = 2.0  # profit target = 2 * ATR  (2:1 vs stop)
SL_ATR_MULT = 1.0  # stop / exit = 1 * ATR
TAKER_FEE = 0.0004  # 0.04% per side (Binance USDT-M taker ballpark)
MIN_HISTORY = 200  # warm-up bars dropped after features
# Output tag so v1 (1h) and v2 (4h) datasets can coexist
DATASET_TAG = "5m_h48"
# ----------------------------------------


def load_klines(symbol: str, interval: str = "5m") -> pd.DataFrame:
    path = DATA_DIR / "klines" / f"{symbol}_{interval}.csv"
    df = pd.read_csv(path)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)
    for c in ["open", "high", "low", "close", "volume", "quote_volume",
              "taker_buy_base", "taker_buy_quote"]:
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype(int)
    return df


def load_funding(symbol: str) -> pd.DataFrame:
    path = DATA_DIR / "funding" / f"{symbol}.csv"
    df = pd.read_csv(path)
    df["fundingTime"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True)
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df.drop_duplicates("fundingTime").sort_values("fundingTime").reset_index(drop=True)


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            (df["high"] - df["low"]),
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window, min_periods=window).mean()


def build_features(eth: pd.DataFrame, btc: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    df = eth.copy()
    df = df.merge(
        btc[["open_time", "close", "volume"]].rename(
            columns={"close": "btc_close", "volume": "btc_volume"}
        ),
        on="open_time",
        how="left",
    )
    # funding is every 8h — forward-fill onto 5m bars (known at settlement, no peek ahead of bar)
    fund = funding.rename(columns={"fundingTime": "open_time"})
    df = pd.merge_asof(
        df.sort_values("open_time"),
        fund.sort_values("open_time"),
        on="open_time",
        direction="backward",
    )

    c = df["close"]
    v = df["volume"]

    # Returns
    for n in (1, 3, 6, 12, 24, 48):
        df[f"ret_{n}"] = c.pct_change(n)

    # Trend / moving averages
    for n in (20, 50, 100):
        ma = c.rolling(n, min_periods=n).mean()
        df[f"sma_{n}_dist"] = (c - ma) / ma
        df[f"sma_{n}_slope"] = ma.pct_change(5)

    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    df["macd"] = macd / c
    df["macd_hist"] = (macd - signal) / c
    df["macd_hist_slope"] = df["macd_hist"].diff(3)

    # Momentum
    df["rsi_14"] = rsi(c, 14)
    df["rsi_7"] = rsi(c, 7)
    high14 = df["high"].rolling(14, min_periods=14).max()
    low14 = df["low"].rolling(14, min_periods=14).min()
    df["stoch_k"] = 100 * (c - low14) / (high14 - low14).replace(0, np.nan)

    # Volatility
    df["atr_14"] = atr(df, ATR_WINDOW)
    df["atr_pct"] = df["atr_14"] / c
    mid = c.rolling(20, min_periods=20).mean()
    std = c.rolling(20, min_periods=20).std()
    df["bb_pctb"] = (c - (mid - 2 * std)) / (4 * std).replace(0, np.nan)
    df["bb_width"] = (4 * std) / mid
    df["realized_vol_24"] = df["ret_1"].rolling(24, min_periods=24).std()
    df["realized_vol_96"] = df["ret_1"].rolling(96, min_periods=96).std()

    # Volume
    vol_ma = v.rolling(48, min_periods=48).mean()
    vol_std = v.rolling(48, min_periods=48).std()
    df["volume_z"] = (v - vol_ma) / vol_std.replace(0, np.nan)
    df["taker_buy_ratio"] = df["taker_buy_base"] / v.replace(0, np.nan)
    df["trade_count_z"] = (
        (df["trades"] - df["trades"].rolling(48, min_periods=48).mean())
        / df["trades"].rolling(48, min_periods=48).std().replace(0, np.nan)
    )
    df["obv_slope"] = (
        np.sign(c.diff()).fillna(0) * v
    ).cumsum().pct_change(12)

    # Range / candle shape
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    df["close_loc"] = (c - df["low"]) / rng
    df["body_pct"] = (c - df["open"]).abs() / rng
    df["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / rng
    df["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / rng

    # Perp / funding
    df["funding_rate"] = df["fundingRate"].astype(float)
    df["funding_z"] = (
        (df["funding_rate"] - df["funding_rate"].rolling(21 * 3, min_periods=21).mean())
        / df["funding_rate"].rolling(21 * 3, min_periods=21).std().replace(0, np.nan)
    )
    df["funding_change"] = df["funding_rate"].diff()

    # BTC context
    df["btc_ret_1"] = df["btc_close"].pct_change(1)
    df["btc_ret_12"] = df["btc_close"].pct_change(12)
    df["eth_btc_ratio"] = c / df["btc_close"]
    df["eth_btc_ret_12"] = df["eth_btc_ratio"].pct_change(12)
    df["eth_btc_corr_96"] = df["ret_1"].rolling(96, min_periods=48).corr(df["btc_ret_1"])

    # Clock / session (UTC)
    hour = df["open_time"].dt.hour
    dow = df["open_time"].dt.dayofweek
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["dow_sin"] = np.sin(2 * np.pi * dow / 7)
    df["dow_cos"] = np.cos(2 * np.pi * dow / 7)
    df["is_weekend"] = (dow >= 5).astype(int)
    df["session_asia"] = ((hour >= 0) & (hour < 8)).astype(int)
    df["session_london"] = ((hour >= 8) & (hour < 13)).astype(int)
    df["session_ny"] = ((hour >= 13) & (hour < 21)).astype(int)
    # hours to next funding (00/08/16 UTC)
    next_funding_hour = ((hour // 8) + 1) * 8
    hours_to_funding = next_funding_hour - hour
    hours_to_funding = hours_to_funding.where(next_funding_hour < 24, 24 - hour)
    df["hours_to_funding"] = hours_to_funding.astype(float)

    feature_cols = [
        c for c in df.columns
        if c not in {
            "open", "high", "low", "close", "volume", "close_time", "quote_volume",
            "trades", "taker_buy_base", "taker_buy_quote", "btc_close", "btc_volume",
            "fundingRate", "funding_rate",  # keep funding_rate — wait, we want it
        }
        and c != "open_time"
    ]
    # Keep funding_rate explicitly; remove raw merge leftovers only
    keep = [
        "open_time", "open", "high", "low", "close", "volume", "atr_14",
        "ret_1", "ret_3", "ret_6", "ret_12", "ret_24", "ret_48",
        "sma_20_dist", "sma_50_dist", "sma_100_dist", "sma_20_slope", "sma_50_slope", "sma_100_slope",
        "macd", "macd_hist", "macd_hist_slope",
        "rsi_14", "rsi_7", "stoch_k",
        "atr_pct", "bb_pctb", "bb_width", "realized_vol_24", "realized_vol_96",
        "volume_z", "taker_buy_ratio", "trade_count_z", "obv_slope",
        "close_loc", "body_pct", "upper_wick", "lower_wick",
        "funding_rate", "funding_z", "funding_change",
        "btc_ret_1", "btc_ret_12", "eth_btc_ratio", "eth_btc_ret_12", "eth_btc_corr_96",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend",
        "session_asia", "session_london", "session_ny", "hours_to_funding",
    ]
    return df[keep].copy()


def triple_barrier_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mode B: ATR-scaled barriers, 2:1 reward:risk.
    Label at bar i uses only future path i+1 .. i+HORIZON (no leakage into features at i).
    Fees: round-trip taker subtracted from the effective move when classifying.
    """
    n = len(df)
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    atr_arr = df["atr_14"].to_numpy(dtype=float)

    labels = np.full(n, -1, dtype=int)  # -1 = invalid / warm-up / insufficient future
    # 0 = timeout, 1 = up-win, 2 = down-win
    hit_bars = np.full(n, np.nan)

    fee_rt = 2.0 * TAKER_FEE  # entry + exit

    for i in range(n - 1):
        a = atr_arr[i]
        px = close[i]
        if not np.isfinite(a) or a <= 0 or not np.isfinite(px) or px <= 0:
            continue
        end = min(i + HORIZON_BARS, n - 1)
        if end <= i:
            continue

        pt_long = px + PT_ATR_MULT * a
        sl_long = px - SL_ATR_MULT * a
        pt_short = px - PT_ATR_MULT * a
        sl_short = px + SL_ATR_MULT * a

        # Which barrier hits first for long and short paths independently,
        # then pick the trade direction that wins first (standard TB for direction).
        long_hit = None  # ("up", t) or ("stop", t)
        short_hit = None

        for j in range(i + 1, end + 1):
            if long_hit is None:
                if high[j] >= pt_long:
                    long_hit = ("up", j)
                elif low[j] <= sl_long:
                    long_hit = ("stop", j)
            if short_hit is None:
                if low[j] <= pt_short:
                    short_hit = ("down", j)
                elif high[j] >= sl_short:
                    short_hit = ("stop", j)
            if long_hit is not None and short_hit is not None:
                break

        # Net of fees: a "win" must clear the fee drag in price terms
        fee_buffer = px * fee_rt

        candidates = []
        if long_hit is not None and long_hit[0] == "up":
            # gross target move = PT_ATR_MULT * atr; require > fee
            if PT_ATR_MULT * a > fee_buffer:
                candidates.append((long_hit[1], 1))  # up-win
        if short_hit is not None and short_hit[0] == "down":
            if PT_ATR_MULT * a > fee_buffer:
                candidates.append((short_hit[1], 2))  # down-win

        if candidates:
            # earliest successful directional hit
            candidates.sort(key=lambda x: x[0])
            t, lab = candidates[0]
            labels[i] = lab
            hit_bars[i] = t - i
        else:
            # both timed out or only stopped — timeout / no edge
            labels[i] = 0
            hit_bars[i] = end - i

    out = df.copy()
    out["label"] = labels
    out["label_name"] = out["label"].map({-1: "invalid", 0: "timeout", 1: "up", 2: "down"})
    out["bars_to_hit"] = hit_bars
    return out


def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    max_t = df["open_time"].max()
    cut = max_t - pd.Timedelta(days=HOLDOUT_DAYS)
    train = df[df["open_time"] < cut].copy()
    holdout = df[df["open_time"] >= cut].copy()
    return train, holdout, cut


def feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    drop = {"open_time", "open", "high", "low", "close", "volume", "atr_14",
            "label", "label_name", "bars_to_hit"}
    cols = [c for c in df.columns if c not in drop]
    X = df[cols].replace([np.inf, -np.inf], np.nan)
    y = df["label"].astype(int)
    return X, y


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading klines + funding...")
    eth = load_klines("ETHUSDT", "5m")
    btc = load_klines("BTCUSDT", "5m")
    funding = load_funding("ETHUSDT")
    print(f"  ETH 5m: {len(eth):,}  |  BTC 5m: {len(btc):,}  |  funding: {len(funding):,}")
    print(f"  ETH range: {eth['open_time'].iloc[0]} -> {eth['open_time'].iloc[-1]}")

    print("Building features...")
    feat = build_features(eth, btc, funding)

    print(f"Building Mode B triple-barrier labels (horizon={HORIZON_BARS} bars, "
          f"PT={PT_ATR_MULT}*ATR, SL={SL_ATR_MULT}*ATR)...")
    labeled = triple_barrier_labels(feat)

    # Drop warm-up / invalid
    labeled = labeled.iloc[MIN_HISTORY:].copy()
    labeled = labeled[labeled["label"] >= 0].copy()
    # Drop rows with too many NaN features
    X_all, _ = feature_matrix(labeled)
    nan_frac = X_all.isna().mean(axis=1)
    labeled = labeled.loc[nan_frac <= 0.1].copy()

    print("Time-splitting...")
    train, holdout, cut = time_split(labeled)
    print(f"  Cut date (holdout starts): {cut}")
    print(f"  Train rows:   {len(train):,}")
    print(f"  Holdout rows: {len(holdout):,}")

    for name, part in [("train", train), ("holdout", holdout)]:
        vc = part["label_name"].value_counts()
        print(f"  {name} label mix:\n{vc.to_string()}\n")

    X_train, y_train = feature_matrix(train)
    X_hold, y_hold = feature_matrix(holdout)

    # Stateless policy: no trade-pattern / trade-memory features
    assert_features_allowed(X_train.columns)

    # Persist full labeled frames + X/y for training
    train_path = OUT_DIR / f"train_{DATASET_TAG}.parquet"
    hold_path = OUT_DIR / f"holdout_{DATASET_TAG}.parquet"
    train.to_parquet(train_path, index=False)
    holdout.to_parquet(hold_path, index=False)

    # Also write "current" pointers used by train/backtest scripts
    cur_train = OUT_DIR / "train_5m.parquet"
    cur_hold = OUT_DIR / "holdout_5m.parquet"
    train.to_parquet(cur_train, index=False)
    holdout.to_parquet(cur_hold, index=False)

    meta = {
        "symbol": "ETHUSDT",
        "interval": "5m",
        "dataset_tag": DATASET_TAG,
        "horizon_bars": HORIZON_BARS,
        "horizon_hours": HORIZON_BARS * 5 / 60,
        "pt_atr_mult": PT_ATR_MULT,
        "sl_atr_mult": SL_ATR_MULT,
        "taker_fee": TAKER_FEE,
        "holdout_days": HOLDOUT_DAYS,
        "cut_timestamp": str(cut),
        "n_train": int(len(train)),
        "n_holdout": int(len(holdout)),
        "n_features": int(X_train.shape[1]),
        "feature_columns": list(X_train.columns),
        "label_map": {"0": "timeout", "1": "up", "2": "down"},
        "train_path": str(cur_train),
        "holdout_path": str(cur_hold),
        "train_path_tagged": str(train_path),
        "holdout_path_tagged": str(hold_path),
        "status": "READY_FOR_FIT",
        "model_policy": policy_dict(),
        "note": "v2 longer-horizon (4h) labels. Stateless policy enforced. Run train_first_model.py to fit.",
    }
    meta_path = OUT_DIR / "dataset_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("=" * 60)
    print("DATASET READY FOR TRAINING (fit not started)")
    print(f"  Features:     {X_train.shape[1]}")
    print(f"  Train X:      {X_train.shape}")
    print(f"  Holdout X:    {X_hold.shape}")
    print(f"  Saved:        {train_path}")
    print(f"  Saved:        {hold_path}")
    print(f"  Meta:         {meta_path}")
    print("  Next:         python train_first_model.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
