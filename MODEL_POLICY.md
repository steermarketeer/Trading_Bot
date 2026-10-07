# Model decision policy (all models)

## Rule
**Stateless. No trade-pattern memory. Patterns stay blank.**

## Allowed
- Indicators / features from the **current market bar** (and normal lagged market series)
- Regime from completed weekly/monthly market structure
- State of the **open** position only while it is open (then discarded)

## Forbidden
- Last-N / kNN / “similar past trades” retrieval
- Features from closed-trade history, streaks, profile, pattern store
- Saving patterns on a user profile or vanishing/replaying trade memory into the model

## Code
Enforced by `model_policy.py` → `assert_features_allowed(...)`.

Market history for training is OK. Your past bot trades are **not** model memory.
