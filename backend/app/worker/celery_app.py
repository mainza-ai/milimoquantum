"""Milimo Quantum — Celery Worker App.

Configures the Celery application for asynchronous job orchestration.
Requires a Redis broker and result backend.
"""
from __future__ import annotations

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

# Redis URLs from environment or defaults
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

app = Celery(
    "milimoquantum_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

# Optional configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Route quantum jobs to specific queues if needed later
    task_routes={
        "app.worker.tasks.execute_quantum_circuit": {"queue": "quantum"},
    },
)

logger.info(f"Initialized Celery worker with broker {CELERY_BROKER_URL}")

if __name__ == "__main__":
    app.start()
