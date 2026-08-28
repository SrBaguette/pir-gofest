from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
)
from app.services.almacen import (
    crear_pasaporte,
    marcar_accion_completada,
    obtener_pasaporte,
    obtener_resumen_dashboard,
)
from app.services.motor_ruta import generar_ruta, obtener_catalogo_publico
from app.services.seed_demo import generar_casos
from app.services.twilio_whatsapp import estado_integracion, manejar_webhook

app = FastAPI(
    title="Pasaporte Inteligente de Recuperación",
    description="Plataforma adaptativa de recuperación post-emergencia",
    version="0.3.0",
)

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
    twilio = estado_integracion()
    return {
        "mensaje": "Pasaporte Inteligente de Recuperación API funcionando",
        "version": "0.3.0",
        "modulos_ml": ["ml1_necesidades_emergentes", "ml2_mapa_inteligente"],
        "whatsapp": {
            "configurado": twilio["configurado"],
            "webhook": twilio["webhook_url"],
        },
    }


@app.post("/diagnostico")
async def diagnostico(request: Request):
    body = await request.json()
    datos = _parsear_diagnostico(body)
    resultado = generar_ruta(datos)
    pasaporte = crear_pasaporte(datos, resultado)
    return {
        "diagnostico": datos.model_dump(),
        "resultado": resultado,
        "pasaporte": pasaporte,
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


@app.get("/ml/necesidades-emergentes")
def ml_necesidades_emergentes():
    """ML 1 — Detector de necesidades emergentes."""
    resumen = obtener_resumen_dashboard(obtener_catalogo_publico())
    return {
        "alertas": resumen.get("ml_necesidades_emergentes", []),
        "tendencia": resumen.get("tendencia_emergente"),
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


@app.get("/integraciones/twilio")
def integracion_twilio():
    return estado_integracion()


@app.post("/demo/seed")
def demo_seed(cantidad: int = 100, reemplazar: bool = False):
    if cantidad < 1 or cantidad > 500:
        raise HTTPException(status_code=400, detail="cantidad debe estar entre 1 y 500")
    return generar_casos(cantidad=cantidad, reemplazar=reemplazar)
