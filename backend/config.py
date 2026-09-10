"""FemWell backend — configuration.

All secrets/config come from environment variables (see .env.example).
Nothing here is hardcoded for production use — the defaults are dev-only
fallbacks so the app can run locally without a .env file present.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'femwell.db'}")

# --- Auth ---
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# --- CORS ---
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# --- ML artifacts (produced by ml/src/train.py) ---
ML_MODELS_DIR = BASE_DIR.parent / "ml" / "models"
BEST_MODEL_PATH = ML_MODELS_DIR / "best_model.joblib"
PREPROCESSOR_PATH = ML_MODELS_DIR / "preprocessor.joblib"
UNCALIBRATED_MODEL_PATH = ML_MODELS_DIR / "best_model_uncalibrated.joblib"
MODEL_REGISTRY_PATH = ML_MODELS_DIR / "model_registry.json"

# --- Risk category thresholds ---
RISK_LOW_MAX = 0.33
RISK_MEDIUM_MAX = 0.66
