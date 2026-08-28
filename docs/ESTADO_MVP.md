# Estado MVP PIR — cierre honesto (hackathon)

## ✅ Listo hoy

| Pieza | Estado |
|-------|--------|
| 3 rutas diagnóstico (web + demo WhatsApp) | ✅ |
| Pasaporte dinámico + progreso | ✅ |
| Dashboard entidades (brechas, alertas, semáforos) | ✅ |
| ML1 necesidades emergentes (estadístico) | ✅ |
| ML2 mapa clusters básico (Leaflet) | ✅ |
| **Gemini gratis** — NLU, confianza ML4, recomendación ML3, resumen ML1 | ✅ |
| Demo WhatsApp funcional (`/whatsapp-demo.html`) | ✅ |
| Seed demo 150 casos | ✅ |

## 🔶 En otro equipo / pendiente corto

| Pieza | Quién | Notas |
|-------|-------|-------|
| **Google Maps** integración territorial | Equipo Maps | Reemplazará/complementará coords en ML2 |
| **Clusters geográficos finales** | Después de Maps | Hoy ML2 agrupa por municipio; falta lat/lng real |
| **Twilio WhatsApp producción** | Pendiente | Sandbox + webhook; código en stash `whatsapp-rutas` |
| **Persistencia BD** | Post-hackathon | Hoy todo en RAM (`almacen.py`) |
| **Seguimiento D+3** (“¿pudiste acceder?”) | Nice-to-have | intru2.md — cron + Twilio outbound |

## 🤖 Gemini (tier gratuito)

Variables `.env`:
```env
GEMINI_API_KEY=tu_key_de_ai_studio
GEMINI_MODEL=gemini-3.5-flash-lite
```

Endpoints:
- `GET /integraciones/gemini?probar=true` — estado
- `POST /ia/interpretar` — `{ "mensaje": "..." }`
- `POST /diagnostico` — incluye bloque `"ia"` en respuesta
- `GET /ml/necesidades-emergentes` — incluye `"resumen_ia"`

**No usa Gemini para:** conteos ML1, clusters ML2 (Python), matching base del catálogo.

## 🎯 Para cerrar el pitch (5 demos intru2)

1. ✅ María/demo completa ruta → pasaporte  
2. ✅ Aparece en dashboard (seed + mapa)  
3. ✅ ML1 detecta patrón (seed 100)  
4. ✅ Gemini explica recomendación / confianza  
5. 🔶 Maps del otro equipo + merge cluster  

## Comandos rápidos

```bash
# Backend
.\venv\Scripts\uvicorn.exe app.main:app --reload --port 8001

# Frontend + demo WhatsApp
cd app\frontend && ..\..\venv\Scripts\python.exe -m http.server 8080
```

Demo: http://127.0.0.1:8080/whatsapp-demo.html
