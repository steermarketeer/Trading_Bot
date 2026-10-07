"""
First LightGBM training entrypoint.

Loads the prepared train/holdout parquet from prepare_dataset.py,
builds the feature matrices, constructs the model — and STOPS before fit.

When you are ready to actually train, set RUN_FIT = True below (or we flip it later).

Usage:
    .\\.venv\\Scripts\\python.exe prepare_dataset.py   # once
    .\\.venv\\Scripts\\python.exe train_first_model.py
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from model_policy import assert_features_allowed, policy_dict

# ---------------- CONFIG ----------------
PROCESSED = Path("data/processed")
MODELS_DIR = Path("models")
RUN_FIT = True  # training enabled
MODEL_OUT = MODELS_DIR / "lgbm_5m_h48_v2.txt"
REPORT_OUT = MODELS_DIR / "lgbm_5m_h48_v2_report.json"
# ----------------------------------------

LABEL_DROP = {
    "open_time", "open", "high", "low", "close", "volume", "atr_14",
    "label", "label_name", "bars_to_hit",
}


def load_xy(path: Path) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    df = pd.read_parquet(path)
    cols = [c for c in df.columns if c not in LABEL_DROP]
    X = df[cols].replace([np.inf, -np.inf], np.nan)
    y = df["label"].astype(int)
    return X, y, df


def main() -> None:
    meta_path = PROCESSED / "dataset_meta.json"
    if not meta_path.exists():
        raise SystemExit(
            "Missing data/processed/dataset_meta.json.\n"
            "Run first:  python prepare_dataset.py"
        )

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    print("Loaded dataset meta:")
    print(f"  train:    {meta['n_train']:,} rows")
    print(f"  holdout:  {meta['n_holdout']:,} rows")
    print(f"  features: {meta['n_features']}")
    print(f"  cut:      {meta['cut_timestamp']}")

    X_train, y_train, _ = load_xy(Path(meta["train_path"]))
    X_hold, y_hold, _ = load_xy(Path(meta["holdout_path"]))
    assert_features_allowed(X_train.columns)
    print(f"Model policy OK: {policy_dict()['name']} (stateless, no trade-pattern memory)")

    # LightGBM handles NaN natively — no imputation required
    model = lgb.LGBMClassifier(
        objective="multiclass",
        num_class=3,
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=63,
        subsample=0.8,
        colsample_bytree=0.8,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    print("\nModel constructed:")
    print(f"  {model}")
    print(f"\nTrain matrix ready: X={X_train.shape}, y={y_train.shape}")
    print(f"Holdout matrix ready: X={X_hold.shape}, y={y_hold.shape}")
    print(f"Label counts (train): {y_train.value_counts().sort_index().to_dict()}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ready = {
        "status": "READY_TO_FIT",
        "run_fit": RUN_FIT,
        "model_params": model.get_params(),
        "n_train": int(len(X_train)),
        "n_holdout": int(len(X_hold)),
        "n_features": int(X_train.shape[1]),
    }
    (MODELS_DIR / "fit_ready.json").write_text(json.dumps(ready, indent=2), encoding="utf-8")

    if not RUN_FIT:
        print("\n" + "=" * 60)
        print("STOPPED BEFORE model.fit()  (RUN_FIT = False)")
        print("Dataset + model object are ready.")
        print("Say the word when you want training to start.")
        print("=" * 60)
        return

    # ---- actual training ----
    print("\nFitting LightGBM (this may take several minutes)...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_hold, y_hold)],
        eval_metric="multi_logloss",
    )
    out = MODEL_OUT
    model.booster_.save_model(str(out))
    print(f"Saved model -> {out}")

    # Holdout report (accuracy is a first check; P&L backtest comes next)
    from sklearn.metrics import classification_report, accuracy_score, log_loss

    pred = model.predict(X_hold)
    proba = model.predict_proba(X_hold)
    acc = accuracy_score(y_hold, pred)
    ll = log_loss(y_hold, proba, labels=[0, 1, 2])
    print(f"\nHoldout accuracy: {acc:.4f}")
    print(f"Holdout log-loss: {ll:.4f}")
    print("\nClassification report (holdout):")
    print(classification_report(
        y_hold, pred,
        labels=[0, 1, 2],
        target_names=["timeout", "up", "down"],
        digits=3,
    ))

    imp = pd.Series(model.feature_importances_, index=X_train.columns)
    top = imp.sort_values(ascending=False).head(15)
    print("Top 15 features:")
    print(top.to_string())

    report = {
        "status": "TRAINED",
        "model_path": str(out),
        "horizon_note": "4h labels (48 x 5m bars)",
        "holdout_accuracy": float(acc),
        "holdout_logloss": float(ll),
        "top_features": top.to_dict(),
        "label_map": {"0": "timeout", "1": "up", "2": "down"},
    }
    report_path = REPORT_OUT
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport saved -> {report_path}")


if __name__ == "__main__":
    main()
