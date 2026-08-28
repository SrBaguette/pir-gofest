const API_BASE = window.location.port === "8080"
  ? "http://127.0.0.1:8001"
  : "";
const API_URL = `${API_BASE}/diagnostico`;
const DASHBOARD_POLL_MS = 30000;

const ACTIVIDADES = [
  "Tienda",
  "Restaurante",
  "Taller",
  "Panadería",
  "Agricultura",
  "Otro",
];

const DANOS = [
  "Maquinaria",
  "Equipos",
  "Herramientas",
  "Local",
  "Infraestructura",
  "Vivienda",
  "Mercancía",
  "Espacio",
  "Otro",
];

const NECESIDADES = [
  "Equipamiento",
  "Dinero",
  "Financiamiento",
  "Reparación",
  "Insumos",
  "Transporte",
  "Espacio",
];

const NECESIDADES_INMEDIATAS = [
  "Alimentación",
  "Alojamiento",
  "Agua",
  "Medicamentos",
  "Servicios básicos",
  "Otro",
];

const URGENCIAS = ["Baja", "Media", "Alta"];

const AFECTACIONES_VIVIENDA = [
  "Estructural",
  "Grietas",
  "Techo",
  "Servicios",
  "Otro",
];

const HABITABILIDAD = [
  "Habitable",
  "Parcialmente habitable",
  "No habitable",
];

const SERVICIOS_VIVIENDA = [
  "Agua",
  "Luz",
  "Gas",
  "Drenaje",
  "Ninguno",
];

const state = {
  screen: "welcome",
  tipo_ruta: null,
  step: 0,
  municipio: "",
  actividad_economica: "",
  actividad_otro: "",
  danos: [],
  dano_otro: "",
  puede_operar: null,
  necesidades: [],
  personas_hogar: "",
  necesidad_inmediata: "",
  necesidad_otro: "",
  urgencia: "",
  tipo_afectacion: [],
  afectacion_otro: "",
  habitabilidad: "",
  servicios_afectados: [],
  evidencia: "",
  resultado: null,
  pasaporte: null,
  ia: null,
  diagnostico: null,
  nombre: "",
  pasaporteLookupId: "",
  showAyudas: true,
  dashboardData: null,
  dashboardUpdatedAt: null,
  mapaInstance: null,
  error: "",
  loading: false,
};

const app = document.getElementById("app");
const headerNav = document.getElementById("header-nav");
const headerInner = document.querySelector(".header__inner");
const toast = document.getElementById("toast");
let dashboardInterval = null;

function toBackendValue(text) {
  return text.trim().toLowerCase();
}

function isDashboardView() {
  return window.location.hash === "#dashboard";
}

function updateHeader() {
  const enDashboard = isDashboardView();
  headerInner.classList.toggle("header__inner--wide", enDashboard);
  headerNav.innerHTML = `
    <a href="#" class="header__link ${!enDashboard ? "header__link--active" : ""}" data-nav="persona">
      Persona
    </a>
    <a href="#dashboard" class="header__link ${enDashboard ? "header__link--active" : ""}" data-nav="dashboard">
      Entidades
    </a>
  `;

  headerNav.querySelector('[data-nav="persona"]').addEventListener("click", (event) => {
    event.preventDefault();
    stopDashboardPolling();
    window.location.hash = "";
    render();
  });
}

function render() {
  updateHeader();

  if (isDashboardView()) {
    app.classList.add("main--dashboard");
    renderDashboardView();
    return;
  }

  app.classList.remove("main--dashboard");
  app.classList.toggle("main--persona-home", state.screen === "result");
  stopDashboardPolling();

  if (state.screen === "welcome") {
    app.innerHTML = renderWelcome();
    bindWelcome();
    return;
  }

  if (state.screen === "route-select") {
    app.innerHTML = renderRouteSelect();
    bindRouteSelect();
    return;
  }

  if (state.screen === "quiz") {
    app.innerHTML = renderQuiz();
    bindQuiz();
    return;
  }

  if (state.screen === "loading") {
    app.innerHTML = renderLoading();
    return;
  }

  if (state.screen === "pasaporte-lookup") {
    app.innerHTML = renderPasaporteLookup();
    bindPasaporteLookup();
    return;
  }

  if (state.screen === "pasaporte-view") {
    app.innerHTML = renderPasaporteView();
    bindPasaporteView();
    return;
  }

  if (state.screen === "result") {
    app.innerHTML = renderResult();
    bindResult();
    return;
  }
}

function getTotalSteps() {
  return 5;
}

function renderRouteSelect() {
  return `
    <section class="card">
      <h2 class="question__title">¿Qué necesitas recuperar primero?</h2>
      <p class="question__hint">Elige una ruta. Cada una tiene un flujo de 5 pasos.</p>
      <div class="route-cards">
        ${renderRouteCard("ayuda_inmediata", "Ayuda inmediata", "Alimentación, alojamiento, agua, medicamentos, servicios básicos.", "inmediata")}
        ${renderRouteCard("vivienda", "Recuperar vivienda", "Daños estructurales, habitabilidad y servicios afectados.", "vivienda")}
        ${renderRouteCard("ingresos", "Recuperar ingresos", "Comercio, emprendimiento, producción o trabajo independiente.", "ingresos")}
      </div>
      ${state.error ? `<p class="error-msg">${state.error}</p>` : ""}
      <div class="actions">
        <button type="button" class="btn btn--secondary" id="btn-back-welcome">Atrás</button>
        <button type="button" class="btn btn--primary" id="btn-route-continue">Continuar</button>
      </div>
    </section>
  `;
}

function bindRouteSelect() {
  document.querySelectorAll(".route-card").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.tipo_ruta = btn.dataset.route;
      state.error = "";
      render();
    });
  });

  document.getElementById("btn-back-welcome").addEventListener("click", () => {
    state.screen = "welcome";
    state.tipo_ruta = null;
    state.error = "";
    render();
  });

  document.getElementById("btn-route-continue").addEventListener("click", () => {
    if (!state.tipo_ruta) {
      state.error = "Selecciona una ruta para continuar.";
      render();
      return;
    }
    state.screen = "quiz";
    state.step = 1;
    state.error = "";
    render();
  });
}

function renderPasaporteLookup() {
  return `
    <section class="card">
      <h2 class="question__title">Consultar mi pasaporte</h2>
      <p class="question__hint">Ingresa el ID que recibiste al completar tu diagnóstico (ejemplo: PAS-0001).</p>
      <input
        type="text"
        class="input-text"
        id="input-pasaporte-id"
        placeholder="PAS-0001"
        value="${escapeHtml(state.pasaporteLookupId)}"
      >
      ${state.error ? `<p class="error-msg">${state.error}</p>` : ""}
      <div class="actions">
        <button type="button" class="btn btn--secondary" id="btn-back-welcome">Atrás</button>
        <button type="button" class="btn btn--primary" id="btn-buscar-pasaporte">Consultar</button>
      </div>
    </section>
  `;
}

function renderPasaporteView() {
  const pasaporte = state.pasaporte;
  if (!pasaporte) return "";

  return `
    <section class="card">
      <p class="result__label">Pasaporte de Recuperación</p>
      <h2 class="result__title">${escapeHtml(pasaporte.ruta_nombre || "Tu progreso")}</h2>

      <div class="result__priority">
        <p class="result__priority-label">¿Qué hacer primero?</p>
        <p class="result__priority-text">${escapeHtml(pasaporte.que_hacer_primero)}</p>
      </div>

      ${renderPasaporte(pasaporte)}
      ${pasaporte.ayudas && pasaporte.ayudas.length ? renderAyudas(pasaporte.ayudas) : ""}

      <div class="result__actions">
        <button type="button" class="btn btn--secondary" id="btn-volver-inicio">Volver al inicio</button>
      </div>
    </section>
  `;
}

function bindPasaporteLookup() {
  const input = document.getElementById("input-pasaporte-id");
  input.addEventListener("input", (e) => {
    state.pasaporteLookupId = e.target.value.toUpperCase();
    state.error = "";
  });
  input.focus();

  document.getElementById("btn-back-welcome").addEventListener("click", () => {
    state.screen = "welcome";
    state.error = "";
    render();
  });

  document.getElementById("btn-buscar-pasaporte").addEventListener("click", () => {
    buscarPasaporte();
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") buscarPasaporte();
  });
}

async function buscarPasaporte() {
  const id = state.pasaporteLookupId.trim().toUpperCase();
  if (!id) {
    state.error = "Escribe el ID de tu pasaporte.";
    render();
    return;
  }

  state.screen = "loading";
  state.error = "";
  render();

  try {
    const response = await fetch(`${API_BASE}/pasaporte/${encodeURIComponent(id)}`);
    if (!response.ok) {
      throw new Error("No encontramos ese pasaporte. Verifica el ID e intenta de nuevo.");
    }
    state.pasaporte = await response.json();
    state.screen = "pasaporte-view";
    render();
  } catch (error) {
    state.screen = "pasaporte-lookup";
    state.error = error.message || "No pudimos consultar el pasaporte.";
    render();
  }
}

function bindPasaporteView() {
  bindPasaporteActions();
  document.getElementById("btn-volver-inicio").addEventListener("click", () => {
    resetFormState();
    render();
  });
}

function bindPasaporteActions() {
  document.querySelectorAll(".accion-item input[type='checkbox']:not(:disabled)").forEach((checkbox) => {
    checkbox.addEventListener("change", async (event) => {
      if (!event.target.checked || !state.pasaporte) return;
      await marcarAccion(parseInt(event.target.dataset.accion, 10));
    });
  });
}

function renderWelcome() {
  return `
    <section class="card card--welcome">
      <h1 class="welcome__title">¿Qué necesitas recuperar?</h1>
      <p class="welcome__subtitle">
        Diagnóstico guiado en 5 pasos. Al finalizar recibes tu Pasaporte de Recuperación con ruta y ayudas compatibles.
      </p>
      <div class="welcome__channels">
        ${renderSemaforo("verde", "Web")}
        <a href="whatsapp-demo.html" class="welcome__wa-link">${renderSemaforo("amarillo", "WhatsApp")}</a>
      </div>
      <div class="actions actions--single">
        <button type="button" class="btn btn--primary btn--wide" id="btn-start">
          Iniciar diagnóstico
        </button>
        <a href="whatsapp-demo.html" class="btn btn--accent btn--wide" style="text-align:center;text-decoration:none;display:inline-flex;align-items:center;justify-content:center">
          Canal WhatsApp (demo)
        </a>
        <button type="button" class="btn btn--accent btn--wide" id="btn-consultar-pasaporte">
          Consultar pasaporte
        </button>
        <button type="button" class="btn btn--secondary btn--wide" id="btn-dashboard">
          Panel de entidades
        </button>
      </div>
      <p class="welcome__hint">Si ya tienes un ID (PAS-0001), usa consultar pasaporte.</p>
    </section>
  `;
}

function renderProgress() {
  const total = getTotalSteps();
  const current = state.step;
  const percent = (current / total) * 100;

  return `
    <div class="progress">
      <div class="progress__label">
        <span>Paso ${current} de ${total}</span>
        <span>${Math.round(percent)}%</span>
      </div>
      <div class="progress__bar" role="progressbar" aria-valuenow="${current}" aria-valuemin="0" aria-valuemax="${total}">
        <div class="progress__fill" style="width: ${percent}%"></div>
      </div>
    </div>
  `;
}

function renderQuiz() {
  const content = getStepContent();
  const isFirst = state.step === 1;
  const isLast = state.step === getTotalSteps();

  return `
    <section class="card">
      ${state.tipo_ruta ? `<p class="quiz-route-badge">Ruta: ${escapeHtml(getRouteLabel(state.tipo_ruta))}</p>` : ""}
      ${renderProgress()}
      <h2 class="question__title">${content.title}</h2>
      ${content.hint ? `<p class="question__hint">${content.hint}</p>` : ""}
      ${content.body}
      ${state.error ? `<p class="error-msg">${state.error}</p>` : ""}
      <div class="actions">
        ${!isFirst ? `<button type="button" class="btn btn--secondary" id="btn-back">Atrás</button>` : ""}
        <button type="button" class="btn btn--primary" id="btn-next">
          ${isLast ? "Ver mi ruta" : "Continuar"}
        </button>
      </div>
    </section>
  `;
}

function getStepContent() {
  if (state.tipo_ruta === "ayuda_inmediata") return getStepAyudaInmediata();
  if (state.tipo_ruta === "vivienda") return getStepVivienda();
  return getStepIngresos();
}

function renderStepMunicipioNombre() {
  return `
    <div class="field-stack">
      <label class="input-label" for="input-municipio">Municipio</label>
      <input type="text" class="input-text" id="input-municipio" placeholder="Ejemplo: Cali" value="${escapeHtml(state.municipio)}">
      <label class="input-label" for="input-nombre">Tu nombre (opcional)</label>
      <input type="text" class="input-text" id="input-nombre" placeholder="Ejemplo: María" value="${escapeHtml(state.nombre)}">
    </div>
  `;
}

function getStepAyudaInmediata() {
  switch (state.step) {
    case 1:
      return {
        title: "¿En qué municipio ocurrió la afectación?",
        hint: "Escribe el municipio. Tu nombre es opcional para personalizar tu plan.",
        body: renderStepMunicipioNombre(),
      };
    case 2:
      return {
        title: "¿Cuántas personas hay en tu hogar?",
        hint: "Incluye a todas las personas que viven contigo.",
        body: `<input type="number" min="1" class="input-text" id="input-personas" placeholder="Ejemplo: 4" value="${escapeHtml(state.personas_hogar)}">`,
      };
    case 3:
      return {
        title: "¿Cuál es tu necesidad principal?",
        hint: "Selecciona la más urgente.",
        body: `
          <div class="options">${NECESIDADES_INMEDIATAS.map((item) => optionButton("necesidad_inmediata", item, state.necesidad_inmediata === item)).join("")}</div>
          ${state.necesidad_inmediata === "Otro" ? `<div class="other-input"><input type="text" class="input-text" id="input-necesidad-otro" placeholder="Describe tu necesidad" value="${escapeHtml(state.necesidad_otro)}"></div>` : ""}
        `,
      };
    case 4:
      return {
        title: "¿Qué tan urgente es?",
        hint: "Indica el nivel de urgencia.",
        body: `<div class="options">${URGENCIAS.map((item) => optionButton("urgencia", item, state.urgencia === item)).join("")}</div>`,
      };
    case 5:
      return {
        title: "¿Tienes alguna evidencia o detalle adicional?",
        hint: "Opcional. Puedes describir brevemente la situación.",
        body: `<input type="text" class="input-text" id="input-evidencia" placeholder="Ejemplo: perdimos el techo de la casa" value="${escapeHtml(state.evidencia)}">`,
      };
    default:
      return { title: "", body: "" };
  }
}

function getStepVivienda() {
  switch (state.step) {
    case 1:
      return {
        title: "¿En qué municipio está tu vivienda?",
        hint: "Escribe el municipio. Tu nombre es opcional para personalizar tu plan.",
        body: renderStepMunicipioNombre(),
      };
    case 2:
      return {
        title: "¿Qué tipo de afectación tiene tu vivienda?",
        hint: "Puedes seleccionar más de una opción.",
        body: `
          <div class="options">${AFECTACIONES_VIVIENDA.map((item) => optionButton("tipo_afectacion", item, state.tipo_afectacion.includes(item), true)).join("")}</div>
          ${state.tipo_afectacion.includes("Otro") ? `<div class="other-input"><input type="text" class="input-text" id="input-afectacion-otro" placeholder="Describe la afectación" value="${escapeHtml(state.afectacion_otro)}"></div>` : ""}
        `,
      };
    case 3:
      return {
        title: "¿Tu vivienda es habitable?",
        hint: "Indica si puedes habitarla con seguridad.",
        body: `<div class="options">${HABITABILIDAD.map((item) => optionButton("habitabilidad", item, state.habitabilidad === item)).join("")}</div>`,
      };
    case 4:
      return {
        title: "¿Qué servicios están afectados?",
        hint: "Puedes seleccionar más de una opción.",
        body: `<div class="options">${SERVICIOS_VIVIENDA.map((item) => optionButton("servicios", item, state.servicios_afectados.includes(item), true)).join("")}</div>`,
      };
    case 5:
      return {
        title: "¿Tienes alguna evidencia o detalle adicional?",
        hint: "Opcional. Describe brevemente los daños.",
        body: `<input type="text" class="input-text" id="input-evidencia" placeholder="Ejemplo: grietas en muros" value="${escapeHtml(state.evidencia)}">`,
      };
    default:
      return { title: "", body: "" };
  }
}

function getRouteLabel(tipo) {
  if (tipo === "ayuda_inmediata") return "Ayuda inmediata";
  if (tipo === "vivienda") return "Recuperar vivienda";
  return "Recuperar ingresos";
}

function getStepIngresos() {
  switch (state.step) {
    case 1:
      return {
        title: "¿En qué municipio ocurrió la afectación?",
        hint: "Ruta: Recuperar ingresos. Indica dónde opera tu actividad. Tu nombre es opcional.",
        body: renderStepMunicipioNombre(),
      };

    case 2:
      return {
        title: "¿Qué actividad económica realizas?",
        hint: "Comercio, taller, agricultura u otra actividad que genere tus ingresos.",
        body: `
          <div class="options" id="options-actividad">
            ${ACTIVIDADES.map((item) => optionButton("actividad", item, state.actividad_economica === item)).join("")}
          </div>
          ${state.actividad_economica === "Otro" ? `
            <div class="other-input">
              <input
                type="text"
                class="input-text"
                id="input-actividad-otro"
                placeholder="Describe tu actividad"
                value="${escapeHtml(state.actividad_otro)}"
              >
            </div>
          ` : ""}
        `,
      };

    case 3:
      return {
        title: "¿Qué resultó afectado en tu actividad?",
        hint: "Equipos, local, mercancía u otros bienes necesarios para operar. Puedes elegir varios.",
        body: `
          <div class="options" id="options-danos">
            ${DANOS.map((item) => optionButton("danos", item, state.danos.includes(item), true)).join("")}
          </div>
          ${state.danos.includes("Otro") ? `
            <div class="other-input">
              <input
                type="text"
                class="input-text"
                id="input-dano-otro"
                placeholder="Describe qué más resultó afectado"
                value="${escapeHtml(state.dano_otro)}"
              >
            </div>
          ` : ""}
        `,
      };

    case 4:
      return {
        title: "¿Puedes continuar operando actualmente?",
        hint: "Indica si tu actividad puede seguir funcionando hoy.",
        body: `
          <div class="options" id="options-operar">
            ${optionButton("operar", "Sí", state.puede_operar === true)}
            ${optionButton("operar", "No", state.puede_operar === false)}
          </div>
        `,
      };

    case 5:
      return {
        title: "¿Qué necesitas principalmente para recuperar tus ingresos?",
        hint: "Prioriza lo que más te ayudaría a volver a operar o mantener la actividad.",
        body: `
          <div class="options" id="options-necesidades">
            ${NECESIDADES.map((item) => optionButton("necesidades", item, state.necesidades.includes(item), true)).join("")}
          </div>
        `,
      };

    default:
      return { title: "", body: "" };
  }
}

function optionButton(group, label, selected, multi = false) {
  return `
    <button
      type="button"
      class="option ${multi ? "option--multi" : ""} ${selected ? "option--selected" : ""}"
      data-group="${group}"
      data-value="${escapeHtml(label)}"
    >
      <span class="option__check" aria-hidden="true"></span>
      <span>${escapeHtml(label)}</span>
    </button>
  `;
}

function renderLoading() {
  return `
    <section class="card loading">
      <div class="loading__spinner" aria-hidden="true"></div>
      <p class="loading__text">Analizando tu situación…</p>
    </section>
  `;
}

function buildPersonaResumenIA(pasaporte, resultado, ia) {
  const rec = ia?.recomendacion_ia;
  const conf = ia?.confianza_ia;
  if (rec?.explicacion) {
    const extra = rec.ruta_recuperacion ? ` ${rec.ruta_recuperacion}` : "";
    return `${rec.explicacion}${extra}`;
  }
  if (conf?.motivos?.length) {
    return conf.motivos.join(". ") + (conf.accion_sugerida ? ` ${conf.accion_sugerida}` : "");
  }
  const municipio = pasaporte?.municipio || "tu municipio";
  const ruta = pasaporte?.ruta_nombre || resultado?.ruta_nombre || "recuperación";
  const nAyudas = (resultado?.ayudas || []).length;
  return (
    `Según tu diagnóstico, mapeamos tu **Ruta de ${ruta}** en ${municipio}. ` +
    `Hay ${nAyudas} programas compatibles con tu situación. ` +
    `Prioridad: ${resultado?.que_hacer_primero || "revisar ayudas disponibles"}.`
  ).replace(/\*\*/g, "");
}

function buildPersonaDiagnosticoFields(pasaporte, resultado) {
  const diag = state.diagnostico || {};
  let afectacion = pasaporte?.danos?.length
    ? pasaporte.danos.join(", ")
    : pasaporte?.necesidades?.join(", ") || "—";
  if (diag.tipo_afectacion?.length) {
    afectacion = diag.tipo_afectacion.join(", ");
  }
  if (diag.necesidad) {
    afectacion = diag.necesidad;
  }
  let urgencia = diag.urgencia || pasaporte?.prioridad_etiqueta || "—";
  if (typeof urgencia === "string") {
    urgencia = urgencia.charAt(0).toUpperCase() + urgencia.slice(1);
  }
  if (pasaporte?.prioridad_nivel === "rojo" && !diag.urgencia) {
    urgencia = "Crítica";
  }
  return [
    { label: "Ruta elegida", value: pasaporte?.ruta_nombre || resultado?.ruta_nombre || "—" },
    { label: "Ubicación afectada", value: `${pasaporte?.municipio || "—"}, Valle del Cauca` },
    { label: "Tipo de afectación", value: afectacion },
    { label: "Nivel de urgencia", value: urgencia, critico: pasaporte?.prioridad_nivel === "rojo" },
  ];
}

function renderPersonaStepper(pasaporte) {
  const progreso = pasaporte?.progreso || 0;
  const pasoActual = progreso >= 100 ? 5 : progreso > 0 ? 3 : 2;
  const pasos = [
    { titulo: "Diagnóstico inicial", detalle: "Completado vía web" },
    { titulo: "Emisión de pasaporte", detalle: pasaporte ? `ID ${pasaporte.id} asignado` : "Pendiente" },
    { titulo: "Selección de ayudas", detalle: "Revise los recursos compatibles" },
    { titulo: "Verificación de entidad", detalle: "Validación institucional" },
    { titulo: "Recepción de recursos", detalle: "Entrega de apoyos" },
  ];

  return `
    <ol class="persona-stepper">
      ${pasos.map((paso, index) => {
        const num = index + 1;
        let cls = "persona-stepper__item";
        if (num < pasoActual) cls += " persona-stepper__item--done";
        else if (num === pasoActual) cls += " persona-stepper__item--active";
        return `
          <li class="${cls}">
            <span class="persona-stepper__marker">${num < pasoActual ? "✓" : num}</span>
            <div>
              <p class="persona-stepper__title">${escapeHtml(paso.titulo)}</p>
              <p class="persona-stepper__detail">${escapeHtml(paso.detalle)}</p>
            </div>
          </li>
        `;
      }).join("")}
    </ol>
  `;
}

function renderPersonaRecursos(ayudas) {
  const items = ayudas || [];
  const cards = items.length > 0
    ? items.map((ayuda, index) => `
        <article class="persona-recurso">
          <div class="persona-recurso__icon" aria-hidden="true">${index === 0 ? "💼" : index === 1 ? "🏠" : "🍽"}</div>
          <div class="persona-recurso__body">
            <h4 class="persona-recurso__nombre">${escapeHtml(ayuda.nombre)}</h4>
            <p class="persona-recurso__desc">${escapeHtml(ayuda.descripcion)}</p>
            <div class="persona-recurso__tags">
              <span class="persona-recurso__tag">${escapeHtml(ayuda.categoria)}</span>
              <span class="persona-recurso__tag persona-recurso__tag--ok">Cupos demo</span>
            </div>
          </div>
          <button type="button" class="btn ${index === 0 ? "btn--primary" : "btn--secondary"} btn--sm persona-recurso__btn" data-recurso-demo="${index}">
            ${index === 0 ? "Solicitar" : "Ver detalles"}
          </button>
        </article>
      `).join("")
    : `<p class="ayudas__empty">No encontramos recursos compatibles en esta versión demostrativa.</p>`;

  return `
    <section class="persona-recursos" id="seccion-ayudas">
      <div class="persona-recursos__header">
        <h3 class="persona-section__title">Recursos compatibles</h3>
        <span class="persona-recursos__count">${items.length} encontrados</span>
      </div>
      <div class="persona-recursos__list">${cards}</div>
      <p class="ayudas__disclaimer">Recursos demostrativos. En producción se conectarían con fuentes oficiales verificadas.</p>
    </section>
  `;
}

function renderPersonaAcciones(pasaporte) {
  if (!pasaporte?.ruta?.length) return "";
  const completadas = new Set(pasaporte.acciones_completadas || []);
  return `
    <section class="persona-acciones">
      <h3 class="persona-section__title">Acciones de tu ruta</h3>
      <ul class="acciones-list">
        ${pasaporte.ruta.map((accion, index) => `
          <li>
            <label class="accion-item ${completadas.has(index) ? "accion-item--done" : ""}">
              <input type="checkbox" data-accion="${index}" ${completadas.has(index) ? "checked disabled" : ""}>
              <span>${escapeHtml(accion)}</span>
            </label>
          </li>
        `).join("")}
      </ul>
    </section>
  `;
}

function renderResult() {
  const { que_hacer_primero, ayudas = [] } = state.resultado || {};
  const pasaporte = state.pasaporte;
  const nombre = state.nombre.trim() || "María";
  const resumenIA = buildPersonaResumenIA(pasaporte, state.resultado, state.ia);
  const camposDiag = buildPersonaDiagnosticoFields(pasaporte, state.resultado);

  return `
    <div class="persona-home">
      <header class="persona-home__hero">
        <div class="persona-home__badges">
          ${pasaporte ? renderSemaforo(pasaporte.prioridad_nivel, `Prioridad ${pasaporte.prioridad_etiqueta}`) : ""}
          ${pasaporte ? `<span class="persona-home__id">ID: ${escapeHtml(pasaporte.id)}</span>` : ""}
        </div>
        <div class="persona-home__hero-row">
          <div>
            <h1 class="persona-home__title">Hola, ${escapeHtml(nombre)}</h1>
            <p class="persona-home__subtitle">Este es tu plan de acción personalizado para la recuperación.</p>
          </div>
          <div class="persona-home__hero-actions">
            <button type="button" class="btn btn--secondary btn--sm" id="btn-descargar-pdf">Descargar PDF</button>
            <button type="button" class="btn btn--accent btn--sm" id="btn-compartir">Compartir</button>
          </div>
        </div>
      </header>

      <div class="persona-home__grid">
        <div class="persona-home__main">
          <section class="persona-ai-card">
            <h2 class="persona-ai-card__title">✦ Resumen ejecutivo (IA)</h2>
            <p class="persona-ai-card__text">${escapeHtml(resumenIA)}</p>
            ${state.ia?.activo ? `<p class="persona-ai-card__meta">${state.ia.modelo ? `Gemini · ${escapeHtml(state.ia.modelo)}` : "Análisis asistido por IA"}</p>` : `<p class="persona-ai-card__meta">Resumen basado en reglas del sistema (Gemini inactivo).</p>`}
          </section>

          <section class="persona-diagnostico-card">
            <h3 class="persona-section__title">Diagnóstico actual</h3>
            <div class="persona-diagnostico-grid">
              ${camposDiag.map((c) => `
                <div class="persona-diagnostico-item">
                  <span class="persona-diagnostico-item__label">${escapeHtml(c.label)}</span>
                  <span class="persona-diagnostico-item__value ${c.critico ? "persona-diagnostico-item__value--critico" : ""}">${escapeHtml(c.value)}</span>
                </div>
              `).join("")}
            </div>
          </section>

          ${renderPersonaRecursos(ayudas)}

          ${pasaporte ? renderPersonaAcciones(pasaporte) : ""}

          <div class="persona-home__footer-actions">
            <button type="button" class="btn btn--secondary" id="btn-restart">Nuevo diagnóstico</button>
          </div>
        </div>

        <aside class="persona-home__aside">
          <section class="persona-aside-card">
            <h3 class="persona-section__title">Su progreso</h3>
            ${pasaporte ? renderPersonaStepper(pasaporte) : ""}
            ${pasaporte ? `
              <div class="persona-progreso-bar">
                <div class="persona-progreso-bar__fill" style="width: ${pasaporte.progreso}%"></div>
              </div>
              <p class="persona-progreso-bar__label">${pasaporte.progreso}% de la ruta completada</p>
            ` : ""}
          </section>

          <section class="persona-aside-card persona-aside-card--help">
            <p class="persona-aside-help__title">¿Necesita asistencia extra?</p>
            <p class="persona-aside-help__text">Contacte a un asesor territorial para validar su caso.</p>
            <button type="button" class="btn btn--secondary btn--wide btn--sm" id="btn-contactar-asesor">Contactar asesor</button>
          </section>

          ${que_hacer_primero ? `
            <section class="persona-aside-card">
              <h3 class="persona-section__title">Acción prioritaria</h3>
              <p class="persona-priority-text">${escapeHtml(que_hacer_primero)}</p>
            </section>
          ` : ""}
        </aside>
      </div>
    </div>
  `;
}

function renderPasaporte(pasaporte) {
  const completadas = new Set(pasaporte.acciones_completadas || []);
  const progresoNivel = pasaporte.progreso >= 75 ? "verde" : pasaporte.progreso >= 40 ? "amarillo" : "rojo";

  return `
    <section class="pasaporte" id="seccion-pasaporte">
      <div class="pasaporte__header">
        <h3 class="pasaporte__title">Pasaporte de Recuperación</h3>
        <span class="pasaporte__id">${escapeHtml(pasaporte.id)}</span>
      </div>
      <div class="pasaporte__body">
        <div class="semaforo-row">
          ${renderSemaforo(pasaporte.prioridad_nivel, `Prioridad ${pasaporte.prioridad_etiqueta}`)}
          ${renderSemaforo(pasaporte.confianza_nivel, pasaporte.confianza_etiqueta)}
          ${renderSemaforo(progresoNivel, `${pasaporte.progreso}% recuperación`)}
        </div>

        <div class="pasaporte__meta">
          <div class="pasaporte__row">
            <span class="pasaporte__label">Ruta</span>
            <span>${escapeHtml(pasaporte.ruta_nombre || pasaporte.actividad_economica)}</span>
          </div>
          <div class="pasaporte__row">
            <span class="pasaporte__label">Municipio</span>
            <span>${escapeHtml(pasaporte.municipio)}</span>
          </div>
          ${pasaporte.danos.length ? `
          <div class="pasaporte__row">
            <span class="pasaporte__label">Afectación</span>
            <span>${pasaporte.danos.map(escapeHtml).join(", ")}</span>
          </div>` : ""}
          <div class="pasaporte__row">
            <span class="pasaporte__label">Necesidades</span>
            <span>${pasaporte.necesidades.map(escapeHtml).join(", ")}</span>
          </div>
          <div class="pasaporte__row">
            <span class="pasaporte__label">Estado</span>
            <span>${escapeHtml(pasaporte.estado)}</span>
          </div>
        </div>

        <div class="pasaporte__status">
          <div class="pasaporte__progress-bar">
            <div class="pasaporte__progress-fill" style="width: ${pasaporte.progreso}%"></div>
          </div>
          <p class="pasaporte__progress-text">${pasaporte.progreso}%</p>
        </div>

        <h4 class="result__section-title">Acciones</h4>
        <ul class="acciones-list">
          ${pasaporte.ruta.map((accion, index) => `
            <li>
              <label class="accion-item ${completadas.has(index) ? "accion-item--done" : ""}">
                <input type="checkbox" data-accion="${index}" ${completadas.has(index) ? "checked disabled" : ""}>
                <span>${escapeHtml(accion)}</span>
              </label>
            </li>
          `).join("")}
        </ul>
      </div>
    </section>
  `;
}

function renderAyudas(ayudas) {
  const cards = ayudas.length > 0
    ? ayudas.map((ayuda) => `
        <article class="ayuda-card">
          <span class="ayuda-card__categoria">${escapeHtml(ayuda.categoria)}</span>
          <h4 class="ayuda-card__nombre">${escapeHtml(ayuda.nombre)}</h4>
          <p class="ayuda-card__descripcion">${escapeHtml(ayuda.descripcion)}</p>
        </article>
      `).join("")
    : `<p class="ayudas__empty">No encontramos recursos compatibles con tu situación en esta versión demostrativa.</p>`;

  return `
    <section class="ayudas" id="seccion-ayudas">
      <h3 class="result__section-title">Ayudas que pueden ayudarte</h3>
      <p class="ayudas__intro">Recursos relacionados con tu situación y necesidades actuales.</p>
      <div class="ayudas__grid">${cards}</div>
      <p class="ayudas__disclaimer">
        Los recursos mostrados en esta versión son demostrativos.
        En producción se conectarían con fuentes oficiales verificadas.
      </p>
    </section>
  `;
}

function bindWelcome() {
  document.getElementById("btn-start").addEventListener("click", () => {
    state.screen = "route-select";
    state.error = "";
    render();
  });

  document.getElementById("btn-consultar-pasaporte").addEventListener("click", () => {
    state.screen = "pasaporte-lookup";
    state.error = "";
    render();
  });

  document.getElementById("btn-dashboard").addEventListener("click", () => {
    window.location.hash = "dashboard";
    render();
  });
}

function bindQuiz() {
  const municipioInput = document.getElementById("input-municipio");
  if (municipioInput) {
    municipioInput.addEventListener("input", (e) => {
      state.municipio = e.target.value;
      state.error = "";
    });
    municipioInput.focus();
  }

  const nombreInput = document.getElementById("input-nombre");
  if (nombreInput) {
    nombreInput.addEventListener("input", (e) => {
      state.nombre = e.target.value;
    });
  }

  const personasInput = document.getElementById("input-personas");
  if (personasInput) {
    personasInput.addEventListener("input", (e) => {
      state.personas_hogar = e.target.value;
      state.error = "";
    });
    personasInput.focus();
  }

  const evidenciaInput = document.getElementById("input-evidencia");
  if (evidenciaInput) {
    evidenciaInput.addEventListener("input", (e) => {
      state.evidencia = e.target.value;
      state.error = "";
    });
  }

  document.querySelectorAll(".option").forEach((btn) => {
    btn.addEventListener("click", () => {
      const group = btn.dataset.group;
      const value = btn.dataset.value;
      state.error = "";

      if (group === "actividad") {
        state.actividad_economica = value;
        if (value !== "Otro") state.actividad_otro = "";
        render();
        return;
      }
      if (group === "danos") {
        toggleArrayItem(state.danos, value);
        if (!state.danos.includes("Otro")) state.dano_otro = "";
        render();
        return;
      }
      if (group === "operar") {
        state.puede_operar = value === "Sí";
        render();
        return;
      }
      if (group === "necesidades") {
        toggleArrayItem(state.necesidades, value);
        render();
        return;
      }
      if (group === "necesidad_inmediata") {
        state.necesidad_inmediata = value;
        if (value !== "Otro") state.necesidad_otro = "";
        render();
        return;
      }
      if (group === "urgencia") {
        state.urgencia = value;
        render();
        return;
      }
      if (group === "tipo_afectacion") {
        toggleArrayItem(state.tipo_afectacion, value);
        if (!state.tipo_afectacion.includes("Otro")) state.afectacion_otro = "";
        render();
        return;
      }
      if (group === "habitabilidad") {
        state.habitabilidad = value;
        render();
        return;
      }
      if (group === "servicios") {
        if (value === "Ninguno") {
          state.servicios_afectados = ["Ninguno"];
        } else {
          state.servicios_afectados = state.servicios_afectados.filter((s) => s !== "Ninguno");
          toggleArrayItem(state.servicios_afectados, value);
        }
        render();
      }
    });
  });

  bindOptionalInput("input-actividad-otro", "actividad_otro");
  bindOptionalInput("input-dano-otro", "dano_otro");
  bindOptionalInput("input-necesidad-otro", "necesidad_otro");
  bindOptionalInput("input-afectacion-otro", "afectacion_otro");

  const backBtn = document.getElementById("btn-back");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      if (state.step === 1) {
        state.screen = "route-select";
        state.step = 0;
      } else {
        state.step -= 1;
      }
      state.error = "";
      render();
    });
  }

  document.getElementById("btn-next").addEventListener("click", async () => {
    if (!validateStep()) return;

    if (state.step < getTotalSteps()) {
      state.step += 1;
      state.error = "";
      render();
      return;
    }

    await submitDiagnostico();
  });
}

function bindOptionalInput(id, field) {
  const input = document.getElementById(id);
  if (!input) return;
  input.addEventListener("input", (e) => {
    state[field] = e.target.value;
    state.error = "";
  });
  input.focus();
}

function resetFormState() {
  Object.assign(state, {
    screen: "welcome",
    tipo_ruta: null,
    step: 0,
    municipio: "",
    actividad_economica: "",
    actividad_otro: "",
    danos: [],
    dano_otro: "",
    puede_operar: null,
    necesidades: [],
    personas_hogar: "",
    necesidad_inmediata: "",
    necesidad_otro: "",
    urgencia: "",
    tipo_afectacion: [],
    afectacion_otro: "",
    habitabilidad: "",
    servicios_afectados: [],
    evidencia: "",
    resultado: null,
    pasaporte: null,
    ia: null,
    diagnostico: null,
    nombre: "",
    showAyudas: true,
    error: "",
    loading: false,
  });
}

function bindResult() {
  bindPasaporteActions();

  document.getElementById("btn-restart")?.addEventListener("click", () => {
    resetFormState();
    render();
  });

  document.getElementById("btn-descargar-pdf")?.addEventListener("click", () => {
    showToast("Descarga PDF disponible en la versión de producción.");
  });

  document.getElementById("btn-compartir")?.addEventListener("click", () => {
    const id = state.pasaporte?.id || "";
    const text = id ? `Mi Pasaporte de Recuperación: ${id}` : "Pasaporte Inteligente de Recuperación";
    if (navigator.share) {
      navigator.share({ title: "PIR", text }).catch(() => showToast(text));
    } else {
      showToast(text);
    }
  });

  document.getElementById("btn-contactar-asesor")?.addEventListener("click", () => {
    showToast("Un asesor territorial revisará su caso (demo).");
  });

  document.querySelectorAll("[data-recurso-demo]").forEach((btn) => {
    btn.addEventListener("click", () => {
      showToast("Solicitud registrada en modo demostrativo.");
    });
  });
}

async function marcarAccion(numero) {
  if (!state.pasaporte) return;

  try {
    const response = await fetch(
      `${API_BASE}/pasaporte/${state.pasaporte.id}/accion/${numero}`,
      { method: "PATCH" }
    );

    if (!response.ok) {
      throw new Error("No pudimos actualizar tu progreso.");
    }

    state.pasaporte = await response.json();
    render();

    if (state.pasaporte.progreso === 100) {
      showToast("¡Felicitaciones! Has completado tu ruta de recuperación.");
    }
  } catch (error) {
    showToast(error.message || "Error al marcar la acción.");
    render();
  }
}

function validateStep() {
  if (state.tipo_ruta === "ayuda_inmediata") return validateAyudaInmediata();
  if (state.tipo_ruta === "vivienda") return validateVivienda();
  return validateIngresos();
}

function validateAyudaInmediata() {
  switch (state.step) {
    case 1:
      if (!state.municipio.trim()) { state.error = "Por favor escribe el municipio."; render(); return false; }
      return true;
    case 2: {
      const n = parseInt(state.personas_hogar, 10);
      if (!n || n < 1) { state.error = "Indica cuántas personas hay en el hogar."; render(); return false; }
      return true;
    }
    case 3:
      if (!state.necesidad_inmediata) { state.error = "Selecciona una necesidad."; render(); return false; }
      if (state.necesidad_inmediata === "Otro" && !state.necesidad_otro.trim()) {
        state.error = "Describe tu necesidad."; render(); return false;
      }
      return true;
    case 4:
      if (!state.urgencia) { state.error = "Selecciona el nivel de urgencia."; render(); return false; }
      return true;
    case 5:
      return true;
    default:
      return true;
  }
}

function validateVivienda() {
  switch (state.step) {
    case 1:
      if (!state.municipio.trim()) { state.error = "Por favor escribe el municipio."; render(); return false; }
      return true;
    case 2: {
      const hasOtro = state.tipo_afectacion.includes("Otro");
      if (state.tipo_afectacion.length === 0) { state.error = "Selecciona al menos una afectación."; render(); return false; }
      if (hasOtro && !state.afectacion_otro.trim()) { state.error = "Describe la afectación."; render(); return false; }
      return true;
    }
    case 3:
      if (!state.habitabilidad) { state.error = "Selecciona la habitabilidad."; render(); return false; }
      return true;
    case 4:
      if (state.servicios_afectados.length === 0) { state.error = "Selecciona los servicios afectados."; render(); return false; }
      return true;
    case 5:
      return true;
    default:
      return true;
  }
}

function validateIngresos() {
  switch (state.step) {
    case 1:
      if (!state.municipio.trim()) {
        state.error = "Por favor escribe el municipio.";
        render();
        return false;
      }
      return true;

    case 2:
      if (!state.actividad_economica) {
        state.error = "Selecciona una actividad económica.";
        render();
        return false;
      }
      if (state.actividad_economica === "Otro" && !state.actividad_otro.trim()) {
        state.error = "Describe tu actividad económica.";
        render();
        return false;
      }
      return true;

    case 3: {
      const hasOtro = state.danos.includes("Otro");
      if (state.danos.length === 0 || (hasOtro && state.danos.length === 1 && !state.dano_otro.trim())) {
        state.error = "Selecciona al menos una opción.";
        render();
        return false;
      }
      if (hasOtro && !state.dano_otro.trim()) {
        state.error = "Describe qué más resultó afectado.";
        render();
        return false;
      }
      return true;
    }

    case 4:
      if (state.puede_operar === null) {
        state.error = "Selecciona Sí o No.";
        render();
        return false;
      }
      return true;

    case 5:
      if (state.necesidades.length === 0) {
        state.error = "Selecciona al menos una necesidad.";
        render();
        return false;
      }
      return true;

    default:
      return true;
  }
}

function buildPayload() {
  if (state.tipo_ruta === "ayuda_inmediata") {
    const necesidad = state.necesidad_inmediata === "Otro"
      ? state.necesidad_otro.trim()
      : state.necesidad_inmediata;
    return {
      tipo_ruta: "ayuda_inmediata",
      municipio: state.municipio.trim(),
      personas_hogar: parseInt(state.personas_hogar, 10),
      necesidad: toBackendValue(necesidad),
      urgencia: toBackendValue(state.urgencia),
      evidencia: state.evidencia.trim(),
    };
  }

  if (state.tipo_ruta === "vivienda") {
    const afectaciones = state.tipo_afectacion
      .filter((item) => item !== "Otro")
      .map(toBackendValue);
    if (state.tipo_afectacion.includes("Otro") && state.afectacion_otro.trim()) {
      afectaciones.push(toBackendValue(state.afectacion_otro));
    }
    return {
      tipo_ruta: "vivienda",
      municipio: state.municipio.trim(),
      tipo_afectacion: afectaciones,
      habitabilidad: toBackendValue(state.habitabilidad),
      servicios_afectados: state.servicios_afectados.map(toBackendValue),
      evidencia: state.evidencia.trim(),
    };
  }

  const actividad =
    state.actividad_economica === "Otro"
      ? state.actividad_otro.trim()
      : state.actividad_economica;
  const danos = state.danos.filter((item) => item !== "Otro").map(toBackendValue);
  if (state.danos.includes("Otro") && state.dano_otro.trim()) {
    danos.push(toBackendValue(state.dano_otro));
  }

  return {
    tipo_ruta: "ingresos",
    municipio: state.municipio.trim(),
    actividad_economica: actividad,
    danos,
    puede_operar: state.puede_operar,
    necesidades: state.necesidades.map(toBackendValue),
  };
}

async function submitDiagnostico() {
  state.screen = "loading";
  state.error = "";
  render();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    if (!response.ok) {
      throw new Error("No pudimos procesar tu diagnóstico. Intenta de nuevo.");
    }

    const data = await response.json();
    state.resultado = data.resultado;
    state.pasaporte = data.pasaporte;
    state.ia = data.ia || null;
    state.diagnostico = data.diagnostico || null;
    state.screen = "result";
    render();
  } catch (error) {
    state.screen = "quiz";
    state.step = 5;
    state.error = getFetchErrorMessage(error);
    render();
  }
}

function getFetchErrorMessage(error) {
  if (error.message === "Failed to fetch") {
    return (
      "No pudimos conectar con el backend. Asegúrate de tener activo el servidor en el puerto 8001 " +
      "(uvicorn app.main:app --reload --port 8001) en una terminal aparte del frontend."
    );
  }
  return error.message || "Ocurrió un error al procesar tu diagnóstico. Intenta de nuevo.";
}

function toggleArrayItem(array, value) {
  const index = array.indexOf(value);
  if (index === -1) {
    array.push(value);
  } else {
    array.splice(index, 1);
  }
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");

  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderSemaforo(nivel, etiqueta) {
  const n = nivel || "amarillo";
  return `<span class="semaforo semaforo--${escapeHtml(n)}"><span class="semaforo__dot"></span>${escapeHtml(etiqueta)}</span>`;
}

function nivelAlertaToSemaforo(nivel) {
  if (nivel === "alta") return "rojo";
  if (nivel === "media") return "amarillo";
  return "verde";
}

function renderRouteCard(tipo, titulo, desc, indicadorClass) {
  const selected = state.tipo_ruta === tipo;
  return `
    <button type="button" class="route-card ${selected ? "route-card--selected" : ""}" data-route="${tipo}">
      <span class="route-card__indicator route-card__indicator--${indicadorClass}"></span>
      <div class="route-card__body">
        <p class="route-card__title">${escapeHtml(titulo)}</p>
        <p class="route-card__desc">${escapeHtml(desc)}</p>
      </div>
    </button>
  `;
}

function formatTrend(value) {
  if (value > 0) return { text: `+${value} desde la última consulta`, className: "metric-card__trend--up" };
  if (value < 0) return { text: `${value} desde la última consulta`, className: "metric-card__trend--up" };
  return { text: "Sin cambios recientes", className: "metric-card__trend--neutral" };
}

function renderRanking(items, emptyLabel) {
  const entries = Object.entries(items || {});
  if (entries.length === 0) {
    return `<p class="ayudas__empty">${emptyLabel}</p>`;
  }

  const max = Math.max(...entries.map(([, value]) => value), 1);
  return `
    <div class="ranking-list">
      ${entries
        .sort((a, b) => b[1] - a[1])
        .map(([label, value]) => `
          <div class="ranking-item">
            <div class="ranking-item__header">
              <span>${escapeHtml(label)}</span>
              <span>${value}</span>
            </div>
            <div class="ranking-item__bar">
              <div class="ranking-item__fill" style="width: ${(value / max) * 100}%"></div>
            </div>
          </div>
        `).join("")}
    </div>
  `;
}

function renderDashboardView() {
  app.innerHTML = state.dashboardData
    ? renderDashboard(state.dashboardData)
    : `<section class="card loading"><div class="loading__spinner"></div><p class="loading__text">Cargando panel…</p></section>`;

  bindDashboardActions();
  startDashboardPolling();
}

function bindDashboardActions() {
  document.querySelectorAll("[data-seed-perfil]").forEach((btn) => {
    if (btn.dataset.bound === "1") return;
    btn.dataset.bound = "1";
    btn.addEventListener("click", async () => {
      const perfil = btn.dataset.seedPerfil || "a";
      const label = btn.dataset.seedLabel || "Cargar datos";
      btn.disabled = true;
      btn.textContent = "Generando…";
      try {
        const response = await fetch(
          `${API_BASE}/demo/seed?cantidad=250&reemplazar=true&perfil=${encodeURIComponent(perfil)}`,
          { method: "POST" },
        );
        if (!response.ok) throw new Error("No se pudo generar datos demo.");
        const result = await response.json();
        showToast(result.mensaje || `Escenario ${perfil.toUpperCase()} cargado.`);
        await fetchDashboard();
      } catch (error) {
        showToast(error.message || "Error al cargar demo.");
      } finally {
        const refreshed = document.querySelector(`[data-seed-perfil="${perfil}"]`);
        if (refreshed) {
          refreshed.disabled = false;
          refreshed.textContent = label;
        }
      }
    });
  });

  document.querySelectorAll("[data-dash-section]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const sectionId = link.dataset.dashSection;
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
      document.querySelectorAll(".dashboard-sidebar__link").forEach((l) => {
        l.classList.remove("dashboard-sidebar__link--active");
      });
      link.classList.add("dashboard-sidebar__link--active");
    });
  });

  document.querySelector("[data-nav-persona]")?.addEventListener("click", (event) => {
    event.preventDefault();
    stopDashboardPolling();
    window.location.hash = "";
    render();
  });

  if (state.dashboardData?.mapa_inteligente) {
    initMapaInteligente(state.dashboardData.mapa_inteligente);
  }
}

function renderAlertas(alertas) {
  if (!alertas || alertas.length === 0) {
    return `<p class="ayudas__empty">Sin alertas operativas activas.</p>`;
  }

  return `
    <p class="ayudas__intro">Generadas por reglas del sistema (cambios, concentración, brechas). No usan IA.</p>
    <ul class="alertas-list">
      ${alertas.map((alerta) => `
        <li class="alerta alerta--${escapeHtml(alerta.nivel || "info")}">
          <span class="alerta__dot"></span>
          <div class="alerta__body">
            <span class="alerta__nivel">${escapeHtml((alerta.nivel || "info").toUpperCase())}</span>
            <p class="alerta__mensaje">${escapeHtml(alerta.mensaje)}</p>
          </div>
        </li>
      `).join("")}
    </ul>
  `;
}

function renderResumenIA(resumen) {
  if (!resumen) {
    return `
      <section class="dashboard-section dashboard-section--ia">
        <h2 class="dashboard-section__title">Resumen ejecutivo (IA)</h2>
        <p class="ayudas__empty">Gemini no está activo. Las alertas y el simulador funcionan sin IA.</p>
      </section>
    `;
  }
  const texto = resumen.resumen_ejecutivo || resumen.resumen || resumen.texto;
  if (!texto) {
    return `
      <section class="dashboard-section dashboard-section--ia">
        <h2 class="dashboard-section__title">Resumen ejecutivo (IA)</h2>
        <p class="ayudas__empty">Sin narrativa IA disponible (Gemini inactivo o sin datos).</p>
      </section>
    `;
  }
  const titulo = resumen.titulo ? `<strong>${escapeHtml(resumen.titulo)}</strong><br>` : "";
  const accion = resumen.accion_recomendada
    ? `<p class="resumen-ia__accion">→ ${escapeHtml(resumen.accion_recomendada)}</p>`
    : "";
  const municipios = Array.isArray(resumen.municipios_destacados) && resumen.municipios_destacados.length > 0
    ? `<p class="resumen-ia__municipios">
        <span class="resumen-ia__municipios-label">Municipios citados por Gemini:</span>
        ${resumen.municipios_destacados.map((m) => `<span class="demo-badge demo-badge--mun">${escapeHtml(m)}</span>`).join(" ")}
      </p>`
    : "";
  const perfilIa = resumen.perfil_interpretado
    ? `<span class="demo-badge demo-badge--ia">Gemini leyó escenario ${escapeHtml(String(resumen.perfil_interpretado).toUpperCase())}</span>`
    : "";
  return `
    <section class="dashboard-section dashboard-section--ia">
      <h2 class="dashboard-section__title">Resumen ejecutivo (IA — Gemini)</h2>
      <p class="ayudas__intro">Narrativa opcional sobre patrones ya detectados por ML1/reglas. Carga escenario A o B y compara qué municipios cita la IA.</p>
      ${perfilIa ? `<div class="resumen-ia__meta">${perfilIa}</div>` : ""}
      <div class="resumen-ia">${titulo}${escapeHtml(texto)}${accion}${municipios}</div>
    </section>
  `;
}

function renderMlNecesidades(alertas) {
  const items = alertas || [];
  if (items.length === 0) {
    return `<p class="ayudas__empty">Sin patrones emergentes detectados. Carga datos demo para ver ML1 en acción.</p>`;
  }
  return `
    <ul class="ml-alertas-list">
      ${items.map((item) => `
        <li class="ml-alerta ml-alerta--${escapeHtml(item.nivel)}">
          <div class="ml-alerta__header">
            ${renderSemaforo(item.nivel, item.tipo === "crecimiento_temporal" ? "Crecimiento" : "Concentración")}
            <span class="ml-alerta__tipo">${escapeHtml(item.tipo === "crecimiento_temporal" ? "ML1 · Temporal" : "ML1 · Geográfico")}</span>
          </div>
          <p class="ml-alerta__mensaje">${escapeHtml(item.mensaje)}</p>
          ${item.accion_recomendada ? `<p class="ml-alerta__accion">→ ${escapeHtml(item.accion_recomendada)}</p>` : ""}
        </li>
      `).join("")}
    </ul>
  `;
}

function renderMapaSection(mapa) {
  if (!mapa) return "";
  const zonas = mapa.zonas_resumen || [];
  return `
    <section class="dashboard-section">
      <h2 class="dashboard-section__title">Mapa inteligente de afectación (ML2)</h2>
      <p class="ayudas__intro">${escapeHtml(mapa.resumen || "")}</p>
      ${zonas.length > 0 ? `
        <div class="mapa-zonas-grid">
          ${zonas.map((z) => `
            <article class="mapa-zona-card mapa-zona-card--${escapeHtml(z.nivel)}">
              ${renderSemaforo(z.nivel, z.prioridad_label || z.nivel)}
              <h3 class="mapa-zona-card__title">${escapeHtml(z.zona)}</h3>
              <p class="mapa-zona-card__stat"><strong>${z.total}</strong> casos · ${z.municipios_activos} municipios</p>
              <p class="mapa-zona-card__nec">Necesidad dominante: ${escapeHtml(z.necesidad_dominante || "—")}</p>
            </article>
          `).join("")}
        </div>
      ` : ""}
      <div id="mapa-afectacion" class="mapa-container" role="img" aria-label="Mapa de clusters de afectación"></div>
      <div class="mapa-leyenda">
        <span>${renderSemaforo("rojo", "Valle Sur — prioridad alta")}</span>
        <span>${renderSemaforo("amarillo", "Valle Norte — prioridad media")}</span>
        <span>${renderSemaforo("verde", "Cauca — prioridad baja")}</span>
      </div>
      ${(mapa.subclusters || []).length > 0 ? `
        <h3 class="result__section-title" style="margin-top:1rem">Subclusters detectados</h3>
        <ul class="subcluster-list">
          ${mapa.subclusters.slice(0, 5).map((s) => `
            <li class="subcluster-item">
              <strong>${escapeHtml(s.etiqueta)}</strong>
              <span>${escapeHtml(s.descripcion)}</span>
            </li>
          `).join("")}
        </ul>
      ` : ""}
    </section>
  `;
}

function renderRecursosSection(data) {
  const zonas = data.recursos_resumen_zonas || [];
  const recursos = data.recursos_disponibles || [];
  const total = data.recursos_total || recursos.length;
  const muestra = recursos.slice(0, 24);

  return `
    <section class="dashboard-section">
      <h2 class="dashboard-section__title">Recursos disponibles (demostrativos)</h2>
      <p class="ayudas__intro">
        Catálogo de <strong>${total}</strong> recursos repartidos por zona de afectación sísmica
        (Valle Norte, Valle Sur, Cauca). Las brechas comparan solicitudes vs unidades disponibles.
      </p>
      <div class="recursos-zona-grid">
        ${zonas.map((zona) => `
          <article class="recurso-zona-card">
            <h3 class="recurso-zona-card__title">${escapeHtml(zona.zona)}</h3>
            <p class="recurso-zona-card__stat"><strong>${zona.recursos}</strong> tipos · <strong>${zona.unidades_totales}</strong> unidades</p>
            <p class="recurso-zona-card__mun">${escapeHtml((zona.municipios || []).join(", "))}</p>
          </article>
        `).join("")}
      </div>
      <table class="brechas-table recursos-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Recurso</th>
            <th>Zona</th>
            <th>Municipio</th>
            <th>Unidades</th>
          </tr>
        </thead>
        <tbody>
          ${muestra.map((r) => `
            <tr>
              <td>${escapeHtml(r.id || "—")}</td>
              <td><strong>${escapeHtml(r.nombre)}</strong><br><small>${escapeHtml(r.categoria)}</small></td>
              <td>${escapeHtml(r.zona_sismica || "—")}</td>
              <td>${escapeHtml(r.municipio || "—")}</td>
              <td>${r.unidades_disponibles ?? "—"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      ${total > muestra.length ? `<p class="ayudas__disclaimer">Mostrando ${muestra.length} de ${total}. Catálogo completo en <code>GET /recursos/catalogo</code>.</p>` : ""}
      <p class="ayudas__disclaimer">Datos demostrativos. En producción se conectarían con fuentes oficiales verificadas.</p>
    </section>
  `;
}

function renderOfertaDemandaBanner(data) {
  const oferta = data.oferta_meta || {};
  const demanda = data.demanda_meta || {};
  const mun = data.municipio_foco_brechas;

  return `
    <section class="dashboard-section oferta-demanda-banner">
      <h2 class="dashboard-section__title">Oferta vs demanda</h2>
      <div class="oferta-demanda-grid">
        <article class="oferta-demanda-card oferta-demanda-card--demanda">
          <h3>Demanda (real)</h3>
          <p class="oferta-demanda-card__stat"><strong>${data.total_afectados ?? 0}</strong> personas registradas</p>
          <p>${escapeHtml(demanda.mensaje || "Pasaportes y diagnósticos del sistema.")}</p>
          ${mun ? `<p><strong>Municipio con más casos:</strong> ${escapeHtml(mun)}</p>` : ""}
        </article>
        <article class="oferta-demanda-card oferta-demanda-card--oferta">
          <h3>Oferta (demo)</h3>
          <p class="oferta-demanda-card__stat">
            <strong>${oferta.total_programas ?? 0}</strong> programas ·
            <strong>${oferta.total_cupos ?? 0}</strong> cupos
          </p>
          <p>${escapeHtml(oferta.mensaje || "")}</p>
          <p class="oferta-demanda-card__hint">${escapeHtml(oferta.como_se_calcula || "")}</p>
        </article>
      </div>
      <p class="ayudas__disclaimer">${escapeHtml(oferta.produccion || "")}</p>
    </section>
  `;
}

function renderBrechasSection(data) {
  const brechas = data.brechas || [];
  const resumen = data.brechas_resumen || {};
  const maxBrecha = Math.max(1, ...brechas.map((b) => Number(b.brecha) || 0));
  const mun = data.municipio_foco_brechas;
  const titulo = mun
    ? `Brechas en ${mun} (solicitudes vs cupos del municipio)`
    : "Brechas: ¿alcanzan los cupos?";

  return `
    <section class="dashboard-section">
      <h2 class="dashboard-section__title">${escapeHtml(titulo)}</h2>
      <div class="brechas-glosario">
        <p><strong>¿Qué comparamos?</strong> Personas que pidieron una necesidad <em>en ese municipio</em> vs cupos del catálogo demo <em>en ese mismo municipio</em>.</p>
        <ul>
          <li><strong>Solicitudes</strong> = pasaportes con esa necesidad en el municipio foco.</li>
          <li><strong>Cupos</strong> = suma de unidades del programa equivalente en ese municipio.</li>
          <li><strong>Faltan</strong> = solicitudes − cupos (déficit local).</li>
        </ul>
        ${resumen.mensaje ? `<p class="brechas-glosario__resumen">${escapeHtml(resumen.mensaje)}</p>` : ""}
      </div>
      <table class="brechas-table">
        <thead>
          <tr>
            <th>Estado</th>
            <th>Necesidad reportada</th>
            <th>Programa equivalente</th>
            <th>Solicitudes</th>
            <th>Cupos</th>
            <th>Faltan</th>
            <th>Cobertura</th>
          </tr>
        </thead>
        <tbody>
          ${brechas.length > 0
            ? brechas.map((brecha) => `
                <tr class="brecha-row--${escapeHtml(brecha.nivel || brecha.estado || "verde")}">
                  <td>${renderSemaforo(brecha.nivel || "verde", brecha.estado_label || "—")}</td>
                  <td>${escapeHtml(brecha.necesidad)}</td>
                  <td>${escapeHtml(brecha.programa || "—")}</td>
                  <td>${brecha.solicitudes}</td>
                  <td>${brecha.recursos}</td>
                  <td class="brecha-value">
                    <span class="brecha-value__bar" aria-hidden="true">
                      <span class="brecha-value__fill" style="width: ${Math.round(((Number(brecha.brecha) || 0) / maxBrecha) * 100)}%"></span>
                    </span>
                    <strong>${brecha.brecha}</strong>
                  </td>
                  <td>${brecha.cobertura_pct ?? 0}%</td>
                </tr>
                <tr class="brecha-explicacion-row">
                  <td colspan="7"><em>${escapeHtml(brecha.explicacion || "")}</em></td>
                </tr>
              `).join("")
            : `<tr><td colspan="7">Sin datos. Carga los 250 casos demo para ver brechas.</td></tr>`}
        </tbody>
      </table>
    </section>
  `;
}

function renderPanelPrioridades(prioridades) {
  if (!prioridades) return "";
  const items = prioridades.prioridades || [];

  return `
    <section class="dashboard-section panel-prioridades">
      <h2 class="dashboard-section__title">¿Dónde invertir primero?</h2>
      <p class="ayudas__intro">
        Priorización automática para entidades. Cruza solicitudes reales, cupos del catálogo y concentración territorial.
        Sin sliders ni proyecciones abstractas.
      </p>
      <div class="prioridades-contexto">
        <p>
          <strong>Foco territorial:</strong> ${escapeHtml(prioridades.municipio_foco)}
          (${prioridades.casos_en_foco} casos) · Zona ${escapeHtml(prioridades.zona_sismica)}
        </p>
        <p class="prioridades-contexto__mensaje">${escapeHtml(prioridades.mensaje_general || "")}</p>
      </div>
      ${items.length > 0
        ? `<ol class="prioridades-list">
            ${items.map((item) => `
              <li class="prioridad-item prioridad-item--${escapeHtml(item.nivel)}">
                <div class="prioridad-item__header">
                  <span class="prioridad-item__orden">#${item.orden}</span>
                  ${renderSemaforo(item.nivel, item.nivel === "rojo" ? "Alta" : item.nivel === "amarillo" ? "Media" : "Baja")}
                  <strong>${escapeHtml(item.programa)}</strong>
                </div>
                <p class="prioridad-item__accion">${escapeHtml(item.accion_sugerida)}</p>
                <p class="prioridad-item__detalle">
                  ${item.solicitudes} solicitudes · ${item.cupos_disponibles} cupos · faltan ${item.faltan_cupos}
                  · cobertura ${item.cobertura_pct}%
                </p>
                <p class="prioridad-item__justificacion"><em>${escapeHtml(item.justificacion)}</em></p>
              </li>
            `).join("")}
          </ol>`
        : `<p class="ayudas__empty">No hay déficit de cupos con los datos actuales. Las necesidades reportadas están cubiertas en el catálogo demo.</p>`}
      <p class="ayudas__disclaimer">${escapeHtml(prioridades.disclaimer || "")}</p>
    </section>
  `;
}

function initMapaInteligente(mapa) {
  if (!mapa || !window.L) return;
  const el = document.getElementById("mapa-afectacion");
  if (!el) return;

  if (state.mapaInstance) {
    state.mapaInstance.remove();
    state.mapaInstance = null;
  }

  const centro = mapa.centro || { lat: 3.45, lng: -76.53 };
  const map = L.map(el, { scrollWheelZoom: false }).setView([centro.lat, centro.lng], mapa.zoom || 8);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
    maxZoom: 18,
  }).addTo(map);

  const colores = { rojo: "#b42318", amarillo: "#92610a", verde: "#157a3a" };

  (mapa.zonas_resumen || []).forEach((zona) => {
    L.circle([zona.lat, zona.lng], {
      radius: 22000 + zona.total * 120,
      color: colores[zona.nivel] || colores.verde,
      fillColor: colores[zona.nivel] || colores.verde,
      fillOpacity: 0.08,
      weight: 2,
      dashArray: "6 4",
    })
      .bindPopup(
        `<strong>${zona.zona}</strong><br>${zona.total} casos<br>`
        + `<em>${zona.prioridad_label || ""}</em>`
      )
      .addTo(map);
  });

  (mapa.clusters || []).forEach((cluster) => {
    const radio = Math.min(36, 10 + cluster.total * 1.2);
    L.circleMarker([cluster.lat, cluster.lng], {
      radius: radio,
      color: colores[cluster.nivel] || colores.verde,
      fillColor: colores[cluster.nivel] || colores.verde,
      fillOpacity: cluster.nivel === "rojo" ? 0.72 : 0.55,
      weight: cluster.nivel === "rojo" ? 3 : 2,
    })
      .bindPopup(
        `<strong>${cluster.etiqueta}</strong><br>`
        + `Zona: ${cluster.zona_sismica || "—"}<br>`
        + `${cluster.descripcion}<br>`
        + `<em>${cluster.recuperables} recuperables</em>`
      )
      .addTo(map);
  });

  (mapa.subclusters || []).forEach((sub) => {
    const subColor = colores[sub.nivel] || "#0d3b66";
    L.circleMarker([sub.lat, sub.lng], {
      radius: 7,
      color: subColor,
      fillColor: subColor,
      fillOpacity: 0.85,
      weight: 1,
    })
      .bindPopup(`<strong>${sub.etiqueta}</strong><br>${sub.descripcion}`)
      .addTo(map);
  });

  state.mapaInstance = map;
  setTimeout(() => map.invalidateSize(), 100);
}

function renderTendenciaBanner(tendencia) {
  if (!tendencia) return "";
  return `
    <div class="tendencia-banner tendencia-banner--${escapeHtml(tendencia.nivel)}">
      <strong>Detección de tendencia emergente</strong>
      En ${escapeHtml(tendencia.municipio)} aumentaron reportes de
      <strong>${escapeHtml(tendencia.necesidad)}</strong>
      (${tendencia.porcentaje}% del total, ${tendencia.casos} casos).
      <br><em>Acción recomendada: revisar disponibilidad de programas para esta zona.</em>
    </div>
  `;
}

function renderDashboardSidebar(data) {
  const foco = data.municipio_foco_brechas || data.prioridades_entidad?.municipio_foco || "Valle del Cauca";
  const navItems = [
    { id: "sec-resumen", label: "Resumen" },
    { id: "sec-ml1", label: "ML1 Necesidades" },
    { id: "sec-mapa", label: "Mapa territorial" },
    { id: "sec-oferta", label: "Oferta vs demanda" },
    { id: "sec-prioridades", label: "Priorización" },
    { id: "sec-brechas", label: "Brechas" },
    { id: "sec-municipios", label: "Municipios" },
  ];

  return `
    <aside class="dashboard-sidebar">
      <div class="dashboard-sidebar__entity">
        <p class="dashboard-sidebar__entity-label">Entidades territoriales</p>
        <p class="dashboard-sidebar__entity-name">Alcaldía de ${escapeHtml(foco)}</p>
        <p class="dashboard-sidebar__entity-meta">PIR · Post-emergencia v1.0</p>
      </div>
      <nav class="dashboard-sidebar__nav" aria-label="Secciones del panel">
        ${navItems.map((item, index) => `
          <a href="#${item.id}" class="dashboard-sidebar__link ${index === 2 ? "dashboard-sidebar__link--active" : ""}" data-dash-section="${item.id}">
            ${escapeHtml(item.label)}
          </a>
        `).join("")}
      </nav>
      <a href="#" class="btn btn--secondary btn--wide btn--sm dashboard-sidebar__back" data-nav-persona>Volver a Persona</a>
    </aside>
  `;
}

function renderDashboard(data) {
  const t = data.tendencias || {};
  const metrics = [
    { label: "Afectados registrados", value: data.total_afectados, trend: t.total_afectados },
    { label: "No operativos", value: data.total_no_operativos, trend: t.total_no_operativos },
    { label: "Rutas completadas", value: data.total_rutas_completadas, trend: t.total_rutas_completadas },
    { label: "Progreso promedio", value: `${data.progreso_promedio}%`, trend: t.progreso_promedio },
  ];

  const municipios = data.municipios_detalle || Object.entries(data.por_municipio || {}).map(([nombre, total]) => ({
    nombre, total, nivel: "verde",
  }));

  const perfilDemo = data.perfil_demo;
  const perfilBadge = perfilDemo
    ? `<span class="demo-badge demo-badge--${escapeHtml(perfilDemo)}">Escenario ${escapeHtml(String(perfilDemo).toUpperCase())} activo</span>`
    : "";

  return `
    <div class="dashboard-layout">
      ${renderDashboardSidebar(data)}
      <div class="dashboard-main">
        <div class="dashboard" id="sec-resumen">
          <div class="dashboard__header">
            <div>
              <p class="dashboard__eyebrow">Entidades territoriales</p>
              <h1 class="dashboard__title">Panel territorial ${perfilBadge}</h1>
              <p class="dashboard__subtitle">Vista para alcaldías: qué piden las personas, dónde hay déficit de cupos y qué hacer primero.</p>
              ${perfilDemo === "a"
                ? `<p class="dashboard__hint">Escenario A: hotspot en <strong>Cali</strong> (financiamiento).</p>`
                : perfilDemo === "b"
                  ? `<p class="dashboard__hint">Escenario B: hotspot en <strong>Popayán, Quibdó y Palmira</strong> (corredor Valle–Pacífico, sin Cali).</p>`
                  : ""}
              ${state.dashboardUpdatedAt ? `<p class="dashboard__updated">Actualizado: ${state.dashboardUpdatedAt}</p>` : ""}
            </div>
            <div class="dashboard__actions">
              <button type="button" class="btn btn--secondary btn--sm" data-seed-perfil="a" data-seed-label="Cargar datos A (Cali)">Cargar datos A (Cali)</button>
              <button type="button" class="btn btn--primary btn--sm" data-seed-perfil="b" data-seed-label="Cargar datos B (Popayán/Quibdó)">Cargar datos B (Popayán/Quibdó)</button>
            </div>
          </div>

          ${renderTendenciaBanner(data.tendencia_emergente)}

          <div class="dashboard-grid">
            ${metrics.map((metric) => {
              const trend = formatTrend(metric.trend ?? 0);
              return `
                <article class="metric-card">
                  <p class="metric-card__label">${metric.label}</p>
                  <p class="metric-card__value">${metric.value}</p>
                  <p class="metric-card__trend ${trend.className}">${trend.text}</p>
                </article>
              `;
            }).join("")}
          </div>

          <section class="dashboard-section" id="sec-ml1">
            <h2 class="dashboard-section__title">ML1 — Necesidades emergentes</h2>
            ${renderMlNecesidades(data.ml_necesidades_emergentes)}
          </section>

          <div id="sec-mapa">${renderMapaSection(data.mapa_inteligente)}</div>

          <section class="dashboard-section">
            <h2 class="dashboard-section__title">Alertas operativas</h2>
            ${renderAlertas(data.alertas)}
          </section>

          <div id="resumen-ia-container"></div>

          <div id="sec-oferta">${renderOfertaDemandaBanner(data)}</div>

          <div id="sec-prioridades">${renderPanelPrioridades(data.prioridades_entidad)}</div>

          <div id="sec-brechas">${renderBrechasSection(data)}</div>

          <section class="dashboard-section" id="sec-municipios">
            <h2 class="dashboard-section__title">Distribución por municipio</h2>
            <div class="municipio-cards">
              ${municipios.length > 0
                ? municipios.map((m) => `
                    <article class="municipio-card municipio-card--${escapeHtml(m.nivel || "verde")}">
                      <p class="municipio-card__name">${escapeHtml(m.nombre)}</p>
                      <p class="municipio-card__count">${m.total}</p>
                      ${renderSemaforo(m.nivel, m.nivel === "rojo" ? "Alta concentración" : m.nivel === "amarillo" ? "Concentración media" : "Normal")}
                    </article>
                  `).join("")
                : `<p class="ayudas__empty">Sin datos. Usa "Cargar datos A" o "Cargar datos B" para poblar el panel.</p>`}
            </div>
          </section>

          <section class="dashboard-section">
            <h2 class="dashboard-section__title">Prioridad de casos</h2>
            ${renderRanking(data.por_prioridad, "Sin datos de prioridad.")}
          </section>

          <section class="dashboard-section">
            <h2 class="dashboard-section__title">Necesidades reportadas</h2>
            ${renderRanking(data.por_necesidad, "Sin necesidades registradas.")}
          </section>

          <section class="dashboard-section">
            <h2 class="dashboard-section__title">Rutas activas</h2>
            ${renderRanking(data.por_ruta, "Sin rutas registradas.")}
          </section>

          ${renderRecursosSection(data)}
        </div>
      </div>
    </div>
  `;
}

async function fetchResumenIA() {
  const container = document.getElementById("resumen-ia-container");
  if (!container) return;
  try {
    const response = await fetch(`${API_BASE}/ml/necesidades-emergentes`);
    if (!response.ok) throw new Error();
    const data = await response.json();
    container.innerHTML = renderResumenIA(data.resumen_ia);
  } catch {
    container.innerHTML = renderResumenIA(null);
  }
}

async function fetchDashboard() {
  try {
    const response = await fetch(`${API_BASE}/dashboard/resumen`);
    if (!response.ok) throw new Error("No se pudo cargar el dashboard.");

    state.dashboardData = await response.json();
    const now = new Date();
    state.dashboardUpdatedAt = now.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    if (isDashboardView()) {
      app.innerHTML = renderDashboard(state.dashboardData);
      bindDashboardActions();
      fetchResumenIA();
    }
  } catch (error) {
    if (isDashboardView()) {
      app.innerHTML = `
        <section class="card">
          <p class="error-msg">${escapeHtml(getFetchErrorMessage(error))}</p>
        </section>
      `;
      bindDashboardActions();
    }
  }
}

function startDashboardPolling() {
  stopDashboardPolling();
  fetchDashboard();
  dashboardInterval = setInterval(fetchDashboard, DASHBOARD_POLL_MS);
}

function stopDashboardPolling() {
  if (dashboardInterval) {
    clearInterval(dashboardInterval);
    dashboardInterval = null;
  }
}

window.addEventListener("hashchange", () => {
  render();
});

render();
