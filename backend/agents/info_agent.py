from typing import Any

from backend.core.groq_client import GroqClientError, call_groq


SYSTEM_PROMPT = """
Eres el agente de información general de EsSalud.
Manejas: horarios, ubicaciones de sedes, coberturas del seguro, trámites, telemedicina.
Horarios: Lun-Vie 7am-7pm, Emergencias 24h.
Sedes: Hospital Almenara (La Victoria), Rebagliati (Jesús María), Sabogal (Callao).
Cobertura: atención médica, medicamentos, maternidad, emergencias, rehabilitación.
App: EsSalud en Línea. Responde en español, claro y estructurado.
""".strip()


async def handle(message: str, history: list[dict[str, Any]], session_state: dict[str, Any]) -> tuple[str, int]:
    try:
        response = await call_groq(SYSTEM_PROMPT, [*history[-10:], {"role": "user", "content": message}])
        return response["content"], response["tokens_used"]
    except GroqClientError:
        return _fallback(message), 0


def _fallback(message: str) -> str:
    text = message.lower()
    if "horario" in text:
        return "Los horarios generales de atención son de lunes a viernes de 7:00 a.m. a 7:00 p.m. Emergencias atiende las 24 horas."
    if any(word in text for word in ("sede", "hospital", "ubicación", "ubicacion")):
        return "Sedes principales: Hospital Almenara en La Victoria, Rebagliati en Jesús María y Sabogal en el Callao."
    if any(word in text for word in ("cobertura", "seguro", "cubre")):
        return "La cobertura incluye atención médica, medicamentos, maternidad, emergencias y rehabilitación, según tu condición de asegurado."
    return "Puedo orientarte sobre horarios, sedes, coberturas, trámites y la app EsSalud en Línea. ¿Qué información necesitas revisar?"
