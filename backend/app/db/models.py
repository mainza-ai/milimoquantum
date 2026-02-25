"""Milimo Quantum — SQLAlchemy Models.

Structured data models for conversations, experiments, users, and audit logs.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

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

    user = relationship("User", back_populates="experiments")


class AuditLog(Base):
    """Audit trail for compliance and tracking."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(36), nullable=True)
    action = Column(String(64), nullable=False)  # create | read | update | delete | execute
    resource_type = Column(String(32), nullable=False)  # conversation | experiment | circuit
    resource_id = Column(String(36), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
