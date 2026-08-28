/**
 * Demo funcional del canal WhatsApp PIR.
 * Conecta con POST /diagnostico cuando el backend está activo.
 */

const API_BASE = window.location.port === "8080"
  ? "http://127.0.0.1:8001"
  : "";

const MENU =
  "Hola. Somos el Pasaporte Inteligente de Recuperación.\n" +
  "¿Qué necesita recuperar primero?\n\n" +
  "1 — Ayuda inmediata\n" +
  "2 — Recuperar mi vivienda\n" +
  "3 — Recuperar mis ingresos\n\n" +
  "Responda 1, 2 o 3.\n" +
  "También puede escribir: mi pasaporte";

const PASOS = {
  "1": [
    ["municipio", "¿En qué municipio se encuentra?"],
    ["personas_hogar", "¿Cuántas personas conforman su hogar? (número)"],
    ["necesidad", "¿Cuál es su necesidad principal?\n(alojamiento, alimentación, agua, medicamentos, servicios básicos)"],
    ["urgencia", "Nivel de urgencia: baja, media o alta."],
    ["evidencia", "Indique evidencia disponible (descripción breve) o escriba «no»."],
  ],
  "2": [
    ["municipio", "¿En qué municipio está la vivienda afectada?"],
    ["tipo_afectacion", "Tipo de afectación (estructural, grietas, techo, servicios — separados por coma)."],
    ["habitabilidad", "Habitabilidad: habitable, parcialmente habitable o no habitable."],
    ["servicios_afectados", "Servicios afectados (agua, luz, gas, drenaje, ninguno)."],
    ["evidencia", "Describa los daños observados o escriba «no» si no tiene evidencia."],
  ],
  "3": [
    ["municipio", "¿En qué municipio ocurre la afectación?"],
    ["actividad_economica", "¿Qué actividad económica realiza?"],
    ["danos", "¿Qué daño o pérdida principal registró?"],
    ["puede_operar", "¿Puede continuar operando? Responda sí o no."],
    ["necesidades", "¿Qué necesita para recuperarse? (equipamiento, dinero, reparación — separados por coma)"],
  ],
};

const TIPOS = { "1": "ayuda_inmediata", "2": "vivienda", "3": "ingresos" };

const EJEMPLO = [
  "hola", "3", "Cali", "Tienda de abarrotes", "Pérdida de inventario",
  "no", "equipamiento, dinero",
];

let state = { route: null, step: 0, data: {}, pasaporte: null, busy: false };
let apiOnline = false;

const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const jsonOut = document.getElementById("json-out");
const apiStatus = document.getElementById("api-status");

function addBubble(text, kind = "bot") {
  const el = document.createElement("div");
  el.className = `wa-bubble wa-bubble--${kind}`;
  el.textContent = text;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

function parseList(text) {
  return text.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
}

function validate(campo, valor, route) {
  const v = (valor || "").trim();
  const cl = v.toLowerCase();
  if (campo === "municipio" && v.length < 2) return "Indique un municipio válido.";
  if (campo === "personas_hogar" && (!/^\d+$/.test(v) || parseInt(v, 10) < 1))
    return "Indique un número de personas válido (1 o más).";
  if (campo === "urgencia" && !["baja", "media", "alta"].includes(cl))
    return "Responda: baja, media o alta.";
  if (campo === "habitabilidad" && !/(habitable|no habitable|parcial)/.test(cl))
    return "Indique habitabilidad: habitable, parcialmente habitable o no habitable.";
  if (campo === "puede_operar" && !["sí", "si", "s", "no", "n"].includes(cl))
    return "Responda sí o no.";
  if ((campo === "tipo_afectacion" || campo === "servicios_afectados" || campo === "necesidades") && parseList(v).length < 1)
    return "Indique al menos un valor.";
  if (campo === "danos" && v.length < 2) return "Describa el daño o pérdida principal.";
  if (campo === "necesidad" && v.length < 2) return "Describa su necesidad principal.";
  return null;
}

function buildApiBody(data, tipo) {
  if (tipo === "ayuda_inmediata") {
    return {
      tipo_ruta: "ayuda_inmediata",
      municipio: data.municipio,
      personas_hogar: parseInt(data.personas_hogar, 10),
      necesidad: data.necesidad,
      urgencia: data.urgencia.toLowerCase(),
      evidencia: data.evidencia === "no" ? "" : data.evidencia || "",
    };
  }
  if (tipo === "vivienda") {
    return {
      tipo_ruta: "vivienda",
      municipio: data.municipio,
      tipo_afectacion: parseList(data.tipo_afectacion),
      habitabilidad: data.habitabilidad,
      servicios_afectados: parseList(data.servicios_afectados),
      evidencia: data.evidencia === "no" ? "" : data.evidencia || "",
    };
  }
  return {
    tipo_ruta: "ingresos",
    municipio: data.municipio,
    actividad_economica: data.actividad_economica,
    danos: parseList(data.danos).length ? parseList(data.danos) : [data.danos],
    puede_operar: ["sí", "si", "s"].includes((data.puede_operar || "").toLowerCase()),
    necesidades: parseList(data.necesidades),
  };
}

function formatPasaporte(p, resultado, ia) {
  const ayudas = (p.ayudas || []).slice(0, 3);
  const ayudasTxt = ayudas.length
    ? `\n\nEncontramos ${(p.ayudas || []).length} alternativa(s) disponible(s):\n` +
      ayudas.map((a) => `• ${a.nombre}`).join("\n")
    : "";
  const barrera = resultado?.barrera_principal
    ? `\n\nBarrera principal: ${resultado.barrera_principal}`
    : "";
  const prioIcon = p.prioridad_nivel === "rojo" ? "🔴" : p.prioridad_nivel === "verde" ? "🟢" : "🟡";
  const confIcon = p.confianza_nivel === "rojo" ? "🔴" : p.confianza_nivel === "verde" ? "🟢" : "🟡";

  let iaTxt = "";
  if (ia?.activo && ia.recomendacion_ia?.ruta_recuperacion) {
    iaTxt = `\n\nRecomendación IA:\n${ia.recomendacion_ia.ruta_recuperacion}`;
  }
  if (ia?.confianza_ia?.etiqueta) {
    iaTxt += `\nEvaluación: ${ia.confianza_ia.etiqueta}`;
  }

  return (
    `Pasaporte de Recuperación\n` +
    `ID: ${p.id}\n\n` +
    `Ubicación: ${p.municipio}\n` +
    `${confIcon} Confianza: ${p.confianza_etiqueta}\n` +
    `${prioIcon} Prioridad: ${p.prioridad_etiqueta}\n` +
    `Progreso: ${p.progreso}%\n\n` +
    `${p.ruta_nombre || resultado?.ruta_nombre}\n` +
    `${resultado?.que_hacer_primero || p.que_hacer_primero}` +
    barrera +
    ayudasTxt +
    iaTxt +
    `\n\nSiguiente acción:\n${(p.ruta && p.ruta[0]) || "Consulte su ruta completa"}\n\n` +
    `Conserve su ID. Escriba «mi pasaporte» para consultar el avance.`
  );
}

async function emitirPasaporte(data, routeKey) {
  const tipo = TIPOS[routeKey];
  const body = buildApiBody(data, tipo);

  if (apiOnline) {
    try {
      const res = await fetch(`${API_BASE}/diagnostico`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      state.pasaporte = json.pasaporte;
      addBubble(formatPasaporte(json.pasaporte, json.resultado, json.ia), "bot");
      jsonOut.textContent = JSON.stringify(json, null, 2);
      return;
    } catch {
      addBubble("No fue posible registrar en el servidor. Mostrando respuesta local.", "system");
    }
  }

  const local = buildLocalResponse(body, tipo);
  state.pasaporte = local.pasaporte;
  addBubble(formatPasaporte(local.pasaporte, local.resultado, null), "bot");
  jsonOut.textContent = JSON.stringify(local, null, 2);
}

function buildLocalResponse(body, tipo) {
  const id = `PAS-${String(Math.floor(Math.random() * 9000) + 1000)}`;
  const cfg = {
    ayuda_inmediata: {
      ruta_nombre: "Ayuda inmediata",
      ruta: ["Contactar punto de atención municipal", "Registrar necesidad urgente", "Solicitar kit básico"],
      barrera: "Capacidad limitada de alojamiento temporal",
      prioridad: body.urgencia === "alta" ? "Alta" : "Media",
    },
    vivienda: {
      ruta_nombre: "Recuperar vivienda",
      ruta: ["Solicitar visita técnica", "Documentar daños", "Coordinar reparación de servicios"],
      barrera: "Evaluación de habitabilidad pendiente",
      prioridad: /no habitable/.test(body.habitabilidad || "") ? "Alta" : "Media",
    },
    ingresos: {
      ruta_nombre: "Recuperar ingresos",
      ruta: ["Documentar pérdidas", "Solicitar capital de trabajo", "Reactivar operación"],
      barrera: "Falta de capital de trabajo",
      prioridad: body.puede_operar ? "Media" : "Alta",
    },
  }[tipo];

  const pasaporte = {
    id,
    tipo_ruta: tipo,
    municipio: body.municipio,
    ruta_nombre: cfg.ruta_nombre,
    prioridad_etiqueta: cfg.prioridad,
    prioridad_nivel: cfg.prioridad === "Alta" ? "rojo" : "amarillo",
    confianza_etiqueta: body.evidencia ? "Alta confianza" : "Requiere validación",
    confianza_nivel: body.evidencia ? "verde" : "amarillo",
    progreso: 0,
    ruta: cfg.ruta,
    que_hacer_primero: cfg.ruta[0],
    ayudas: [
      { nombre: "Orientación programas compatibles", categoria: "Institucional" },
      { nombre: "Apoyo demostrativo equipamiento", categoria: "Equipamiento" },
    ],
  };
  const resultado = {
    ruta_nombre: cfg.ruta_nombre,
    que_hacer_primero: cfg.ruta[0],
    ruta: cfg.ruta,
    barrera_principal: cfg.barrera,
    ayudas: pasaporte.ayudas,
  };
  return { diagnostico: body, resultado, pasaporte, _modo: "local" };
}

async function processMessage(text) {
  if (state.busy) return;
  const msg = (text || "").trim();
  const low = msg.toLowerCase();
  if (!msg) return;

  addBubble(msg, "user");

  if (low === "menu" || low === "hola" || low === "inicio") {
    state = { route: null, step: 0, data: {}, pasaporte: null, busy: false };
    addBubble(MENU, "bot");
    return;
  }

  if (state.pasaporte && (low === "mi pasaporte" || low === "pasaporte")) {
    const p = state.pasaporte;
    addBubble(
      `Pasaporte ${p.id}\n` +
        `Progreso: ${p.progreso}%\n` +
        `Estado: ${p.estado || "En recuperación"}\n` +
        `Siguiente paso: ${(p.ruta && p.ruta[0]) || "—"}`,
      "bot"
    );
    jsonOut.textContent = JSON.stringify({ pasaporte: p }, null, 2);
    return;
  }

  if (!state.route) {
    if (!["1", "2", "3"].includes(low)) {
      addBubble("Opción no reconocida. Responda 1, 2 o 3.", "error");
      return;
    }
    state.route = low;
    state.step = 0;
    addBubble(PASOS[low][0][1], "bot");
    return;
  }

  const pasos = PASOS[state.route];
  const [campo, pregunta] = pasos[state.step];
  const err = validate(campo, msg, state.route);
  if (err) {
    addBubble(err, "error");
    addBubble(pregunta, "bot");
    return;
  }

  state.data[campo] = msg;
  state.step += 1;

  if (state.step >= pasos.length) {
    state.busy = true;
    input.disabled = true;
    addBubble("Procesando su diagnóstico…", "system");
    await emitirPasaporte(state.data, state.route);
    state.busy = false;
    input.disabled = false;
    return;
  }

  addBubble(pasos[state.step][1], "bot");
}

function resetChat() {
  state = { route: null, step: 0, data: {}, pasaporte: null, busy: false };
  chat.innerHTML = "";
  jsonOut.textContent = "Inicie una conversación o seleccione una ruta.";
  input.disabled = false;
  addBubble(MENU, "bot");
}

async function runAutoDemo() {
  resetChat();
  for (const msg of EJEMPLO) {
    await new Promise((r) => setTimeout(r, 500));
    await processMessage(msg);
  }
}

async function checkApi() {
  try {
    const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(3000) });
    apiOnline = res.ok;
  } catch {
    apiOnline = false;
  }
  apiStatus.textContent = apiOnline ? "API conectada" : "Modo local (sin backend)";
  apiStatus.className = `wa-demo__status ${apiOnline ? "wa-demo__status--ok" : "wa-demo__status--off"}`;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  processMessage(input.value);
  input.value = "";
});

document.getElementById("btn-reset").addEventListener("click", resetChat);
document.getElementById("btn-auto").addEventListener("click", runAutoDemo);

document.querySelectorAll(".wa-route-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    resetChat();
    processMessage(btn.dataset.route);
  });
});

checkApi();
resetChat();
