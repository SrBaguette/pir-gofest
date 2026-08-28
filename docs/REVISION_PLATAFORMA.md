# PIR — Proceso de revisión e implementación visual

> Guía para alinear las 4 pantallas del diseño con el MVP actual **sin romper** API, dashboard ni WhatsApp.

---

## 1. Mapa de las 4 pantallas

| # | Pantalla | Rol | Archivo actual | Estado |
|---|----------|-----|----------------|--------|
| 1 | Inicio Persona / Entidades | Hub de entrada | `index.html` + `app.js` → `renderWelcome()` | ✅ ~90% |
| 2 | Panel territorial (Entidades) | Alcaldías / entidades | `app.js` → `#dashboard` → `renderDashboard()` | ✅ ~90% |
| 3 | Canal WhatsApp | Demo conversacional | `whatsapp-demo.html` + `whatsapp-demo.js` | ✅ ~95% |
| 4 | Plan de acción persona | Post-diagnóstico | `app.js` → `renderResult()` | ✅ Fase 1 |

---

## 2. Reglas de oro (no romper lo existente)

### Backend — NO tocar salvo extensión opcional

| Endpoint | Contrato | Riesgo si se cambia |
|----------|----------|---------------------|
| `POST /diagnostico` | `{ diagnostico, resultado, pasaporte, ia }` | Rompe web + WhatsApp |
| `GET /pasaporte/{id}` | Pasaporte completo | Rompe consulta |
| `PATCH /pasaporte/{id}/accion/{n}` | Progreso | Rompe checkboxes |
| `GET /dashboard/resumen` | Panel entidades | Rompe demo A/B |
| `POST /demo/seed?perfil=a\|b` | Seed territorial | Rompe pitch |
| `GET /ml/necesidades-emergentes` | ML1 + Gemini entidades | Rompe resumen IA panel |

**Principio:** los cambios visuales son **solo frontend** (HTML/CSS en JS). El backend ya expone todo lo necesario.

### Frontend — zonas seguras vs frágiles

| Zona segura (extender) | Zona frágil (no refactorizar) |
|------------------------|-------------------------------|
| `renderResult()` — layout post-diagnóstico | `buildPayload()` / validadores del quiz |
| `renderDashboard()` — añadir sidebar CSS | `fetchDashboard()` / polling |
| `style.css` — nuevas clases `.persona-*` | `submitDiagnostico()` — solo **añadir** `state.ia` |
| `whatsapp-demo.*` — página aislada | `almacen.py`, `seed_demo.py`, `gemini_ia.py` |

### Separación de vistas

```
index.html (#app)
├── Hash ""        → Persona (state.screen)     ← Pantallas 1 y 4
├── Hash "#dashboard" → Entidades               ← Pantalla 2
└── whatsapp-demo.html (página aparte)          ← Pantalla 3
```

**No unificar** WhatsApp dentro de `app.js` en esta fase: la demo ya funciona aislada y el riesgo de regresión es alto.

---

## 3. Checklist de revisión por pantalla

### Pantalla 1 — Inicio (`renderWelcome`)

- [ ] Tabs Persona / Entidades en header
- [ ] Botón «Iniciar diagnóstico» → `route-select`
- [ ] Botón «Canal WhatsApp (demo)» → `whatsapp-demo.html`
- [ ] Botón «Consultar pasaporte» → `pasaporte-lookup`
- [ ] Botón «Panel de entidades» → `#dashboard`
- [ ] Canales WEB / WHATSAPP (badges semáforo)

**Prueba de regresión:** completar flujo Persona → resultado → volver al inicio.

---

### Pantalla 2 — Entidades (`#dashboard`)

- [ ] ML1 necesidades emergentes
- [ ] Mapa ML2 (Leaflet + clusters)
- [ ] Oferta vs demanda + brechas por municipio
- [ ] Priorización entidad
- [ ] Demo A (Cali) / Demo B (Popayán/Quibdó)
- [ ] Resumen Gemini territorial
- [ ] *(Pendiente diseño)* Sidebar de navegación lateral
- [ ] *(Pendiente diseño)* Layout 2 columnas tipo mockup alcaldía

**Prueba de regresión:** cargar A → cargar B → verificar municipios distintos en mapa y Gemini.

---

### Pantalla 3 — WhatsApp (`whatsapp-demo.html`)

- [ ] Mockup teléfono + burbujas
- [ ] Panel JSON derecho
- [ ] 3 rutas + recorrido guiado
- [ ] `POST /diagnostico` al completar
- [ ] Fallback local si API cae

**Prueba de regresión:** recorrido guiado ruta 3 → JSON con `pasaporte.id`.

---

### Pantalla 4 — Plan persona (`renderResult`) ← objetivo del mockup

- [ ] Saludo «Hola, {nombre}» + ID pasaporte
- [ ] Badge prioridad alta / media
- [ ] Tarjeta **Resumen ejecutivo (IA)** — usa `response.ia`
- [ ] Tarjeta **Diagnóstico actual** (ruta, municipio, afectación, urgencia)
- [ ] **Recursos compatibles** con contador y acciones
- [ ] **Stepper de progreso** (5 pasos del journey)
- [ ] Acciones demo: Descargar PDF / Compartir (toast, sin backend)
- [ ] Checkboxes de acciones del pasaporte (existente)

**Prueba de regresión:** diagnóstico ingresos Cali → pantalla 4 → marcar acción → progreso sube.

---

## 4. Plan de implementación por fases

### Fase 0 — Baseline (antes de tocar UI)

1. Servidor: `uvicorn app.main:app --reload --port 8015`
2. Probar: diagnóstico web, consulta PAS-0001, dashboard, seed A/B, WhatsApp demo
3. Anotar capturas «antes»

### Fase 1 — Pantalla 4 persona (prioridad)

| Paso | Archivo | Cambio |
|------|---------|--------|
| 1 | `app.js` | Guardar `state.ia` y `state.diagnostico` en `submitDiagnostico()` |
| 2 | `app.js` | Campo opcional «nombre» en paso 1 del quiz |
| 3 | `app.js` | Reescribir `renderResult()` con layout 2 columnas |
| 4 | `style.css` | Clases `.persona-home`, `.persona-stepper`, etc. |
| 5 | — | **No** cambiar `renderPasaporte()` internamente; reutilizar lógica de acciones |

### Fase 2 — Pantalla 2 entidades (cosmética)

| Paso | Archivo | Cambio |
|------|---------|--------|
| 1 | `renderDashboard()` | Grid con sidebar sticky (solo HTML/CSS) |
| 2 | `style.css` | `.dashboard-layout` con nav lateral |
| 3 | — | Secciones existentes **sin renombrar** IDs usados por Leaflet |

### Fase 3 — Pantalla 1 pulido

| Paso | Cambio |
|------|--------|
| 1 | Ajustar copy y espaciado de `renderWelcome()` al mockup |
| 2 | Footer con links demo (opcional) |

### Fase 4 — Pantalla 3 (opcional)

| Paso | Cambio |
|------|--------|
| 1 | Link «Ver mi plan» post-chat → `index.html` + consulta pasaporte |
| 2 | Solo si hay tiempo; no bloqueante |

---

## 5. Matriz de dependencias de datos (Pantalla 4)

| UI mockup | Fuente API | Campo |
|-----------|------------|-------|
| ID PAS-0001 | `pasaporte.id` | ✅ |
| Prioridad alta | `pasaporte.prioridad_etiqueta` | ✅ |
| Hola, María | `state.nombre` (opcional, paso 1) | 🆕 frontend |
| Resumen IA | `ia.recomendacion_ia.explicacion` + `ia.confianza_ia` | ✅ ya en response |
| Ruta elegida | `pasaporte.ruta_nombre` | ✅ |
| Ubicación | `pasaporte.municipio` | ✅ |
| Tipo afectación | `pasaporte.danos` / necesidades | ✅ |
| Urgencia | `diagnostico.urgencia` / prioridad | ✅ |
| Recursos (5) | `resultado.ayudas` | ✅ |
| Progreso stepper | `pasaporte.progreso` + acciones | ✅ |

**No hace falta nuevo endpoint** para la pantalla 4.

---

## 6. Smoke test final (5 minutos)

```text
1. http://127.0.0.1:8015/ → Iniciar diagnóstico → Ingresos → Cali → completar
   → Ver pantalla 4 con IA, recursos y stepper

2. Consultar pasaporte PAS-0001 → carga progreso

3. #dashboard → Cargar datos A → Cargar datos B → municipios cambian

4. whatsapp-demo.html → Recorrido guiado → JSON válido

5. Reiniciar servidor → todo sigue funcionando
```

---

## 7. Qué NO hacer en esta iteración

- ❌ Migrar a React/Vue
- ❌ Fusionar WhatsApp dentro de `app.js`
- ❌ Cambiar schemas Pydantic del diagnóstico
- ❌ Renombrar endpoints
- ❌ Eliminar `renderPasaporte()` (otras vistas lo usan)
- ❌ PDF real (solo botón demo con toast)

---

*Última actualización: Fase 1 completada — pantalla 4 persona post-diagnóstico.*
