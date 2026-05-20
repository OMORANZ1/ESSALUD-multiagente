import time
from collections.abc import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.agents import citas_agent, derivacion_agent, info_agent, reclamos_agent
from backend.agents.orchestrator_agent import route_to_agent
from backend.config.settings import settings
from backend.core.schemas import ChatRequest, ChatResponse, HealthResponse
from backend.core.session_manager import (
    active_sessions_count,
    append_message,
    get_metrics,
    get_session,
    register_turn,
    update_patient_data,
)


app = FastAPI(
    title="EsSalud Multiagente API",
    description="Chatbot web multiagente con orquestador jerárquico y estado compartido.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_HANDLERS = {
    "citas": citas_agent.handle,
    "informativo": info_agent.handle,
    "reclamos": reclamos_agent.handle,
    "derivacion": derivacion_agent.handle,
}


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"message": "EsSalud Multiagente API activa. Usa POST /api/chat."}


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        groq_configured=bool(settings.groq_api_key),
        active_sessions=active_sessions_count(),
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    started = time.perf_counter()
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="El mensaje no puede estar vacío.")

    state = get_session(request.session_id)
    session_id = state["session_id"]
    append_message(session_id, "user", message)
    update_patient_data(session_id, message)

    route, route_tokens = await route_to_agent(message, state["conversation_history"], state)
    handler = AGENT_HANDLERS.get(route.agent, info_agent.handle)
    reply, agent_tokens = await handler(message, state["conversation_history"], state)

    append_message(session_id, "assistant", reply, route.agent)
    register_turn(session_id, route.agent, route.intent, route_tokens + agent_tokens, success=True)
    latency_ms = round((time.perf_counter() - started) * 1000)

    return ChatResponse(
        reply=reply,
        agent=route.agent,
        intent=route.intent,
        trace=f"orquestador → {route.agent} · {route.intent}",
        session_id=session_id,
        metrics=get_metrics(session_id, latency_ms),
    )


@app.post("/api/chat/stream", tags=["chat"])
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    response = await chat(request)

    async def events() -> AsyncGenerator[str, None]:
        yield f"event: metadata\ndata: {response.model_dump_json()}\n\n"
        yield f"event: reply\ndata: {response.reply}\n\n"
        yield "event: done\ndata: ok\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
