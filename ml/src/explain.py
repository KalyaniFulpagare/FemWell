from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

try:
    import shap
except ImportError as e:
    raise ImportError(
        "shap is required for this module. Install with `pip install shap`."
    ) from e

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODELS_DIR = Path(__file__).parent.parent / "models"
PLOTS_DIR = Path(__file__).parent.parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True, parents=True)

TREE_MODEL_NAMES = (
    "RandomForestClassifier",
    "XGBClassifier",
    "CatBoostClassifier",
    "HistGradientBoostingClassifier",
)


def _make_explainer(raw_model, background):
    model_type = type(raw_model).__name__

    if model_type in TREE_MODEL_NAMES:
        return shap.TreeExplainer(raw_model), "tree"

    if model_type == "LogisticRegression":
        return shap.LinearExplainer(raw_model, background), "linear"

    return (
        shap.KernelExplainer(
            raw_model.predict_proba,
            shap.sample(background, 50)
        ),
        "kernel",
    )


def load_artifacts():
    preprocessor = joblib.load(MODELS_DIR / "preprocessor.joblib")
    raw_model = joblib.load(MODELS_DIR / "best_model_uncalibrated.joblib")
    return preprocessor, raw_model


def _get_required_columns(preprocessor):
    """
    Get the original raw columns expected by the saved preprocessing pipeline.
    The pipeline is:
        FeatureEngineer -> ColumnTransformer
    """

    if not hasattr(preprocessor, "named_steps"):
        raise RuntimeError("Saved preprocessor is not a Pipeline.")

    column_transformer = preprocessor.named_steps.get("preprocessor")

    if column_transformer is None:
        raise RuntimeError(
            "Could not find the ColumnTransformer in the preprocessing pipeline."
        )

    columns = []

    for _, _, transformer_columns in column_transformer.transformers:
        if transformer_columns == "drop" or transformer_columns == "passthrough":
            continue

        columns.extend(list(transformer_columns))

    # FeatureEngineer creates this column before ColumnTransformer.
    if "LH_FSH_ratio" in columns:
        pass

    return list(dict.fromkeys(columns))


def _prepare_record(record, preprocessor):
    required_columns = _get_required_columns(preprocessor)

    row = {
        column: np.nan
        for column in required_columns
    }

    for column, value in record.items():
        if column in row:
            row[column] = (
                np.nan
                if value is None or value == ""
                else value
            )

    # Derived raw feature
    if "FSH/LH" in row and pd.isna(row["FSH/LH"]):
        fsh = record.get("FSH(mIU/mL)")
        lh = record.get("LH(mIU/mL)")

        if fsh not in (None, "", 0) and lh not in (None, ""):
            row["FSH/LH"] = float(fsh) / float(lh)

    return pd.DataFrame([row], columns=required_columns)


def global_summary_plot(
    X_train: pd.DataFrame,
    max_display: int = 15,
    out_path: str | Path = None,
) -> Path:

    preprocessor, raw_model = load_artifacts()

    X_train_t = preprocessor.transform(X_train)

    feature_names = (
        preprocessor
        .named_steps["preprocessor"]
        .get_feature_names_out()
    )

    explainer, _ = _make_explainer(raw_model, X_train_t)
    shap_values = explainer.shap_values(X_train_t)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    elif shap_values.ndim == 3:
        shap_values = shap_values[:, :, 1]

    plt.figure()

    shap.summary_plot(
        shap_values,
        X_train_t,
        feature_names=feature_names,
        max_display=max_display,
        show=False,
    )

    out_path = (
        Path(out_path)
        if out_path
        else PLOTS_DIR / "shap_summary.png"
    )

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    return out_path


def explain_instance(record: dict, top_k: int = 5) -> dict[str, Any]:

    preprocessor, raw_model = load_artifacts()

    X = _prepare_record(record, preprocessor)

    X_t = preprocessor.transform(X)

    feature_names = (
        preprocessor
        .named_steps["preprocessor"]
        .get_feature_names_out()
    )

    explainer, _ = _make_explainer(raw_model, X_t)

    shap_values = explainer.shap_values(X_t)

    if isinstance(shap_values, list):
        sv = shap_values[1][0]
        base_value = explainer.expected_value[1]

    elif shap_values.ndim == 3:
        sv = shap_values[0, :, 1]
        base_value = explainer.expected_value[1]

    else:
        sv = shap_values[0]
        base_value = explainer.expected_value

        if isinstance(base_value, (list, np.ndarray)):
            base_value = base_value[-1]

    contributions = sorted(
        zip(feature_names, sv),
        key=lambda item: item[1],
        reverse=True,
    )

    increasing = [
        {
            "feature": feature,
            "contribution": round(float(value), 4),
        }
        for feature, value in contributions
        if value > 0
    ][:top_k]

    decreasing = [
        {
            "feature": feature,
            "contribution": round(float(value), 4),
        }
        for feature, value in contributions
        if value < 0
    ][-top_k:][::-1]

    return {
        "base_value": round(float(base_value), 4),
        "top_features_increasing": increasing,
        "top_features_decreasing": decreasing,
        "all_contributions": {
            feature: round(float(value), 4)
            for feature, value in zip(feature_names, sv)
        },
    }
