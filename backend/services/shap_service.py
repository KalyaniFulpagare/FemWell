"""FemWell backend — SHAP explanation service.

Reuses ml/src/explain.py directly rather than duplicating the SHAP
explainer logic, so the API always matches whatever ml/src produces.
"""
import sys
from pathlib import Path

# Make ml/src importable from the backend without packaging it as a
# separate installable module (keeps this a straightforward, portfolio-
# scale monorepo rather than adding a build step).
ML_SRC_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "src"
if str(ML_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(ML_SRC_DIR))


def explain(inputs: dict, top_k: int = 5) -> dict:
    """Returns top_features_increasing / top_features_decreasing for a
    single input record. Raises FileNotFoundError if ml/models artifacts
    or `shap` aren't available — callers should catch and degrade
    gracefully (e.g. return the prediction without SHAP) rather than 500.
    """
    from explain import explain_instance  # local import: only needed here
    return explain_instance(inputs, top_k=top_k)
