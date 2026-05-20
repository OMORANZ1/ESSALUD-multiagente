import json
import re
from typing import Any

from backend.core.groq_client import GroqClientError, call_groq
from backend.core.schemas import RouteDecision


SYSTEM_PROMPT = """
Eres el orquestador del sistema multiagente de EsSalud. Tu única función es analizar
el mensaje del usuario y responder ÚNICAMENTE con un JSON válido:
{"agent":"citas"|"informativo"|"reclamos"|"derivacion","intent":"descripción breve","urgency":"normal"|"urgente"}
No agregues texto adicional. Solo el JSON.
""".strip()

VALID_AGENTS = {"citas", "informativo", "reclamos", "derivacion"}


async def route_to_agent(
    user_message: str,
    history: list[dict[str, Any]],
    session_state: dict[str, Any],
) -> tuple[RouteDecision, int]:
    messages = [
        *history[-8:],
        {
            "role": "user",
            "content": (
                f"Mensaje actual: {user_message}\n"
                f"Estado compartido: agente_activo={session_state.get('active_agent')}, "
                f"paciente={session_state.get('patient_name')}, dni={session_state.get('patient_dni')}"
            ),
        },
    ]
    try:
        response = await call_groq(SYSTEM_PROMPT, messages, temperature=0)
        decision = _parse_route(response["content"])
        return decision, response["tokens_used"]
    except (GroqClientError, ValueError, KeyError, json.JSONDecodeError):
        return _fallback_route(user_message), 0


def _parse_route(content: str) -> RouteDecision:
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError("El orquestador no devolvió JSON")
    data = json.loads(match.group(0))
    agent = str(data.get("agent", "")).lower().strip()
    if agent not in VALID_AGENTS:
        raise ValueError(f"Agente inválido: {agent}")
    urgency = str(data.get("urgency", "normal")).lower().strip()
    if urgency not in {"normal", "urgente"}:
        urgency = "normal"
    return RouteDecision(
        agent=agent,
        intent=str(data.get("intent", "consulta general")).strip() or "consulta general",
        urgency=urgency,
    )


def _fallback_route(message: str) -> RouteDecision:
    text = message.lower()
    urgent_words = ("emergencia", "urgente", "dolor fuerte", "sangrado", "accidente", "desmayo")
    urgency = "urgente" if any(word in text for word in urgent_words) else "normal"

    if any(word in text for word in ("cita", "agendar", "reservar", "cancelar", "reprogramar")):
        return RouteDecision(agent="citas", intent="gestión de cita médica", urgency=urgency)
    if any(word in text for word in ("reclamo", "queja", "maltrato", "demora", "expediente")):
        return RouteDecision(agent="reclamos", intent="registro o seguimiento de reclamo", urgency=urgency)
    if any(word in text for word in ("especialista", "derivación", "derivacion", "referencia", "traumatólogo", "cardiólogo")):
        return RouteDecision(agent="derivacion", intent="orientación para derivación médica", urgency=urgency)
    return RouteDecision(agent="informativo", intent="información general de EsSalud", urgency=urgency)
