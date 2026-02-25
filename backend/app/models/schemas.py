"""Milimo Quantum — Pydantic Models & Schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────

class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    CODE = "code"
    RESEARCH = "research"
    CHEMISTRY = "chemistry"
    FINANCE = "finance"
    OPTIMIZATION = "optimization"
    CRYPTO = "crypto"
    QML = "qml"
    CLIMATE = "climate"
    PLANNING = "planning"
    QGI = "qgi"
    SENSING = "sensing"
    NETWORKING = "networking"
    DWAVE = "dwave"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ArtifactType(str, Enum):
    CODE = "code"
    CIRCUIT = "circuit"
    RESULTS = "results"
    NOTEBOOK = "notebook"
    REPORT = "report"


# ── Chat ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    agent: AgentType | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    artifacts: list[Artifact] = []


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ArtifactType
    title: str
    content: str
    language: str | None = None  # For code artifacts
    metadata: dict[str, Any] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    agent: AgentType | None = None


class ChatResponse(BaseModel):
    message: ChatMessage
    conversation_id: str


# ── Quantum ────────────────────────────────────────────────────────

class CircuitRequest(BaseModel):
    qasm: str | None = None
    code: str | None = None
    shots: int = 1024
    backend: str = "aer_simulator"


class ExecutionResult(BaseModel):
    counts: dict[str, int]
    circuit_svg: str
    num_qubits: int
    depth: int
    shots: int
    execution_time_ms: float
    backend: str


# ── Platform ───────────────────────────────────────────────────────

class PlatformInfo(BaseModel):
    os: str
    arch: str
    torch_device: str
    aer_device: str
    llm_backend: str
    gpu_available: bool
    gpu_name: str | None = None


# ── Projects ───────────────────────────────────────────────────────

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    messages: list[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── SSE Events ─────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    event: str  # "token", "artifact", "done", "error"
    data: Any
