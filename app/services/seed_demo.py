"""
Generación de casos demostrativos anonimizados para el dashboard y la demo del hackathon.
"""

import random

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
)
from app.services.almacen import crear_pasaporte, limpiar_pasaportes, marcar_accion_completada
from app.services.motor_ruta import generar_ruta

MUNICIPIOS = [
    "Popayán", "Pasto", "Cali", "Buga", "Palmira",
    "Tuluá", "Jamundí", "Yumbo", "Cartago", "Florida",
]

ACTIVIDADES = ["tienda", "restaurante", "taller", "panadería", "agricultura", "comercio"]
DANOS = ["equipos", "local", "maquinaria", "mercancía", "herramientas", "infraestructura"]
NECESIDADES_INGRESOS = ["equipamiento", "dinero", "financiamiento", "reparación", "insumos", "transporte"]
NECESIDADES_INMEDIATAS = ["alojamiento", "alimentación", "agua", "medicamentos", "servicios básicos"]
URGENCIAS = ["alta", "media", "baja"]
AFECTACIONES = ["estructural", "grietas", "techo", "servicios"]
HABITABILIDAD = ["no habitable", "parcialmente habitable", "habitable"]
SERVICIOS = [["agua", "luz"], ["gas", "drenaje"], ["agua"], ["luz"], ["ninguno"]]


def _caso_ayuda_inmediata() -> DiagnosticoAyudaInmediata:
    return DiagnosticoAyudaInmediata(
        municipio=random.choice(MUNICIPIOS),
        personas_hogar=random.randint(1, 8),
        necesidad=random.choice(NECESIDADES_INMEDIATAS),
        urgencia=random.choice(URGENCIAS),
        evidencia="foto_adjunta_demo" if random.random() > 0.4 else "",
    )


def _caso_vivienda() -> DiagnosticoVivienda:
    return DiagnosticoVivienda(
        municipio=random.choice(MUNICIPIOS),
        tipo_afectacion=random.sample(AFECTACIONES, k=random.randint(1, 2)),
        habitabilidad=random.choice(HABITABILIDAD),
        servicios_afectados=random.choice(SERVICIOS),
        evidencia="evidencia_foto" if random.random() > 0.5 else "",
    )


def _caso_ingresos() -> DiagnosticoIngresos:
    return DiagnosticoIngresos(
        municipio=random.choice(MUNICIPIOS),
        actividad_economica=random.choice(ACTIVIDADES),
        danos=random.sample(DANOS, k=random.randint(1, 3)),
        puede_operar=random.random() > 0.45,
        necesidades=random.sample(NECESIDADES_INGRESOS, k=random.randint(1, 2)),
    )


def generar_casos(cantidad: int = 100, reemplazar: bool = False) -> dict:
    if reemplazar:
        limpiar_pasaportes()

    generadores = [_caso_ayuda_inmediata, _caso_vivienda, _caso_ingresos]
    creados = []

    # Sesgo demo: ~35% de casos en Cali con necesidad financiera (visible en panel)
    zona_demo = "Cali"
    necesidad_demo = "financiamiento"

    for i in range(cantidad):
        if i < int(cantidad * 0.35):
            datos = DiagnosticoIngresos(
                municipio=zona_demo,
                actividad_economica=random.choice(ACTIVIDADES),
                danos=random.sample(DANOS, k=2),
                puede_operar=False,
                necesidades=[necesidad_demo, random.choice(["equipamiento", "insumos"])],
            )
        else:
            datos = random.choice(generadores)()

        resultado = generar_ruta(datos)
        pasaporte = crear_pasaporte(datos, resultado)

        if random.random() < 0.25:
            acciones = random.randint(1, len(pasaporte["ruta"]))
            for j in range(acciones):
                pasaporte = marcar_accion_completada(pasaporte["id"], j)

        creados.append(pasaporte["id"])

    return {
        "generados": len(creados),
        "ids_muestra": creados[:5],
        "mensaje": f"Se generaron {len(creados)} casos demostrativos anonimizados.",
        "zona_demo": zona_demo,
        "necesidad_demo": necesidad_demo,
    }
