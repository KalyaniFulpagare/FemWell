# FemWell — Model Card

## Intended use
FemWell's model is a **screening and education aid**, not a diagnostic tool.
It surfaces patterns in a specific historical dataset that correlate with a
recorded PCOS diagnosis, and explains which inputs drove a given prediction.
It must never be presented as diagnosing PCOS or replacing a clinician.

## Dataset
- Source: Kaggle, "Polycystic ovary syndrome (PCOS)" (Kottarathil, 2020),
  https://www.kaggle.com/datasets/prasoonkottarathil/polycystic-ovary-syndrome-pcos
- 541 patient records collected across 10 hospitals in Kerala, India.
- Target: `PCOS (Y/N)` — 177 positive (32.7%), 364 negative (67.3%). Mild
  class imbalance, handled via `class_weight="balanced"` / `scale_pos_weight`.
- 41 raw features after dropping identifier columns: demographics, vitals,
  menstrual history, hormone panel (FSH, LH, AMH, TSH, PRL, PRG, beta-HCG),
  physical measurements (BMI, waist:hip), lifestyle flags, and follicle/
  ultrasound counts.
- Missingness is minimal (≤1 row for 4 columns) — median/most-frequent
  imputation is sufficient; no rows were dropped.
- Two columns (`II beta-HCG`, `AMH`) contained a small number of malformed
  string cells (e.g. `"1.99."`, `"a"`) in the raw export; these are coerced
  to numeric with `errors="coerce"`, turning them into NaN for the imputer
  rather than being guessed or silently dropped.

### Limitations
- **Small sample** (541 rows) — models are prone to variance; the 15%
  test split is only ~82 records, so reported metrics have real
  uncertainty (a handful of test-set flips would shift F1 by several
  points).
- **Single-region cohort** (Kerala, India, one data collection window) —
  not demonstrated to generalize to other populations, ethnicities, or
  diagnostic criteria (e.g. Rotterdam vs. NIH PCOS criteria may have been
  applied inconsistently across the source hospitals; this isn't
  documented in the original dataset).
- **Labels reflect clinical diagnosis at time of collection**, which
  itself has known inter-rater variability for PCOS.
- Several hormone features are highly informative and easy to spuriously
  overfit to given the sample size — cross-validation and a held-out test
  set are used throughout, but this is a portfolio-scale project, not a
  validated clinical instrument.

## Method
- Stratified 70/15/15 train/val/test split, preprocessing fit on train
  only (median imputation for numeric, most-frequent for binary/
  categorical, one-hot encoding, standard scaling).
- Feature engineering: `LH_FSH_ratio` added alongside the dataset's
  existing `FSH/LH` and `BMI` columns.
- Four candidate models compared with stratified 5-fold CV +
  `RandomizedSearchCV` (20 iterations, scored on ROC-AUC): Logistic
  Regression, Random Forest, XGBoost, CatBoost.
- Best model selected on validation ROC-AUC (tie-break: F1), then
  calibrated with `CalibratedClassifierCV` (sigmoid, 5-fold).
- Final metrics reported on the held-out test set — untouched until this
  final step.

## Results (this run)
> Produced by `ml/src/train.py`. See `ml/models/model_registry.json` for
> the full, current numbers — this section is a snapshot, not the source
> of truth.

This particular run was executed in a sandbox without internet access, so
**XGBoost and CatBoost could not be installed and are missing from this
comparison** (the code supports them — see `ml/src/train.py` — but they
were skipped and a warning logged). A dependency-free
`HistGradientBoostingClassifier` stood in as a third model so the
comparison and pipeline logic could still run end-to-end for real. Re-run
`train.py` in an environment with internet (`pip install -r
requirements.txt`) to get the full 4-model comparison the project spec
calls for — no code changes needed.

| Model | Val ROC-AUC | Val F1 |
|---|---|---|
| Logistic Regression | 0.9049 | 0.7368 |
| Random Forest (selected) | 0.9343 | 0.7556 |
| HistGradientBoosting (stand-in, not part of required 4) | 0.9217 | 0.7500 |

**Selected model: Random Forest.** Test-set metrics (held out, seen once):
Accuracy 0.9146, Precision 0.8846, Recall 0.8519, F1 0.8679, ROC-AUC
0.9636, Brier score 0.0698.

Confusion matrix (test, n=82): 52 true negatives, 3 false positives,
4 false negatives, 23 true positives.

## Explainability
SHAP (`shap.TreeExplainer` for the selected tree model) provides:
- A global summary plot (`ml/plots/shap_summary.png`) showing which
  features matter most across the dataset and in which direction.
- Per-instance explanations (`ml/src/explain.py: explain_instance()`)
  returning the top features pushing an individual prediction up vs.
  down, for the "Explainability" and result pages in the frontend.

SHAP values explain the *model's* reasoning about *this dataset*, not
biological cause-and-effect — the frontend and any generated report must
present them as such (see disclaimer requirement below).

## Required disclaimer (every screen/report that shows a prediction)
> "FemWell is an educational/screening prototype that uses machine
> learning to identify patterns associated with PCOS risk in a specific
> dataset. It does NOT diagnose PCOS, provide medical advice, or replace
> professional healthcare consultation. Please consult a qualified
> healthcare provider for any health concerns."
