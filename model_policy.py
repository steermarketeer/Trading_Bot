"""
Hard policy for ALL models in this project.

Stateless decisions — no trade-pattern memory, no user/profile history.

ALLOWED
  - Market features from the current bar (and lagged market series used as
    normal indicators: RSI, SMA, funding, etc.)
  - Regime gate from completed higher-timeframe market structure
  - Managing the *currently open* position (size, stop, time in trade) only
    while that position exists — discarded when the trade closes

FORBIDDEN (must stay blank / never persist into model inputs)
  - "Last N similar trades" / kNN / retrieval over past bot trades
  - Features built from closed-trade P&L, win streaks, MAE/MFE history
  - A growing pattern store or user trading "profile"
  - Online learning that keeps permanent memory of live trade outcomes
  - Replaying or conditioning on this account's past fill history

Market candle history for *training* is fine. That is not trade-pattern memory.
Trade logs for human reporting are fine. They must NOT feed the model.
"""
from __future__ import annotations

from typing import Iterable

# Substrings / names that must never appear as model features
FORBIDDEN_FEATURE_TOKENS = (
    "last_50",
    "last50",
    "similar_setup",
    "retrieval",
    "knn_",
    "trade_memory",
    "trade_history",
    "closed_trade",
    "win_streak",
    "loss_streak",
    "pattern_store",
    "user_profile",
    "profile_memory",
    "past_pnl",
    "historical_trade",
    "mae_history",
    "mfe_history",
    "trade_db",
)

POLICY_VERSION = "1.0"
POLICY_NAME = "stateless_no_trade_pattern_memory"


def assert_features_allowed(feature_names: Iterable[str]) -> None:
    """Raise ValueError if any feature looks like trade-pattern memory."""
    bad = []
    for name in feature_names:
        low = str(name).lower()
        for tok in FORBIDDEN_FEATURE_TOKENS:
            if tok in low:
                bad.append(name)
                break
    if bad:
        raise ValueError(
            "MODEL POLICY VIOLATION: trade-pattern / trade-memory features are forbidden.\n"
            f"  Offending: {bad}\n"
            "  Policy: decisions are Stateless; patterns stay blank; no trade-history memory."
        )


def policy_dict() -> dict:
    return {
        "name": POLICY_NAME,
        "version": POLICY_VERSION,
        "stateless": True,
        "trade_pattern_memory": False,
        "last_n_retrieval": False,
        "user_profile_patterns": False,
        "forbidden_feature_tokens": list(FORBIDDEN_FEATURE_TOKENS),
        "note": (
            "Each signal uses only current market/regime features. "
            "Closed trades are not fed back into the model. Patterns stay blank."
        ),
    }
