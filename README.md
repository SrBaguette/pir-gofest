# Pasaporte Inteligente de Recuperación (PIR)

Plataforma para la optimización en la distribución de recursos de los afectados por el terremoto de Colombia 2026 — **GoFest**.

> Cada persona recibe una ruta. Cada interacción genera inteligencia. Cada recurso puede generar más recuperación.

## Problema

Después de una emergencia hay muchas personas afectadas, muchas entidades dispuestas a ayudar y muchos datos — pero existe una desconexión: no sabemos suficientemente rápido **quién necesita qué, dónde está, qué tan urgente es, qué ayuda le sirve y si logró recuperarse**.

## Solución (MVP actual)

Canal **Web** (WhatsApp planificado) → **3 rutas de diagnóstico** → **Motor de ruta** → **Pasaporte de Recuperación** → **Dashboard de entidad** con alertas y brechas.

```text
Persona (Web)  →  POST /diagnostico  →  Motor de ruta  →  Pasaporte PAS-XXXX
                                              ↓
Entidad        →  GET /dashboard/resumen  ←  Agregación en memoria
```

### Las 3 rutas

| Ruta | Caso de uso | Campos clave |
|------|-------------|--------------|
| Ayuda inmediata | Alimentación, alojamiento, agua, medicamentos | municipio, personas, necesidad, urgencia |
| Recuperar vivienda | Daños estructurales, habitabilidad | tipo afectación, habitabilidad, servicios |
| Recuperar ingresos | Comercio, emprendimiento, productor | actividad, daños, puede operar, necesidades |

### Pasaporte de Recuperación

- ID único (`PAS-0001`)
- Ruta personalizada con acciones marcables
- Progreso dinámico (% completado)
- Consulta posterior por ID
- Ayudas compatibles (catálogo demostrativo)

### Dashboard para Gobierno / Alcaldías

Responde a las 5 preguntas clave del producto:

1. **¿Dónde están los afectados?** — por municipio
2. **¿Qué necesitan?** — ranking de necesidades
3. **¿Qué está empeorando?** — alertas y tendencias
4. **¿Qué ayudas tenemos?** — catálogo demostrativo
5. **¿Dónde hay brecha?** — necesidad vs recursos

## Stack

- Python 3.12 + FastAPI + Pydantic
- Frontend HTML/CSS/JS vanilla (sin frameworks)
- Almacenamiento en memoria (MVP hackathon)
- API canal-agnóstica (lista para WhatsApp/Twilio)

## Cómo ejecutar

```bash
# 1. Entorno
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. Backend (puerto 8001)
uvicorn app.main:app --reload --port 8001

# 3. Frontend (otra terminal, puerto 8080)
cd app/frontend
python -m http.server 8080
```

Abrir [http://127.0.0.1:8080](http://127.0.0.1:8080)

## API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/diagnostico` | Diagnóstico + ruta + pasaporte |
| GET | `/pasaporte/{id}` | Consultar pasaporte |
| PATCH | `/pasaporte/{id}/accion/{n}` | Marcar acción completada |
| GET | `/dashboard/resumen` | Agregados, alertas, brechas |

## Roadmap (visión completa)

- [ ] WhatsApp / Twilio + Gemini (conversación)
- [ ] Google Maps / clusters geográficos
- [ ] BigQuery + Vertex AI (ML: tendencias, recomendaciones, anomalías)
- [ ] Índice de confianza del reporte
- [ ] Módulo WOW: "Tengo recursos, ¿dónde los pongo?"
- [ ] Seguimiento proactivo (¿pudiste acceder a la ayuda?)

Ver [`instruccion.md`](instruccion.md) para el documento maestro de producto.

## Equipo

Proyecto GoFest — optimización en la distribución de recursos para afectados por el terremoto de Colombia 2026.
