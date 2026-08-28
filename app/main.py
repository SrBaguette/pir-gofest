from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
    EscenariosInput,
)
from app.services.almacen import (
    crear_pasaporte,
    listar_pasaportes,
    marcar_accion_completada,
    obtener_pasaporte,
    obtener_resumen_dashboard,
)
from app.services.catalogo_recursos import obtener_catalogo_publico as catalogo_publico
from app.services.escenarios import simular_escenarios
from app.services.motor_ruta import generar_ruta, obtener_catalogo_publico
from app.services.gemini_ia import (
    enriquecer_diagnostico,
    estado_gemini,
    interpretar_mensaje,
    resumir_alertas_ml1,
)
from app.services.seed_demo import generar_casos
from app.services.twilio_whatsapp import estado_integracion, manejar_webhook

app = FastAPI(
    title="Pasaporte Inteligente de Recuperación",
    description="Plataforma adaptativa de recuperación post-emergencia",
    version="0.4.0",
)

FRONTEND_DIR = Path(__file__).parent / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parsear_diagnostico(body: dict):
    tipo_ruta = body.get("tipo_ruta", "ingresos")
    if tipo_ruta == "ayuda_inmediata":
        return DiagnosticoAyudaInmediata(**body)
    if tipo_ruta == "vivienda":
        return DiagnosticoVivienda(**body)
    if tipo_ruta == "ingresos":
        return DiagnosticoIngresos(**body)
    raise HTTPException(status_code=422, detail="tipo_ruta inválido")


@app.get("/")
def inicio():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/diagnostico")
async def diagnostico(request: Request):
    body = await request.json()
    datos = _parsear_diagnostico(body)
    resultado = generar_ruta(datos)
    pasaporte = crear_pasaporte(datos, resultado)
    ia = enriquecer_diagnostico(datos.model_dump(), resultado, pasaporte)
    return {
        "diagnostico": datos.model_dump(),
        "resultado": resultado,
        "pasaporte": pasaporte,
        "ia": ia,
    }


@app.get("/pasaporte/{pasaporte_id}")
def get_pasaporte(pasaporte_id: str):
    return obtener_pasaporte(pasaporte_id)


@app.patch("/pasaporte/{pasaporte_id}/accion/{numero}")
def completar_accion(pasaporte_id: str, numero: int):
    return marcar_accion_completada(pasaporte_id, numero)


@app.get("/dashboard/resumen")
def dashboard_resumen():
    return obtener_resumen_dashboard(obtener_catalogo_publico())


@app.get("/recursos/catalogo")
def recursos_catalogo():
    """150 recursos demostrativos distribuidos por zona sísmica (Valle/Cauca)."""
    return {
        "total": len(catalogo_publico()),
        "demostrativo": True,
        "recursos": catalogo_publico(),
    }


@app.post("/dashboard/escenarios")
def dashboard_escenarios(entrada: EscenariosInput):
    resumen = obtener_resumen_dashboard(obtener_catalogo_publico())
    return simular_escenarios(
        listar_pasaportes(),
        resumen.get("brechas", []),
        presupuesto_millones=entrada.presupuesto_millones,
        kits_emergencia=entrada.kits_emergencia,
        tecnicos=entrada.tecnicos,
    )


@app.get("/ml/necesidades-emergentes")
def ml_necesidades_emergentes():
    """ML 1 — Detector de necesidades emergentes."""
    resumen = obtener_resumen_dashboard(obtener_catalogo_publico())
    return {
        "alertas": resumen.get("ml_necesidades_emergentes", []),
        "tendencia": resumen.get("tendencia_emergente"),
        "resumen_ia": resumir_alertas_ml1(
            resumen.get("ml_necesidades_emergentes", []),
            resumen,
        ),
    }


@app.get("/ml/mapa")
def ml_mapa_inteligente():
    """ML 2 — Mapa inteligente con clusters de afectación."""
    resumen = obtener_resumen_dashboard(obtener_catalogo_publico())
    return resumen.get("mapa_inteligente", {})


@app.post("/webhook/whatsapp")
async def webhook_whatsapp(request: Request):
    twiml = await manejar_webhook(request)
    return Response(content=twiml, media_type="application/xml")


@app.get("/integraciones/gemini")
def integracion_gemini(probar: bool = False):
    return estado_gemini(probar_conexion=probar)


@app.post("/ia/interpretar")
async def ia_interpretar(request: Request):
    body = await request.json()
    mensaje = (body.get("mensaje") or "").strip()
    if not mensaje:
        raise HTTPException(status_code=400, detail="mensaje requerido")
    interpretacion = interpretar_mensaje(mensaje, body.get("contexto"))
    if interpretacion is None:
        return {
            "activo": False,
            "mensaje": "Gemini no disponible — use menú 1/2/3",
        }
    return {"activo": True, "interpretacion": interpretacion}


@app.get("/integraciones/twilio")
def integracion_twilio():
    return estado_integracion()


@app.post("/demo/seed")
def demo_seed(cantidad: int = 150, reemplazar: bool = False):
    if cantidad < 1 or cantidad > 500:
        raise HTTPException(status_code=400, detail="cantidad debe estar entre 1 y 500")
    return generar_casos(cantidad=cantidad, reemplazar=reemplazar)


app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend",
)
