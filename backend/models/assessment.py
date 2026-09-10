from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Raw inputs and SHAP output stored as JSON text (SQLite has no native
    # JSON type; Postgres deployments can switch this column to JSONB
    # without changing the API contract).
    inputs_json = Column(Text, nullable=False)
    shap_json = Column(Text, nullable=True)

    prediction_probability = Column(Float, nullable=False)

    @property
    def probability(self):
        return self.prediction_probability
    risk_category = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
