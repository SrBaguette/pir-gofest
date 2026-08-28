const API_BASE = "http://127.0.0.1:8001";
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
  pasaporteLookupId: "",
  showAyudas: true,
  dashboardData: null,
  dashboardUpdatedAt: null,
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
      Persona afectada
    </a>
    <a href="#dashboard" class="header__link ${enDashboard ? "header__link--active" : ""}" data-nav="dashboard">
      Vista de entidades
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
  }
}

function getTotalSteps() {
  return 5;
}

function renderRouteSelect() {
  return `
    <section class="card">
      <h2 class="question__title">¿Qué necesitas recuperar primero?</h2>
      <p class="question__hint">Selecciona la opción que mejor describe tu situación.</p>
      <div class="options">
        ${optionButton("tipo_ruta", "Ayuda inmediata", state.tipo_ruta === "ayuda_inmediata")}
        ${optionButton("tipo_ruta", "Recuperar vivienda", state.tipo_ruta === "vivienda")}
        ${optionButton("tipo_ruta", "Recuperar ingresos", state.tipo_ruta === "ingresos")}
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
  document.querySelectorAll(".option").forEach((btn) => {
    btn.addEventListener("click", () => {
      const label = btn.dataset.value;
      if (label === "Ayuda inmediata") state.tipo_ruta = "ayuda_inmediata";
      else if (label === "Recuperar vivienda") state.tipo_ruta = "vivienda";
      else state.tipo_ruta = "ingresos";
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
      <h1 class="welcome__title">Ruta de Recuperación</h1>
      <p class="welcome__subtitle">
        Cuéntanos qué ocurrió y te ayudaremos a identificar qué hacer primero.
      </p>
      <span class="welcome__badge">Diagnóstico de aproximadamente 3 minutos</span>
      <p class="welcome__hint">¿Ya tienes un pasaporte? Consulta tu progreso cuando quieras.</p>
      <div class="actions actions--single">
        <button type="button" class="btn btn--primary btn--wide" id="btn-start">
          Comenzar diagnóstico
        </button>
        <button type="button" class="btn btn--accent btn--wide" id="btn-consultar-pasaporte">
          Consultar mi pasaporte
        </button>
        <button type="button" class="btn btn--secondary btn--wide" id="btn-dashboard">
          Vista de entidades
        </button>
      </div>
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

function getStepAyudaInmediata() {
  switch (state.step) {
    case 1:
      return {
        title: "¿En qué municipio ocurrió la afectación?",
        hint: "Escribe el municipio donde necesitas apoyo.",
        body: `<input type="text" class="input-text" id="input-municipio" placeholder="Ejemplo: Jojutla" value="${escapeHtml(state.municipio)}">`,
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
        hint: "Escribe el municipio.",
        body: `<input type="text" class="input-text" id="input-municipio" placeholder="Ejemplo: Jojutla" value="${escapeHtml(state.municipio)}">`,
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
        hint: "Ruta: Recuperar ingresos. Indica dónde vives o dónde opera tu actividad económica.",
        body: `
          <input
            type="text"
            class="input-text"
            id="input-municipio"
            placeholder="Ejemplo: Jojutla"
            value="${escapeHtml(state.municipio)}"
            autocomplete="address-level2"
          >
        `,
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

function renderResult() {
  const { que_hacer_primero, ruta, ayudas = [], barrera_principal, ruta_nombre } = state.resultado;
  const pasaporte = state.pasaporte;

  return `
    <section class="card">
      <p class="result__label">Tu Ruta de Recuperación</p>
      <h2 class="result__title">${escapeHtml(ruta_nombre || "Esto es lo que te recomendamos")}</h2>

      <div class="result__priority">
        <p class="result__priority-label">¿Qué hacer primero?</p>
        <p class="result__priority-text">${escapeHtml(que_hacer_primero)}</p>
      </div>

      ${barrera_principal ? `
        <div class="result__priority" style="margin-top:-1rem;background:#faf0e8;border-left-color:var(--color-accent);">
          <p class="result__priority-label">Principal barrera</p>
          <p class="result__priority-text">${escapeHtml(barrera_principal)}</p>
        </div>
      ` : ""}

      <h3 class="result__section-title">Tu ruta</h3>
      <ol class="route-steps">
        ${ruta.map((paso, index) => `
          <li class="route-step">
            <span class="route-step__number">${String(index + 1).padStart(2, "0")}</span>
            <p class="route-step__text">${escapeHtml(paso)}</p>
          </li>
        `).join("")}
      </ol>

      ${pasaporte ? renderPasaporte(pasaporte) : ""}
      ${renderAyudas(ayudas)}

      <div class="result__actions">
        <button type="button" class="btn btn--secondary" id="btn-restart">
          Realizar otro diagnóstico
        </button>
      </div>
    </section>
  `;
}

function renderPasaporte(pasaporte) {
  const completadas = new Set(pasaporte.acciones_completadas || []);

  return `
    <section class="pasaporte" id="seccion-pasaporte">
      <h3 class="pasaporte__title">Mi Pasaporte de Recuperación</h3>
      <div class="pasaporte__meta">
        <div class="pasaporte__row">
          <span class="pasaporte__label">ID:</span>
          <span>${escapeHtml(pasaporte.id)}</span>
        </div>
        <div class="pasaporte__row">
          <span class="pasaporte__label">Ruta:</span>
          <span>${escapeHtml(pasaporte.ruta_nombre || pasaporte.actividad_economica)}</span>
        </div>
        <div class="pasaporte__row">
          <span class="pasaporte__label">Municipio:</span>
          <span>${escapeHtml(pasaporte.municipio)}</span>
        </div>
        ${pasaporte.danos.length ? `
        <div class="pasaporte__row">
          <span class="pasaporte__label">Afectaciones:</span>
          <span>${pasaporte.danos.map(escapeHtml).join(", ")}</span>
        </div>` : ""}
        <div class="pasaporte__row">
          <span class="pasaporte__label">Necesidades:</span>
          <span>${pasaporte.necesidades.map(escapeHtml).join(", ")}</span>
        </div>
      </div>

      <div class="pasaporte__status">
        <span class="pasaporte__badge ${pasaporte.progreso === 100 ? "pasaporte__badge--done" : ""}">
          ${escapeHtml(pasaporte.estado)}
        </span>
        <div class="pasaporte__progress-wrap">
          <div class="pasaporte__progress-bar">
            <div class="pasaporte__progress-fill" style="width: ${pasaporte.progreso}%"></div>
          </div>
          <p class="pasaporte__progress-text">${pasaporte.progreso}% completado</p>
        </div>
      </div>

      <h4 class="result__section-title">Acciones de tu ruta</h4>
      <ul class="acciones-list">
        ${pasaporte.ruta.map((accion, index) => `
          <li>
            <label class="accion-item ${completadas.has(index) ? "accion-item--done" : ""}">
              <input
                type="checkbox"
                data-accion="${index}"
                ${completadas.has(index) ? "checked disabled" : ""}
              >
              <span>${escapeHtml(accion)}</span>
            </label>
          </li>
        `).join("")}
      </ul>
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
    showAyudas: true,
    error: "",
    loading: false,
  });
}

function bindResult() {
  bindPasaporteActions();

  document.getElementById("btn-restart").addEventListener("click", () => {
    resetFormState();
    render();
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
    : `<section class="card loading"><div class="loading__spinner"></div><p class="loading__text">Cargando dashboard…</p></section>`;

  startDashboardPolling();
}

function renderAlertas(alertas) {
  if (!alertas || alertas.length === 0) {
    return `<p class="ayudas__empty">Sin alertas activas.</p>`;
  }

  return `
    <ul class="alertas-list">
      ${alertas.map((alerta) => `
        <li class="alerta alerta--${escapeHtml(alerta.nivel || "info")}">
          <span class="alerta__nivel">${escapeHtml((alerta.nivel || "info").toUpperCase())}</span>
          <p class="alerta__mensaje">${escapeHtml(alerta.mensaje)}</p>
        </li>
      `).join("")}
    </ul>
  `;
}

function renderDashboard(data) {
  const t = data.tendencias || {};
  const metrics = [
    { label: "Personas afectadas", value: data.total_afectados, trend: t.total_afectados },
    { label: "Negocios no operativos", value: data.total_no_operativos, trend: t.total_no_operativos },
    { label: "Rutas completadas", value: data.total_rutas_completadas, trend: t.total_rutas_completadas },
    { label: "Progreso promedio", value: `${data.progreso_promedio}%`, trend: t.progreso_promedio, suffix: "%" },
  ];

  const municipios = Object.entries(data.por_municipio || {});

  return `
    <div class="dashboard">
      <div class="dashboard__header">
        <h1 class="dashboard__title">Dashboard de entidad</h1>
        <p class="dashboard__subtitle">
          Vista agregada para alcaldías, gobiernos y organizaciones de apoyo.
        </p>
        ${state.dashboardUpdatedAt ? `<p class="dashboard__updated">Última actualización: ${state.dashboardUpdatedAt}</p>` : ""}
      </div>

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

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">Alertas</h2>
        <p class="ayudas__intro">Señales detectadas desde la última consulta del dashboard.</p>
        ${renderAlertas(data.alertas)}
      </section>

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">¿Dónde están los afectados?</h2>
        <div class="municipio-cards">
          ${municipios.length > 0
            ? municipios.map(([nombre, total]) => `
                <article class="municipio-card">
                  <p class="municipio-card__name">${escapeHtml(nombre)}</p>
                  <p class="municipio-card__count">${total}</p>
                </article>
              `).join("")
            : `<p class="ayudas__empty">Aún no hay diagnósticos registrados.</p>`}
        </div>
      </section>

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">¿Qué necesitan?</h2>
        ${renderRanking(data.por_necesidad, "Sin necesidades registradas todavía.")}
      </section>

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">¿Qué rutas siguen las personas?</h2>
        ${renderRanking(data.por_ruta, "Sin rutas registradas todavía.")}
      </section>

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">Tendencias</h2>
        <div class="dashboard-grid">
          ${Object.entries(t).map(([key, value]) => `
            <article class="metric-card">
              <p class="metric-card__label">${escapeHtml(key.replace(/_/g, " "))}</p>
              <p class="metric-card__value">${value > 0 ? `+${value}` : value}</p>
            </article>
          `).join("")}
        </div>
      </section>

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">Recursos disponibles (demostrativos)</h2>
        <div class="recursos-grid">
          ${(data.recursos_disponibles || []).map((recurso) => `
            <article class="ayuda-card">
              <span class="ayuda-card__categoria">${escapeHtml(recurso.categoria)}</span>
              <h4 class="ayuda-card__nombre">${escapeHtml(recurso.nombre)}</h4>
              <p class="ayuda-card__descripcion">${escapeHtml(recurso.descripcion)}</p>
            </article>
          `).join("")}
        </div>
        <p class="ayudas__disclaimer">
          Los recursos mostrados en esta versión son demostrativos.
          En producción se conectarían con fuentes oficiales verificadas.
        </p>
      </section>

      <section class="dashboard-section">
        <h2 class="dashboard-section__title">¿Dónde están las brechas?</h2>
        <p class="ayudas__intro">
          Comparación entre solicitudes registradas y recursos demostrativos disponibles.
          Brecha = solicitudes − recursos.
        </p>
        <table class="brechas-table">
          <thead>
            <tr>
              <th>Necesidad</th>
              <th>Solicitudes</th>
              <th>Recursos</th>
              <th>Brecha</th>
            </tr>
          </thead>
          <tbody>
            ${(data.brechas || []).length > 0
              ? data.brechas.map((brecha) => `
                  <tr class="${brecha.brecha > 0 ? "brecha-row--alta" : ""}">
                    <td>${escapeHtml(brecha.necesidad)}</td>
                    <td>${brecha.solicitudes}</td>
                    <td>${brecha.recursos}</td>
                    <td>${brecha.brecha}</td>
                  </tr>
                `).join("")
              : `<tr><td colspan="4">Sin datos de brechas todavía.</td></tr>`}
          </tbody>
        </table>
      </section>
    </div>
  `;
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
    }
  } catch (error) {
    if (isDashboardView()) {
      app.innerHTML = `
        <section class="card">
          <p class="error-msg">${escapeHtml(getFetchErrorMessage(error))}</p>
        </section>
      `;
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
