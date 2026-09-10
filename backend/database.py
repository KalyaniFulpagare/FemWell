"""FemWell backend — SQLAlchemy engine/session setup.

Uses SQLite by default (set DATABASE_URL for Postgres in production —
see .env.example and docs for the Neon/Supabase deployment path).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once on app startup."""
    import models.user  # noqa: F401 — ensures models are registered on Base
    import models.assessment  # noqa: F401
    Base.metadata.create_all(bind=engine)
