import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.assessment import Assessment
from auth import get_current_user
from schemas.assessment import (
    AssessmentCreate, AssessmentResult, FeatureContribution,
    WhatIfRequest, WhatIfResponse, AssessmentSummary, AssessmentDetail,
    ComparisonResponse,
)
from services import prediction_service
from services import shap_service

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


def _safe_explain(inputs: dict) -> dict | None:
    """SHAP is optional at request time — if it's not installed or the
    model artifacts are missing, degrade to a prediction-only response
    instead of a 500. Errors are logged to stdout for visibility.
    """
    try:
        return shap_service.explain(inputs)
    except Exception as e:  # noqa: BLE001 — intentionally broad: any SHAP
        # failure should degrade gracefully, not break the assessment.
        print(f"[shap_service] explanation unavailable: {e}")
        return None


@router.get("/feature-schema")
def feature_schema():
    """Returns the exact raw feature keys the model expects, sourced
    from the training data columns so the frontend form always matches
    what ml/src/train.py was actually trained on.
    """
    import sys
    ml_src = Path(__file__).resolve().parent.parent.parent / "ml" / "src"
    if str(ml_src) not in sys.path:
        sys.path.insert(0, str(ml_src))
    from data_loading import load_clean, TARGET_COL
    from config import ML_MODELS_DIR

    df = load_clean(ML_MODELS_DIR.parent / "data" / "raw")
    features = [c for c in df.columns if c != TARGET_COL]
    return {"features": features}


@router.post("", response_model=AssessmentResult, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        probability = prediction_service.predict(payload.inputs)
    except prediction_service.ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    category = prediction_service.risk_category(probability)
    explanation = _safe_explain(payload.inputs)

    increasing = [FeatureContribution(**f) for f in explanation["top_features_increasing"]] if explanation else []
    decreasing = [FeatureContribution(**f) for f in explanation["top_features_decreasing"]] if explanation else []

    assessment = Assessment(
        user_id=current_user.id,
        inputs_json=json.dumps(payload.inputs),
        shap_json=json.dumps(explanation) if explanation else None,
        prediction_probability=probability,
        risk_category=category,
        model_version=prediction_service.get_model_version(),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return AssessmentResult(
        assessment_id=assessment.id,
        probability=round(probability, 4),
        risk_category=category,
        top_features_increasing=increasing,
        top_features_decreasing=decreasing,
        model_version=assessment.model_version,
    )


@router.post("/whatif", response_model=WhatIfResponse)
def whatif(
    payload: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    baseline = db.query(Assessment).filter(
        Assessment.id == payload.baseline_assessment_id,
        Assessment.user_id == current_user.id,
    ).first()
    if not baseline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline assessment not found")

    baseline_inputs = json.loads(baseline.inputs_json)
    modified_inputs = {**baseline_inputs, **payload.modified_features}

    p0 = baseline.prediction_probability
    try:
        p1 = prediction_service.predict(modified_inputs)
    except prediction_service.ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return WhatIfResponse(p0=round(p0, 4), p1=round(p1, 4), delta=round(p1 - p0, 4))


@router.get("/history", response_model=list[AssessmentSummary])
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )


@router.get("/compare/{id1}/{id2}", response_model=ComparisonResponse)
def compare(id1: int, id2: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == id1, Assessment.user_id == current_user.id).first()
    b = db.query(Assessment).filter(Assessment.id == id2, Assessment.user_id == current_user.id).first()
    if not a or not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both assessments not found")

    inputs_a = json.loads(a.inputs_json)
    inputs_b = json.loads(b.inputs_json)
    all_keys = set(inputs_a) | set(inputs_b)
    diff_inputs = {
        k: {"a": inputs_a.get(k), "b": inputs_b.get(k)}
        for k in all_keys
        if inputs_a.get(k) != inputs_b.get(k)
    }

    return ComparisonResponse(
        diff_inputs=diff_inputs,
        diff_prediction={
            "a": round(a.prediction_probability, 4),
            "b": round(b.prediction_probability, 4),
            "delta": round(b.prediction_probability - a.prediction_probability, 4),
        },
    )


@router.get("/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(assessment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id, Assessment.user_id == current_user.id
    ).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    shap_data = json.loads(assessment.shap_json) if assessment.shap_json else None
    return AssessmentDetail(
        id=assessment.id,
        created_at=assessment.created_at,
        probability=assessment.prediction_probability,
        risk_category=assessment.risk_category,
        inputs=json.loads(assessment.inputs_json),
        model_version=assessment.model_version,
        top_features_increasing=(
            [FeatureContribution(**f) for f in shap_data["top_features_increasing"]] if shap_data else None
        ),
        top_features_decreasing=(
            [FeatureContribution(**f) for f in shap_data["top_features_decreasing"]] if shap_data else None
        ),
    )
