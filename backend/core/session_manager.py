import time
import uuid
from copy import deepcopy
from typing import Any


SessionState = dict[str, Any]

_sessions: dict[str, SessionState] = {}


def create_session() -> SessionState:
    session_id = str(uuid.uuid4())
    state: SessionState = {
        "session_id": session_id,
        "patient_name": None,
        "patient_dni": None,
        "active_agent": "orquestador",
        "conversation_history": [],
        "intent_log": [],
        "tokens_used": 0,
        "queries_count": 0,
        "success_count": 0,
        "start_time": time.time(),
    }
    _sessions[session_id] = state
    return state


def get_session(session_id: str | None) -> SessionState:
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    return create_session()


def append_message(session_id: str, role: str, content: str, agent: str | None = None) -> None:
    message: dict[str, Any] = {
        "role": role,
        "content": content,
        "timestamp": time.time(),
    }
    if agent:
        message["agent"] = agent
    _sessions[session_id]["conversation_history"].append(message)


def update_patient_data(session_id: str, message: str) -> None:
    state = _sessions[session_id]
    digits = "".join(ch for ch in message if ch.isdigit())
    if len(digits) >= 8 and state.get("patient_dni") is None:
        state["patient_dni"] = digits[:8]

    lowered = message.lower()
    markers = ("me llamo ", "mi nombre es ", "soy ")
    for marker in markers:
        if marker in lowered and state.get("patient_name") is None:
            start = lowered.index(marker) + len(marker)
            candidate = message[start:].split(",")[0].split(".")[0].strip()
            if 3 <= len(candidate) <= 80:
                state["patient_name"] = candidate.title()
            break


def register_turn(
    session_id: str,
    agent: str,
    intent: str,
    tokens_used: int,
    success: bool = True,
) -> None:
    state = _sessions[session_id]
    state["active_agent"] = agent
    state["tokens_used"] += max(tokens_used, 0)
    state["queries_count"] += 1
    if success:
        state["success_count"] += 1
    state["intent_log"].append(
        {
            "agent": agent,
            "intent": intent,
            "timestamp": time.time(),
        }
    )


def get_metrics(session_id: str, latency_ms: int) -> dict[str, int]:
    state = _sessions[session_id]
    queries_count = max(state["queries_count"], 1)
    return {
        "tokens_used": state["tokens_used"],
        "latency_ms": latency_ms,
        "queries_count": state["queries_count"],
        "success_rate": round((state["success_count"] / queries_count) * 100),
    }


def active_sessions_count() -> int:
    return len(_sessions)


def snapshot(session_id: str) -> SessionState:
    return deepcopy(_sessions[session_id])
