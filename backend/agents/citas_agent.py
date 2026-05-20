from typing import Any

from backend.core.groq_client import GroqClientError, call_groq


SYSTEM_PROMPT = """
Eres el agente especializado en citas médicas de EsSalud (Seguro Social de Salud del Perú).
Ayudas a: agendar nuevas citas, modificar o cancelar citas existentes, informar requisitos.
Disponibilidad simulada: Medicina general mañana 9am (Hospital Almenara), Pediatría 3 días,
Ginecología 1 semana, Traumatología 2 días, Cardiología 10 días.
Para agendar necesitas: nombre completo, DNI y especialidad.
Responde siempre en español peruano, de forma amigable y profesional.
""".strip()


async def handle(message: str, history: list[dict[str, Any]], session_state: dict[str, Any]) -> tuple[str, int]:
    try:
        response = await call_groq(SYSTEM_PROMPT, _messages(message, history, session_state))
        return response["content"], response["tokens_used"]
    except GroqClientError:
        return _fallback(message, session_state), 0


def _messages(message: str, history: list[dict[str, Any]], session_state: dict[str, Any]) -> list[dict[str, str]]:
    context = (
        "Estado compartido de sesión: "
        f"nombre={session_state.get('patient_name')}, dni={session_state.get('patient_dni')}, "
        f"agente_activo={session_state.get('active_agent')}."
    )
    return [*history[-10:], {"role": "user", "content": f"{context}\nMensaje: {message}"}]


def _fallback(message: str, session_state: dict[str, Any]) -> str:
    missing = []
    if not session_state.get("patient_name"):
        missing.append("nombre completo")
    if not session_state.get("patient_dni"):
        missing.append("DNI")
    if not any(word in message.lower() for word in ("medicina", "pediatría", "pediatria", "ginecología", "ginecologia", "traumatología", "traumatologia", "cardiología", "cardiologia")):
        missing.append("especialidad")

    if missing:
        return (
            "Claro, puedo ayudarte con tu cita en EsSalud. Para continuar necesito: "
            f"{', '.join(missing)}. Disponibilidad referencial: Medicina general mañana 9am "
            "en Hospital Almenara, Pediatría en 3 días, Ginecología en 1 semana, "
            "Traumatología en 2 días y Cardiología en 10 días."
        )
    return (
        "Listo, tengo los datos necesarios para simular la solicitud de cita. "
        "La disponibilidad más cercana se confirmará según la especialidad elegida y la sede asignada."
    )
