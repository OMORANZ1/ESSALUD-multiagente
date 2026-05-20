from typing import Any

from backend.core.groq_client import GroqClientError, call_groq


SYSTEM_PROMPT = """
Eres el agente de derivación médica de EsSalud.
Orientas sobre: qué especialista corresponde, proceso de referencia, tiempos de espera.
Proceso: Médico de cabecera → solicita referencia → cita con especialista.
Disponibilidad: Traumatología 2d, Dermatología 1sem, Cardiología 10d, Neurología 2sem.
Si hay urgencia, indica ir directamente a Emergencias. Responde con empatía.
""".strip()


async def handle(message: str, history: list[dict[str, Any]], session_state: dict[str, Any]) -> tuple[str, int]:
    try:
        response = await call_groq(SYSTEM_PROMPT, [*history[-10:], {"role": "user", "content": message}])
        return response["content"], response["tokens_used"]
    except GroqClientError:
        return _fallback(message), 0


def _fallback(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ("urgente", "emergencia", "dolor fuerte", "sangrado", "accidente")):
        return "Por los síntomas que describes, te recomiendo acudir directamente a Emergencias para evaluación inmediata."
    if any(word in text for word in ("hueso", "rodilla", "fractura", "golpe", "trauma")):
        return "Podría corresponder Traumatología. El proceso es: médico de cabecera, solicitud de referencia y luego cita con especialista. Tiempo referencial: 2 días."
    if any(word in text for word in ("piel", "mancha", "lunar", "dermat")):
        return "Podría corresponder Dermatología. Primero solicita evaluación con médico de cabecera para la referencia. Tiempo referencial: 1 semana."
    if any(word in text for word in ("corazón", "corazon", "pecho", "cardio")):
        return "Podría corresponder Cardiología. Si hay dolor de pecho intenso o falta de aire, acude a Emergencias. Tiempo referencial: 10 días."
    return "Para derivación, el médico de cabecera evalúa tu caso y solicita la referencia al especialista adecuado. Cuéntame tus síntomas principales para orientarte mejor."
