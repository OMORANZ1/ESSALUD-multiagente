const isStandaloneLocalFrontend =
  ["localhost", "127.0.0.1"].includes(window.location.hostname) &&
  ["", "5500"].includes(window.location.port);
const API_BASE = isStandaloneLocalFrontend ? "http://localhost:8000" : window.location.origin;

const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const statusPill = document.querySelector("#statusPill");
const agentButtons = [...document.querySelectorAll(".agent")];
const metrics = {
  queriesCount: document.querySelector("#queriesCount"),
  tokensUsed: document.querySelector("#tokensUsed"),
  successRate: document.querySelector("#successRate"),
  latency: document.querySelector("#latency"),
};

let sessionId = localStorage.getItem("essalud_session_id");

const examples = [
  "Quiero agendar una cita para medicina general.",
  "¿Cuál es el horario del Hospital Almenara?",
  "Deseo registrar un reclamo por demora en atención.",
];

function addMessage(role, text, meta = "") {
  const bubble = document.createElement("article");
  bubble.className = `message ${role}`;
  if (meta) {
    const label = document.createElement("span");
    label.className = "message-meta";
    label.textContent = meta;
    bubble.appendChild(label);
  }
  const body = document.createElement("div");
  body.textContent = text;
  bubble.appendChild(body);
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function setActiveAgent(agent) {
  agentButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.agent === agent);
  });
}

function updateMetrics(data) {
  metrics.queriesCount.textContent = data.queries_count;
  metrics.tokensUsed.textContent = data.tokens_used;
  metrics.successRate.textContent = `${data.success_rate}%`;
  metrics.latency.textContent = `${data.latency_ms} ms`;
}

function setStatus(text, isError = false) {
  statusPill.textContent = text;
  statusPill.classList.toggle("error", isError);
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    if (!response.ok) throw new Error("Backend no disponible");
    const data = await response.json();
    setStatus(data.groq_configured ? "Groq activo" : "Modo fallback");
  } catch {
    setStatus("Backend offline", true);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);
  input.value = "";
  input.disabled = true;
  form.querySelector("button").disabled = true;
  setStatus("Procesando");

  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    sessionId = data.session_id;
    localStorage.setItem("essalud_session_id", sessionId);
    addMessage("assistant", data.reply, `${data.agent} · ${data.intent}`);
    setActiveAgent(data.agent);
    updateMetrics(data.metrics);
    setStatus("Conectado");
  } catch (error) {
    addMessage("assistant", "No pude conectar con el backend. Verifica que el servicio FastAPI esté ejecutándose.", "sistema");
    setStatus("Error", true);
  } finally {
    input.disabled = false;
    form.querySelector("button").disabled = false;
    input.focus();
  }
});

addMessage("assistant", `Hola, soy el asistente virtual multiagente de EsSalud. Puedes probar: ${examples.join(" · ")}`, "orquestador");
checkHealth();
