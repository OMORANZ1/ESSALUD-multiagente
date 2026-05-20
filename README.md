# EsSalud Multiagente

Chatbot web multiagente para EsSalud, construido con FastAPI, Groq API y frontend vanilla. El sistema usa una topología jerárquica con un orquestador central que detecta intención, enruta a subagentes especializados y mantiene estado compartido de sesión.

## Arquitectura

```text
Usuario (Web Chat)
       |
       v
+-------------------------+
|   ORQUESTADOR PRINCIPAL |
|   orchestrator_agent.py |
+-----------+-------------+
            |
            | route_to_agent()
    +-------+---------+----------+-----------+
    |                 |          |           |
    v                 v          v           v
[CITAS]       [INFORMATIVO] [RECLAMOS] [DERIVACION]
citas_agent   info_agent    reclamos   derivacion
```

## Agentes

- `orchestrator_agent.py`: analiza cada mensaje y devuelve JSON con agente, intención y urgencia.
- `citas_agent.py`: agenda, modifica o cancela citas médicas simuladas.
- `info_agent.py`: responde sobre horarios, sedes, cobertura, trámites y telemedicina.
- `reclamos_agent.py`: registra y orienta reclamos CAS con expediente simulado.
- `derivacion_agent.py`: orienta sobre especialistas, referencias y urgencias.

## Estado Compartido

Cada sesión vive en memoria con esta estructura:

```python
session_state = {
    "session_id": str,
    "patient_name": str | None,
    "patient_dni": str | None,
    "active_agent": str,
    "conversation_history": list,
    "intent_log": list,
    "tokens_used": int,
    "queries_count": int,
    "success_count": int,
    "start_time": float,
}
```

## Instalación

```bash
cd essalud-multiagente
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y coloca tu API key:

```bash
GROQ_API_KEY=tu_api_key_de_groq
GROQ_MODEL=llama-3.3-70b-versatile
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

## Ejecutar Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

Prueba principal:

```bash
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Quiero agendar una cita para cardiología\"}"
```

## Ejecutar Frontend

Abre `frontend/index.html` en el navegador. El frontend llama al backend en `http://localhost:8000`.

## Endpoint Principal

`POST /api/chat`

Request:

```json
{
  "message": "Quiero agendar una cita",
  "session_id": "abc123"
}
```

Response:

```json
{
  "reply": "Claro, puedo ayudarte...",
  "agent": "citas",
  "intent": "gestión de cita médica",
  "trace": "orquestador → citas · gestión de cita médica",
  "session_id": "abc123",
  "metrics": {
    "tokens_used": 342,
    "latency_ms": 1240,
    "queries_count": 1,
    "success_rate": 100
  }
}
```

## Casos de Prueba para Demo

1. Citas: `Quiero agendar una cita para medicina general. Me llamo Ana Torres y mi DNI es 12345678.`
2. Informativo: `¿Cuál es el horario del Hospital Almenara?`
3. Reclamos: `Quiero registrar un reclamo por demora en atención. Mi DNI es 87654321.`
4. Derivación: `Tengo dolor fuerte en la rodilla, ¿qué especialista me corresponde?`
5. Urgencia: `Tengo dolor de pecho urgente y falta de aire.`

## Robustez

- Si Groq no está configurado o devuelve un JSON inválido, el orquestador usa un fallback por palabras clave.
- Los subagentes también tienen respuestas locales de respaldo para mantener la demo funcional.
- CORS está habilitado para conectar el frontend con FastAPI.
- `.env` está excluido por `.gitignore`.
