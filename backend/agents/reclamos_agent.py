import random
from typing import Any

from backend.core.groq_client import GroqClientError, call_groq


SYSTEM_PROMPT = """
Eres el agente de reclamos de EsSalud (Centro de Atención al Asegurado - CAS).
Gestionas: registro de quejas, seguimiento de reclamos, escalamiento.
Para registrar un reclamo necesitas: nombre, DNI, número de asegurado, descripción, fecha.
Al registrar genera un número de expediente simulado: EXP-2026-XXXXX.
Sé empático y profesional. Valida los sentimientos del asegurado.
""".strip()


async def handle(message: str, history: list[dict[str, Any]], session_state: dict[str, Any]) -> tuple[str, int]:
    try:
        response = await call_groq(SYSTEM_PROMPT, _messages(message, history, session_state), temperature=0.35)
        return response["content"], response["tokens_used"]
    except GroqClientError:
        return _fallback(message, session_state), 0


def _messages(message: str, history: list[dict[str, Any]], session_state: dict[str, Any]) -> list[dict[str, str]]:
    context = (
        "Estado compartido de sesión: "
        f"nombre={session_state.get('patient_name')}, dni={session_state.get('patient_dni')}."
    )
    return [*history[-10:], {"role": "user", "content": f"{context}\nMensaje: {message}"}]


def _fallback(message: str, session_state: dict[str, Any]) -> str:
    has_dni = bool(session_state.get("patient_dni")) or any(ch.isdigit() for ch in message)
    has_description = len(message.strip()) > 25
    if has_dni and has_description:
        return (
            "Lamento la mala experiencia. He registrado tu reclamo de manera simulada con el "
            f"expediente EXP-2026-{random.randint(10000, 99999)}. Conserva este número para seguimiento."
        )
    return (
        "Lamento lo ocurrido; vamos a registrarlo correctamente. Para crear el reclamo necesito "
        "nombre, DNI, número de asegurado, descripción de lo sucedido y fecha aproximada."
    )
