"""Milimo Quantum — Database Layer.

SQLAlchemy models and connection management for PostgreSQL.
Falls back to SQLite when PostgreSQL is not configured.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


def get_database_url() -> str:
    """Get database URL from environment, defaulting to SQLite."""
    url = os.environ.get("DATABASE_URL", "")
    if url:
        # Convert postgres:// to postgresql:// for SQLAlchemy 2.x
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    # Default: local SQLite
    from pathlib import Path
    db_path = Path.home() / ".milimoquantum" / "milimoquantum.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


# ── Engine & Session Factory ──────────────────────────
_engine = None
_SessionFactory = None


def get_engine():
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = get_database_url()
        is_sqlite = url.startswith("sqlite")
        _engine = create_engine(
            url,
            echo=os.environ.get("DB_ECHO", "").lower() == "true",
            pool_pre_ping=not is_sqlite,
            pool_size=5 if not is_sqlite else 0,
            max_overflow=10 if not is_sqlite else 0,
        )
        logger.info(f"Database engine created: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory


def get_session() -> Session:
    """Get a new database session."""
    factory = get_session_factory()
    return factory()


def init_db():
    """Create all tables (for development). In production, use Alembic."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables created/verified")


def is_postgres() -> bool:
    """Check if currently using PostgreSQL."""
    return not get_database_url().startswith("sqlite")
