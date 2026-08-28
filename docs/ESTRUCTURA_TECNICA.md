# PIR — Estructura técnica completa

> Pasaporte Inteligente de Recuperación · GoFest Hackathon  
> Versión MVP `0.4.0` · Backend FastAPI + Frontend vanilla + Cloud Run

---

## 1. Visión en una línea

```
Persona (WhatsApp/Web) → Diagnóstico → Pasaporte → Dashboard entidad
                              ↓
                    ML1 + ML2 + Brechas + Gemini (opcional)
```

---

## 2. Arquitectura de carpetas

```
hackaron22/
├── app/
│   ├── main.py                 # FastAPI: API + sirve frontend estático
│   ├── schemas.py              # Pydantic: 3 tipos de diagnóstico + escenarios
│   ├── frontend/               # HTML/CSS/JS (sin framework)
│   │   ├── index.html          # App principal + panel territorial
│   │   ├── app.js              # Lógica UI, dashboard, mapa Leaflet
│   │   ├── whatsapp-demo.*     # Demo canal WhatsApp (sin Twilio real)
│   │   └── style.css
│   └── services/
│       ├── almacen.py          # Pasaportes (RAM o PostgreSQL)
│       ├── base_datos.py       # SQLAlchemy + tablas Cloud SQL
│       ├── motor_ruta.py       # 3 rutas + matching de ayudas
│       ├── catalogo_recursos.py# 150 programas demo por municipio/zona
│       ├── seed_demo.py        # Genera 250 casos por zona sísmica
│       ├── semaforo.py         # Prioridad, confianza, brechas
│       ├── ml_necesidades.py   # ML1 — patrones emergentes
│       ├── ml_mapa.py          # ML2 — clusters + mapa OSM
│       ├── panel_decision.py   # Priorización para entidades
│       ├── escenarios.py       # Simulador (legacy API)
│       ├── gemini_ia.py        # IA narrativa (tier gratuito)
│       └── twilio_whatsapp.py  # Webhook WhatsApp
├── docs/
│   ├── ESTADO_MVP.md
│   ├── ESTRUCTURA_TECNICA.md   # Este archivo
│   └── TWILIO_SETUP.md
├── Procfile                    # Cloud Run: uvicorn
├── requirements.txt
└── .env                        # GEMINI_API_KEY, TWILIO, DATABASE_URL (no commitear)
```

---

## 3. Flujo de datos

### 3.1 Persona afectada

1. Completa formulario web o demo WhatsApp.
2. `POST /diagnostico` → `motor_ruta.py` genera ruta + ayudas compatibles.
3. `almacen.py` crea **Pasaporte** (`PAS-0001`) con progreso, prioridad, confianza.
4. `gemini_ia.py` opcionalmente enriquece con bloque `"ia"`.

### 3.2 Dashboard entidad

1. `GET /dashboard/resumen` agrega todos los pasaportes.
2. Calcula brechas, prioridades, ML1, ML2, alertas.
3. Frontend renderiza panel + mapa Leaflet (OpenStreetMap).

### 3.3 Demo masiva

1. `POST /demo/seed?cantidad=250&reemplazar=true`
2. `seed_demo.py` distribuye casos por zona sísmica (ver §5).

---

## 4. Las tres rutas de diagnóstico

| Ruta | Schema | Campos clave | Salida |
|------|--------|--------------|--------|
| Ayuda inmediata | `DiagnosticoAyudaInmediata` | necesidad, urgencia, personas_hogar | Kits, alojamiento, agua |
| Vivienda | `DiagnosticoVivienda` | habitabilidad, tipo_afectacion | Evaluación, reparación |
| Ingresos | `DiagnosticoIngresos` | puede_operar, danos, necesidades | Financiamiento, equipamiento |

**Motor:** `app/services/motor_ruta.py`  
**Matching:** busca en `catalogo_recursos.py` recursos del **mismo municipio**.

---

## 5. Zonas sísmicas y seed (250 casos)

Definidas en `catalogo_recursos.py`:

| Zona | Municipios | Peso seed | Semáforo | Perfil demo |
|------|------------|-----------|----------|-------------|
| **Valle Sur** | Cali, Yumbo, Jamundí, Florida | 42% | Rojo | Cali: financiamiento, no operativos |
| **Valle Norte** | Palmira, Buga, Cartago, Tuluá | 33% | Amarillo | Vivienda + ingresos mixtos |
| **Cauca** | Popayán, Pasto | 25% | Verde | Ayuda baja/media, menor presión |

Dentro de Valle Sur, **~68%** de casos van a **Cali** (hotspot del pitch).

---

## 6. Oferta vs demanda (recursos)

### Demanda (real en demo)
- Pasaportes registrados (`almacen.py`).
- Conteo de necesidades por municipio.

### Oferta (simulada)
- **150 programas** en catálogo (`catalogo_recursos.py`).
- **~844 cupos** totales (suma de `unidades_disponibles`).
- Marcados `demostrativo: true`.

### Brecha
```
Faltan = solicitudes_en_municipio − cupos_en_municipio (misma categoría)
```

Ejemplo con 250 casos: Cali financiamiento ~50+ solicitudes vs **3 cupos** → déficit visible.

**API catálogo:** `GET /recursos/catalogo`

---

## 7. ML1 — Necesidades emergentes

**Archivo:** `ml_necesidades.py`  
**Tipo:** Estadístico (no red neuronal).

Detecta:
- Concentración geográfica (misma necesidad en un municipio).
- Crecimiento temporal (snapshots entre consultas).

**API:** `GET /ml/necesidades-emergentes`  
**Gemini:** solo resume en `resumen_ia` — no genera alertas nuevas.

---

## 8. ML2 — Mapa inteligente (OpenStreetMap)

**Archivo:** `ml_mapa.py`  
**Frontend:** Leaflet + tiles OSM en `initMapaInteligente()`.

### Capas en el mapa
1. **Círculos de zona** (trazo punteado) — Valle Sur / Norte / Cauca con color semáforo.
2. **Clusters por municipio** — radio proporcional a casos, color rojo/amarillo/verde.
3. **Subclusters** — perfiles similares (misma ruta en un municipio).

### Semáforo
| Color | Zona | Significado pitch |
|-------|------|-------------------|
| Rojo | Valle Sur | Prioridad alta — epicentro demo |
| Amarillo | Valle Norte | Prioridad media |
| Verde | Cauca | Prioridad baja |

**API:** incluido en `GET /dashboard/resumen` → `mapa_inteligente`.

---

## 9. Panel de decisión para entidades

**Archivo:** `panel_decision.py`

Secciones del dashboard:
1. **Oferta vs demanda** — banner explicativo.
2. **¿Dónde invertir primero?** — acciones ordenadas por déficit.
3. **Brechas en {municipio}** — tabla con glosario.
4. **Recursos disponibles** — catálogo por zona.

**Alertas operativas:** reglas puras (`almacen._generar_alertas`).  
**Resumen IA:** sección aparte (Gemini).

---

## 10. Gemini (IA opcional)

**Archivo:** `gemini_ia.py`  
**Modelo:** `gemini-3.5-flash-lite` (tier gratuito en AI Studio).

| Usa IA | No usa IA |
|--------|-----------|
| NLU mensaje libre | Conteos ML1 |
| Narrativa confianza | Clusters ML2 |
| Resumen ejecutivo alcalde | Brechas y matching base |
| Enriquecer diagnóstico | Alertas operativas |

**Variables `.env`:**
```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.5-flash-lite
```

**Probar:** `GET /integraciones/gemini?probar=true`

---

## 11. Persistencia

| Modo | Cuándo | Archivo |
|------|--------|---------|
| **RAM** | Local sin `DATABASE_URL` | `almacen.py` dict `_pasaportes` |
| **PostgreSQL** | Cloud Run + Cloud SQL | `base_datos.py` + SQLAlchemy |

Tablas: `pasaportes`, `acciones_ruta`.

---

## 12. Despliegue

### Local (unificado — recomendado)
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8015
```
Abrir: **http://127.0.0.1:8015/**

Frontend y API mismo origen (`API_BASE = ""` en `app.js`).

### Cloud Run
- `Procfile` → uvicorn en `$PORT`.
- `main.py` monta `StaticFiles` en `/`.
- Variables: `DATABASE_URL`, `GEMINI_API_KEY`, Twilio.

---

## 13. Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Frontend index |
| POST | `/diagnostico` | Crear pasaporte |
| GET | `/pasaporte/{id}` | Consultar |
| PATCH | `/pasaporte/{id}/accion/{n}` | Marcar paso |
| GET | `/dashboard/resumen` | Panel completo |
| GET | `/recursos/catalogo` | 150 recursos |
| POST | `/demo/seed?cantidad=250` | Poblar demo |
| GET | `/ml/necesidades-emergentes` | ML1 + resumen IA |
| GET | `/ml/mapa` | ML2 |
| POST | `/webhook/whatsapp` | Twilio |
| GET | `/integraciones/gemini` | Estado IA |

---

## 14. Guion pitch (5 min)

1. **María** entra por web → elige ruta ingresos → pasaporte con ayudas en su municipio.
2. Panel territorial → **Cargar datos demo (250)**.
3. Mapa OSM: Valle Sur rojo (Cali hotspot), Cauca verde.
4. ML1: patrón financiamiento en Cali.
5. Brechas: «52 solicitudes vs 3 cupos de capital de trabajo».
6. Priorización: «Movilizar cupos en Cali».
7. Cierre: «Demanda real + oferta que declara la entidad = decisiones accionables».

---

## 15. Qué falta para producción

- Catálogo cargado por entidades (no simulado).
- Google Maps Platform (reemplaza coords fijas).
- Twilio WhatsApp flujo completo (P0+P1 en rama stash).
- Seguimiento D+3 automático.
- ML3 con aprendizaje histórico real.

---

*Documento generado para el equipo PIR — hackathon GoFest 2026.*
