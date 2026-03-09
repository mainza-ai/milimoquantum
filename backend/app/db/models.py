"""Milimo Quantum — SQLAlchemy Models.

Structured data models for conversations, experiments, users, and audit logs.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON,
)
from sqlalchemy.orm import relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Platform user (for future Keycloak integration)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    username = Column(String(128), unique=True, nullable=False)
    email = Column(String(256), unique=True, nullable=True)
    display_name = Column(String(256), nullable=True)
    role = Column(String(32), default="user")  # user | admin | viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSON, default=dict)  # Per-user preferences

    conversations = relationship("Conversation", back_populates="user")
    experiments = relationship("Experiment", back_populates="user")


class Conversation(Base):
    """Chat conversation with messages."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(String(256), default="New Conversation")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual chat message."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(16), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    agent = Column(String(32), nullable=True)  # code | research | chemistry etc
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    conversation = relationship("Conversation", back_populates="messages")
    artifacts = relationship("Artifact", back_populates="message", cascade="all, delete-orphan")


class Artifact(Base):
    """Code, circuit, or result artifact."""
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=_uuid)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    type = Column(String(32), nullable=False)  # code | circuit | results | notebook
    title = Column(String(256), nullable=True)
    content = Column(Text, nullable=True)
    language = Column(String(32), nullable=True)  # python | qiskit | openqasm
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="artifacts")


class Experiment(Base):
    """Quantum experiment run record."""
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=_uuid)
    project = Column(String(128), default="default")
    name = Column(String(256), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    agent = Column(String(32), nullable=True)
    circuit_code = Column(Text, nullable=True)
    backend = Column(String(64), default="aer_simulator")
    shots = Column(Integer, default=1024)
    results = Column(JSON, default=dict)  # counts, metrics, etc.
    parameters = Column(JSON, default=dict)  # circuit params, error rates
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    runtime_ms = Column(Float, nullable=True)
    is_synced = Column(Boolean, default=False)

    user = relationship("User", back_populates="experiments")


class AuditLog(Base):
    """Audit trail for compliance and tracking."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(36), nullable=True)
    action = Column(String(64), nullable=False)  # create | read | update | delete | execute
    resource_type = Column(String(32), nullable=False)  # conversation | experiment | circuit
    resource_id = Column(String(128), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)


class Project(Base):
    """Workspace organizing conversations, experiments, and results."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=_uuid)
    tenant_id = Column(String(36), index=True, nullable=False, default="default-tenant")
    name = Column(String(256), nullable=False, default="New Project")
    description = Column(Text, default="")
    tags = Column(JSON, default=list)
    conversation_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BenchmarkResult(Base):
    """Persistent record of quantum-classical benchmarks."""
    __tablename__ = "benchmark_results"

    id = Column(String(36), primary_key=True, default=_uuid)
    benchmark_name = Column(String(128), nullable=False)
    problem_size = Column(Integer, nullable=False)
    backend = Column(String(64), nullable=False)
    shots = Column(Integer, default=1024)

    # Timings (stored in seconds as per benchmarking.py logic)
    preparation_time = Column(Float, nullable=True)
    quantum_exec_time = Column(Float, nullable=True)
    classical_sim_time = Column(Float, nullable=True)

    # Results & Classification
    classification = Column(String(32))  # quantum_advantage | classical_superior | quantum_only
    metrics = Column(JSON, default=dict)  # width, depth, gates
    result_summary = Column(String(128))

    timestamp = Column(DateTime, default=datetime.utcnow)


class MarketplacePlugin(Base):
    """Available plugins in the community marketplace."""
    __tablename__ = "marketplace_plugins"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    author = Column(String(128))
    description = Column(Text)
    version = Column(String(32))
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPlugin(Base):
    """Tracks which plugins a user has installed."""
    __tablename__ = "user_plugins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plugin_id = Column(String(64), ForeignKey("marketplace_plugins.id"), nullable=False)
    installed_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate installs
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
