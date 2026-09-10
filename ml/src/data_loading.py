"""
FemWell ML — Data loading & cleaning.

Loads the Kaggle PCOS dataset (Kottarathil et al.) and produces a clean,
analysis-ready DataFrame. This module ONLY cleans — no imputation, encoding,
or scaling here (that belongs in the sklearn Pipeline in preprocessing.py,
so it can be fit on training data only and avoid leakage).

Dataset: https://www.kaggle.com/datasets/prasoonkottarathil/polycystic-ovary-syndrome-pcos
~541 records, 10 hospitals in Kerala, India. Binary target PCOS (Y/N).
"""

from pathlib import Path
import pandas as pd

TARGET_COL = "PCOS (Y/N)"

# Identifier columns present in the raw file — not predictive features.
ID_COLS = ["Sl. No", "Patient File No."]

# Columns known to be stored as `object` dtype in the raw file due to a
# small number of malformed cells (e.g. "1.99." with a trailing period,
# or a stray "a"). We coerce these to numeric and let the resulting NaN
# be handled by the imputer in the preprocessing pipeline (not silently
# dropped or guessed here).
DIRTY_NUMERIC_COLS = ["II    beta-HCG(mIU/mL)", "AMH(ng/mL)"]


def load_raw(data_dir: str | Path) -> pd.DataFrame:
    """Load the 'Full_new' sheet of the main Excel file."""
    data_dir = Path(data_dir)
    xlsx_path = data_dir / "PCOS_data_without_infertility.xlsx"
    if not xlsx_path.exists():
        raise FileNotFoundError(
            f"Expected {xlsx_path}. Download the dataset from Kaggle and "
            f"place PCOS_data_without_infertility.xlsx under {data_dir}."
        )
    df = pd.read_excel(xlsx_path, sheet_name="Full_new")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply documented, justified cleaning steps. Returns a new DataFrame."""
    df = df.copy()

    # Drop the fully-empty trailing artifact column some exports include,
    # and the two identifier columns (not features, and they'd leak the
    # patient's raw index into the model if left in by accident).
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
    df = df.drop(columns=ID_COLS, errors="ignore")

    # Strip stray whitespace from column names — the raw file has
    # inconsistent spacing (e.g. " Age (yrs)", "Height(Cm) ").
    df.columns = [c.strip() for c in df.columns]

    # Coerce known-dirty numeric columns. `errors="coerce"` turns the
    # malformed cells (e.g. "1.99.", "a") into NaN rather than crashing or
    # silently truncating — those NaNs are then handled by the imputer.
    for col in DIRTY_NUMERIC_COLS:
        col = col.strip()
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ensure the target is a clean 0/1 int.
    df[TARGET_COL] = df[TARGET_COL].astype(int)

    return df


def load_clean(data_dir: str | Path) -> pd.DataFrame:
    return clean(load_raw(data_dir))


def dataset_report(df: pd.DataFrame) -> str:
    """Human-readable summary used in docs/model_card.md and the README."""
    n_rows, n_cols = df.shape
    target_counts = df[TARGET_COL].value_counts()
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    lines = [
        f"Rows: {n_rows}, Columns (incl. target): {n_cols}",
        f"Target distribution: PCOS=1 -> {target_counts.get(1, 0)}, "
        f"PCOS=0 -> {target_counts.get(0, 0)} "
        f"(positive rate: {target_counts.get(1, 0) / n_rows:.1%})",
        "Missing values by column:" if len(missing) else "No missing values after cleaning.",
    ]
    for col, n in missing.items():
        lines.append(f"  - {col}: {n} ({n / n_rows:.1%})")
    return "\n".join(lines)


if __name__ == "__main__":
    df = load_clean("../data/raw")
    print(dataset_report(df))
