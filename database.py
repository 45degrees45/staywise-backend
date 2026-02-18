"""
database.py — SQLAlchemy engine, session factory, and declarative base.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load .env before reading any env vars (module is imported before main.py runs load_dotenv)
load_dotenv()

# ── Database URL ──────────────────────────────────────────────────────────────
# Default: SQLite file inside /app/data (persistent volume on Render/Railway)
# Override DATABASE_URL in .env for Postgres in production.
_data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
_data_dir.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_data_dir}/staywise.db")

_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yield a database session, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
