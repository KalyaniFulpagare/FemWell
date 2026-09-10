"""
FemWell ML — Model training, comparison, calibration, and persistence.

Trains Logistic Regression, Random Forest, XGBoost, and CatBoost with
stratified 5-fold CV + randomized hyperparameter search, evaluates each on
a held-out validation set, selects the best by validation ROC-AUC/F1,
calibrates it, reports final test-set metrics, and saves the artifacts.

XGBoost/CatBoost are optional imports: if unavailable in the current
environment (e.g. no internet to pip install), the script logs a warning,
skips them, and still runs Logistic Regression + Random Forest +
HistGradientBoostingClassifier (a dependency-free gradient-boosting
model used here only as a stand-in so the pipeline is fully exercised
end-to-end). Install xgboost/catboost to get the full 4-model comparison
the project spec calls for.

Usage: python train.py
"""

from __future__ import annotations
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, brier_score_loss,
)
from sklearn.pipeline import Pipeline

from data_loading import load_clean, TARGET_COL, dataset_report
from preprocessing import build_full_pipeline

RANDOM_STATE = 42
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True, parents=True)

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False


def get_model_search_space() -> dict:
    """Model + RandomizedSearchCV param distributions, keyed by model name."""
    space = {
        "logistic_regression": (
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
            {
                "C": [0.01, 0.03, 0.1, 0.3, 1, 3, 10],
            },
        ),
        "random_forest": (
            RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE),
            {
                "n_estimators": [200, 300, 500, 800],
                "max_depth": [None, 4, 6, 8, 12],
                "min_samples_split": [2, 4, 8],
                "min_samples_leaf": [1, 2, 4],
                "max_features": ["sqrt", "log2", None],
            },
        ),
    }

    if HAS_XGB:
        # scale_pos_weight handles class imbalance (~1:2 positive:negative)
        space["xgboost"] = (
            XGBClassifier(
                eval_metric="logloss", random_state=RANDOM_STATE,
                scale_pos_weight=364 / 177,
            ),
            {
                "n_estimators": [100, 200, 300, 500],
                "max_depth": [3, 4, 5, 6, 8],
                "learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2],
                "subsample": [0.7, 0.8, 0.9, 1.0],
                "colsample_bytree": [0.6, 0.8, 1.0],
            },
        )
    else:
        warnings.warn("xgboost not installed — skipping. `pip install xgboost` to include it.")

    if HAS_CATBOOST:
        space["catboost"] = (
            CatBoostClassifier(
                verbose=0, random_state=RANDOM_STATE, auto_class_weights="Balanced",
                allow_writing_files=False,
            ),
            {
                "iterations": [200, 300, 500],
                "depth": [4, 6, 8],
                "learning_rate": [0.01, 0.03, 0.05, 0.1],
                "l2_leaf_reg": [1, 3, 5, 9],
            },
        )
    else:
        warnings.warn("catboost not installed — skipping. `pip install catboost` to include it.")

    if not HAS_XGB and not HAS_CATBOOST:
        # Dependency-free stand-in so the comparison isn't just two models
        # when neither boosted-tree library is available in this
        # environment. Not a substitute for XGBoost/CatBoost results —
        # included only so the pipeline logic is exercised end-to-end.
        space["hist_gradient_boosting (stand-in)"] = (
            HistGradientBoostingClassifier(random_state=RANDOM_STATE),
            {
                "max_iter": [100, 200, 300],
                "max_depth": [None, 4, 6, 8],
                "learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2],
                "l2_regularization": [0.0, 0.1, 1.0],
            },
        )

    return space


def evaluate(model, X, y) -> dict:
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {
        "accuracy": round(accuracy_score(y, pred), 4),
        "precision": round(precision_score(y, pred), 4),
        "recall": round(recall_score(y, pred), 4),
        "f1": round(f1_score(y, pred), 4),
        "roc_auc": round(roc_auc_score(y, proba), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def main():
    print("=" * 70)
    print("FemWell — Loading and cleaning data")
    print("=" * 70)
    df = load_clean(DATA_DIR)
    print(dataset_report(df))
    print(f"Booster availability — xgboost: {HAS_XGB}, catboost: {HAS_CATBOOST}\n")

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # Stratified 70/15/15 train/val/test split.
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE
    )
    print(f"Split sizes — train: {len(X_train)}, val: {len(X_val)}, test: {len(X_test)}\n")

    # Fit preprocessing ONLY on training data.
    preprocessor, _, _, _ = build_full_pipeline(df)
    X_train_t = preprocessor.fit_transform(X_train, y_train)
    X_val_t = preprocessor.transform(X_val)
    X_test_t = preprocessor.transform(X_test)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search_space = get_model_search_space()

    results = {}
    fitted_estimators = {}

    for name, (estimator, param_dist) in search_space.items():
        print(f"--- Tuning {name} ---")
        search = RandomizedSearchCV(
            estimator, param_distributions=param_dist, n_iter=20, cv=cv,
            scoring="roc_auc", random_state=RANDOM_STATE, n_jobs=-1,
        )
        search.fit(X_train_t, y_train)
        best_est = search.best_estimator_
        fitted_estimators[name] = best_est

        val_metrics = evaluate(best_est, X_val_t, y_val)
        results[name] = {
            "best_params": search.best_params_,
            "cv_best_roc_auc": round(search.best_score_, 4),
            "val_metrics": val_metrics,
        }
        print(f"  CV ROC-AUC: {search.best_score_:.4f} | "
              f"Val ROC-AUC: {val_metrics['roc_auc']:.4f} | Val F1: {val_metrics['f1']:.4f}\n")

    # Select best model by validation ROC-AUC, tie-broken by F1.
    best_name = max(
        results, key=lambda n: (results[n]["val_metrics"]["roc_auc"], results[n]["val_metrics"]["f1"])
    )
    print(f"Selected model: {best_name}")
    best_model = fitted_estimators[best_name]

    # Calibrate the selected model (sigmoid — safer default for small
    # datasets like this one; isotonic can overfit with ~380 training rows).
    print("Calibrating selected model...")
    calibrated = CalibratedClassifierCV(best_model, method="sigmoid", cv=5)
    calibrated.fit(X_train_t, y_train)

    # Calibration quality on validation set.
    val_proba_calibrated = calibrated.predict_proba(X_val_t)[:, 1]
    brier = round(brier_score_loss(y_val, val_proba_calibrated), 4)
    print(f"Validation Brier score (calibrated): {brier}")

    # Final, unbiased evaluation on the held-out test set.
    test_metrics = evaluate(calibrated, X_test_t, y_test)
    test_proba = calibrated.predict_proba(X_test_t)[:, 1]
    test_brier = round(brier_score_loss(y_test, test_proba), 4)
    print(f"Test metrics: {test_metrics}")
    print(f"Test Brier score: {test_brier}")

    # Persist model + preprocessor + full pipeline for the API to use.
    full_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", calibrated),
    ])
    joblib.dump(full_pipeline, MODELS_DIR / "best_model.joblib")
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.joblib")
    # Also persist the raw (uncalibrated) best tree/linear model separately —
    # shap.TreeExplainer needs the underlying tree model, not the
    # CalibratedClassifierCV wrapper.
    joblib.dump(best_model, MODELS_DIR / "best_model_uncalibrated.joblib")

    registry = {
        "model_version": datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S"),
        "algorithm": best_name,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "preprocessor_version": "v1",
        "cv_folds": 5,
        "split": {"train": len(X_train), "val": len(X_val), "test": len(X_test)},
        "val_metrics": results[best_name]["val_metrics"],
        "test_metrics": test_metrics,
        "test_brier_score": test_brier,
        "val_brier_score_calibrated": brier,
        "best_params": results[best_name]["best_params"],
        "all_models_val_comparison": {
            k: v["val_metrics"] for k, v in results.items()
        },
        "notes": (
            "xgboost/catboost were unavailable in the environment that "
            "produced this run" if not (HAS_XGB and HAS_CATBOOST) else
            "Full 4-model comparison (LR, RF, XGBoost, CatBoost)."
        ),
    }
    with open(MODELS_DIR / "model_registry.json", "w") as f:
        json.dump(registry, f, indent=2)

    print("\nSaved: models/best_model.joblib, preprocessor.joblib, model_registry.json")
    return registry


if __name__ == "__main__":
    main()
