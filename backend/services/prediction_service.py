"""FemWell backend — prediction service."""

import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from config import (
    BEST_MODEL_PATH,
    MODEL_REGISTRY_PATH,
    RISK_LOW_MAX,
    RISK_MEDIUM_MAX,
)


class ModelNotFoundError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_pipeline():
    if not BEST_MODEL_PATH.exists():
        raise ModelNotFoundError(
            f"Best model not found at {BEST_MODEL_PATH}"
        )
    return joblib.load(BEST_MODEL_PATH)


@lru_cache(maxsize=1)
def get_model_version() -> str:
    if not MODEL_REGISTRY_PATH.exists():
        return "unknown"

    try:
        data = json.loads(MODEL_REGISTRY_PATH.read_text())
        return str(
            data.get(
                "best_model",
                data.get("model_version", "unknown")
            )
        )
    except Exception:
        return "unknown"


def risk_category(probability: float) -> str:
    if probability <= RISK_LOW_MAX:
        return "Low"
    if probability <= RISK_MEDIUM_MAX:
        return "Medium"
    return "High"


def _get_required_columns(pipeline):
    """Get the original feature columns expected by the trained model."""

    # The trained preprocessing pipeline exposes the original columns here.
    if hasattr(pipeline, "feature_names_in_"):
        return list(pipeline.feature_names_in_)

    # If the outer object is a Pipeline containing another Pipeline,
    # search its steps recursively.
    if hasattr(pipeline, "named_steps"):
        for step in pipeline.named_steps.values():
            if hasattr(step, "feature_names_in_"):
                return list(step.feature_names_in_)

            if hasattr(step, "named_steps"):
                for nested_step in step.named_steps.values():
                    if hasattr(nested_step, "feature_names_in_"):
                        return list(nested_step.feature_names_in_)

    raise RuntimeError(
        "Could not determine the feature columns expected by the trained model."
    )


def _prepare_input(inputs: dict, pipeline) -> pd.DataFrame:
    """Build a complete model-compatible dataframe."""

    required_columns = _get_required_columns(pipeline)

    # Start with every feature expected by the trained model.
    row = {
        column: np.nan
        for column in required_columns
    }

    # Fill in the values supplied by the frontend.
    for column, value in inputs.items():
        if column in row:
            if value is None or value == "":
                row[column] = np.nan
            else:
                row[column] = value

    # Calculate FSH/LH-derived feature when possible.
    if "FSH/LH" in row and pd.isna(row["FSH/LH"]):
        fsh = inputs.get("FSH(mIU/mL)")
        lh = inputs.get("LH(mIU/mL)")

        if fsh not in (None, "", 0) and lh not in (None, ""):
            row["FSH/LH"] = float(fsh) / float(lh)

    return pd.DataFrame([row], columns=required_columns)


def predict(inputs: dict) -> float:
    """Predict using the trained model with all required columns."""

    pipeline = get_pipeline()

    X = _prepare_input(inputs, pipeline)

    proba = pipeline.predict_proba(X)[:, 1][0]

    return float(proba)
