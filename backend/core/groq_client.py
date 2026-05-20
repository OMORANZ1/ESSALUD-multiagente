import time
from typing import Any

import httpx

from backend.config.settings import settings


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClientError(RuntimeError):
    pass


async def call_groq(
    system: str,
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.25,
) -> dict[str, Any]:
    if not settings.groq_api_key:
        raise GroqClientError("GROQ_API_KEY no configurada")

    payload = {
        "model": model or settings.groq_model,
        "temperature": temperature,
        "messages": [{"role": "system", "content": system}, *_clean_messages(messages)],
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(GROQ_CHAT_COMPLETIONS_URL, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GroqClientError(f"Error al llamar a Groq: {exc}") from exc

    latency_ms = round((time.perf_counter() - started) * 1000)
    data = response.json()
    choice = data.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "").strip()
    usage = data.get("usage", {})
    return {
        "content": content,
        "tokens_used": int(usage.get("total_tokens") or 0),
        "latency_ms": latency_ms,
        "raw": data,
    }


def _clean_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    clean: list[dict[str, str]] = []
    for item in messages[-12:]:
        role = item.get("role", "user")
        if role not in {"user", "assistant"}:
            role = "user"
        content = str(item.get("content", "")).strip()
        if content:
            clean.append({"role": role, "content": content})
    return clean
