"""Milimo Quantum — Local Offline Cache Database.

Dedicated SQLite connection manager exclusively for offline tracking
of quantum experiments. Never connects to PostgreSQL.
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base

logger = logging.getLogger(__name__)

LOCAL_DB_PATH = Path.home() / ".milimoquantum" / "local_cache.db"
LOCAL_URL = f"sqlite:///{LOCAL_DB_PATH}"

_local_engine = None
_LocalSessionFactory = None


def get_local_engine():
    global _local_engine
    if _local_engine is None:
        LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local_engine = create_engine(
            LOCAL_URL,
            echo=False,
            # SQLite specific configuration
            connect_args={"check_same_thread": False},
        )
        # Ensure schema exists in local cache
        from app.db import models
        Base.metadata.create_all(_local_engine)
        logger.info(f"Local SQLite cache engine created at {LOCAL_DB_PATH}")
    return _local_engine


def get_local_session_factory():
    global _LocalSessionFactory
    if _LocalSessionFactory is None:
        _LocalSessionFactory = sessionmaker(bind=get_local_engine(), expire_on_commit=False)
    return _LocalSessionFactory


def get_local_session() -> Session:
    """Get a new session strictly bound to the local SQLite cache."""
    factory = get_local_session_factory()
    return factory()
