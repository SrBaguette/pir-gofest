from fastapi import FastAPI, HTTPException, Request
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

app = FastAPI(
    title="Ruta de Recuperación",
    description="Motor inteligente de rutas de recuperación para comunidades afectadas por sismos",
    version="0.1.0"
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
    return {
        "mensaje": "Ruta de Recuperación API funcionando",
        "version": "0.1.0"
    }


@app.post("/diagnostico")
async def diagnostico(request: Request):
    """
    Punto de entrada del diagnóstico.
    Cualquier canal (Web, WhatsApp futuro, etc.) puede usar este endpoint.
    """
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
