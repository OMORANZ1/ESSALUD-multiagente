from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class ChatMetrics(BaseModel):
    tokens_used: int
    latency_ms: int
    queries_count: int
    success_rate: int


class ChatResponse(BaseModel):
    reply: str
    agent: str
    intent: str
    trace: str
    session_id: str
    metrics: ChatMetrics


class RouteDecision(BaseModel):
    agent: str
    intent: str
    urgency: str = "normal"


class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    active_sessions: int


ConversationMessage = dict[str, Any]
