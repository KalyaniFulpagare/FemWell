from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class AssessmentCreate(BaseModel):
    """User-friendly assessment inputs mapped to model features.
    Missing clinical/report values are allowed and handled by the
    trained preprocessing pipeline.
    """
    inputs: Dict[str, Optional[float]]


class FeatureContribution(BaseModel):
    feature: str
    contribution: float


class AssessmentResult(BaseModel):
    assessment_id: int
    probability: float
    risk_category: str
    top_features_increasing: List[FeatureContribution]
    top_features_decreasing: List[FeatureContribution]
    model_version: str
    disclaimer: str = (
        "FemWell is an educational/screening prototype that uses machine "
        "learning to identify patterns associated with PCOS risk in a "
        "specific dataset. It does NOT diagnose PCOS, provide medical "
        "advice, or replace professional healthcare consultation. Please "
        "consult a qualified healthcare provider for any health concerns."
    )


class WhatIfRequest(BaseModel):
    baseline_assessment_id: int
    modified_features: Dict[str, float]


class WhatIfResponse(BaseModel):
    p0: float
    p1: float
    delta: float
    note: str = (
        "This shows how the model's estimate changes with different "
        "inputs, not a guarantee of outcome."
    )


class AssessmentSummary(BaseModel):
    id: int
    created_at: datetime
    probability: float
    risk_category: str

    class Config:
        from_attributes = True


class AssessmentDetail(AssessmentSummary):
    inputs: Dict[str, Optional[float]]
    model_version: str
    top_features_increasing: Optional[List[FeatureContribution]] = None
    top_features_decreasing: Optional[List[FeatureContribution]] = None


class ComparisonResponse(BaseModel):
    diff_inputs: Dict[str, Dict[str, Optional[float]]]
    diff_prediction: Dict[str, float]
