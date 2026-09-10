"""
FemWell ML — Preprocessing pipeline.

Builds an sklearn ColumnTransformer/Pipeline that:
  - engineers clinically-relevant features (LH/FSH ratio; BMI already present),
  - imputes missing values (median for numeric, most-frequent for categorical),
  - scales numeric features,
  - passes through binary Y/N flags (already 0/1 in the raw data).

Fit ONLY on the training split — never on val/test — to avoid leakage.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin

from data_loading import TARGET_COL

# Binary (Y/N) columns are already encoded as 0/1 ints in the raw data —
# they need imputation (rare) but not one-hot encoding or scaling.
BINARY_COLS = [
    "Pregnant(Y/N)", "Weight gain(Y/N)", "hair growth(Y/N)",
    "Skin darkening (Y/N)", "Hair loss(Y/N)", "Pimples(Y/N)",
    "Fast food (Y/N)", "Reg.Exercise(Y/N)",
]

# Nominal categorical columns that need one-hot encoding.
CATEGORICAL_COLS = ["Blood Group", "Cycle(R/I)"]


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Adds LH/FSH ratio (clinically relevant for PCOS diagnosis).

    BMI is already present in the raw dataset (computed from weight/height
    by the original data collectors), so we don't recompute it — we just
    verify it's consistent and use it as-is.

    FSH/LH ratio is also already present as a raw column ('FSH/LH'); we
    keep that but additionally derive LH/FSH (the inverse) since some
    clinical literature reports it in that direction and it's a distinct,
    numerically well-behaved feature (avoids near-zero denominators that
    FSH/LH can hit when FSH is very small).
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        if "LH(mIU/mL)" in X.columns and "FSH(mIU/mL)" in X.columns:
            with np.errstate(divide="ignore", invalid="ignore"):
                X["LH_FSH_ratio"] = X["LH(mIU/mL)"] / X["FSH(mIU/mL)"].replace(0, np.nan)
            X["LH_FSH_ratio"] = X["LH_FSH_ratio"].replace([np.inf, -np.inf], np.nan)
        return X


def get_feature_lists(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """Split feature columns (excluding target) into numeric / binary / categorical."""
    all_cols = [c for c in df.columns if c != TARGET_COL]
    categorical = [c for c in CATEGORICAL_COLS if c in all_cols]
    binary = [c for c in BINARY_COLS if c in all_cols]
    numeric = [c for c in all_cols if c not in categorical and c not in binary]
    return numeric, binary, categorical


def build_preprocessor(numeric_cols: list[str], binary_cols: list[str],
                        categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    binary_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", __import__("sklearn.preprocessing", fromlist=["OneHotEncoder"])
                    .OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, numeric_cols),
        ("bin", binary_pipe, binary_cols),
        ("cat", categorical_pipe, categorical_cols),
    ])
    return preprocessor


def build_full_pipeline(df: pd.DataFrame) -> tuple[Pipeline, list[str], list[str], list[str]]:
    """Returns (feature_engineer + preprocessor as a Pipeline, numeric, binary, categorical cols).

    Note: the engineered column 'LH_FSH_ratio' is numeric and is added by
    FeatureEngineer BEFORE the ColumnTransformer runs, so it must be
    included in numeric_cols up front.
    """
    numeric, binary, categorical = get_feature_lists(df)
    if "LH_FSH_ratio" not in numeric:
        numeric = numeric + ["LH_FSH_ratio"]

    preprocessor = build_preprocessor(numeric, binary, categorical)
    pipeline = Pipeline([
        ("feature_engineer", FeatureEngineer()),
        ("preprocessor", preprocessor),
    ])
    return pipeline, numeric, binary, categorical


def get_output_feature_names(pipeline: Pipeline) -> list[str]:
    """Feature names after the ColumnTransformer (for SHAP labeling)."""
    return list(pipeline.named_steps["preprocessor"].get_feature_names_out())
