"""
Generación de casos demostrativos anonimizados para el dashboard y la demo del hackathon.

Distribución por zonas sísmicas (250 casos por defecto):
- Valle Sur (rojo): mayor concentración — epicentro demo en Cali
- Valle Norte (amarillo): concentración media
- Cauca (verde): menor concentración
"""

import random

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
)
from app.services.almacen import (
    crear_pasaporte,
    establecer_perfil_demo,
    limpiar_pasaportes,
    listar_pasaportes,
    marcar_accion_completada,
)
from app.services.catalogo_recursos import ZONAS_SISMICAS
from app.services.ml_necesidades import registrar_snapshot, registrar_snapshot_demo_previo
from app.services.motor_ruta import generar_ruta

ACTIVIDADES = ["tienda", "restaurante", "taller", "panadería", "agricultura", "comercio"]
DANOS = ["equipos", "local", "maquinaria", "mercancía", "herramientas", "infraestructura"]
NECESIDADES_INGRESOS = ["equipamiento", "dinero", "financiamiento", "reparación", "insumos", "transporte"]
NECESIDADES_INMEDIATAS = ["alojamiento", "alimentación", "agua", "medicamentos", "servicios básicos"]
AFECTACIONES = ["estructural", "grietas", "techo", "servicios"]
HABITABILIDAD = ["no habitable", "parcialmente habitable", "habitable"]
SERVICIOS = [["agua", "luz"], ["gas", "drenaje"], ["agua"], ["luz"], ["ninguno"]]

# Perfil A — hotspot Cali / Valle Sur (financiamiento)
PESOS_ZONA_A = {
    "Valle Sur": 0.42,
    "Valle Norte": 0.33,
    "Cauca": 0.25,
}
PESO_CALI_EN_VALLE_SUR_A = 0.68

# Perfil B — hotspot Popayán + Quibdó + Palmira (vivienda/agua), sin Cali ni Pasto
PESOS_ZONA_B = {
    "Cauca": 0.40,
    "Valle Norte": 0.35,
    "Valle Sur": 0.25,
}
PESOS_MUNICIPIO_B: dict[str, dict[str, float]] = {
    "Cauca": {
        "Popayán": 0.38,
        "Quibdó": 0.32,
        "Santander de Quilichao": 0.18,
        "Puerto Tejada": 0.12,
    },
    "Valle Norte": {"Palmira": 0.38, "Buga": 0.32, "Tuluá": 0.20, "Cartago": 0.10},
    "Valle Sur": {"Yumbo": 0.34, "Jamundí": 0.33, "Florida": 0.33},
}

DESCRIPCION_PERFILES = {
    "a": "Escenario A: concentración en Cali (Valle Sur) — financiamiento y negocios detenidos.",
    "b": "Escenario B: Popayán, Quibdó y Palmira — vivienda y agua en el corredor Valle–Pacífico, sin Cali.",
}

def obtener_perfil_demo() -> str | None:
    from app.services.almacen import obtener_perfil_demo as _obtener

    return _obtener()


def _municipio_por_zona(zona: str, perfil: str) -> str:
    municipios = ZONAS_SISMICAS[zona]
    if perfil == "b":
        pesos_mun = PESOS_MUNICIPIO_B.get(zona, {})
        if pesos_mun:
            nombres = list(pesos_mun.keys())
            pesos = list(pesos_mun.values())
            return random.choices(nombres, weights=pesos, k=1)[0]
        return random.choice(municipios)

    if zona == "Valle Sur":
        if random.random() < PESO_CALI_EN_VALLE_SUR_A:
            return "Cali"
        otros = [m for m in municipios if m != "Cali"]
        return random.choice(otros)
    return random.choice(municipios)


def _asignar_zona_municipio(perfil: str) -> tuple[str, str]:
    pesos = PESOS_ZONA_B if perfil == "b" else PESOS_ZONA_A
    zona = random.choices(list(pesos.keys()), weights=list(pesos.values()), k=1)[0]
    return zona, _municipio_por_zona(zona, perfil)


def _caso_valle_sur(municipio: str):
    """Hotspot rojo: ingresos detenidos + financiamiento (Cali) o vivienda crítica."""
    if municipio == "Cali":
        return DiagnosticoIngresos(
            municipio=municipio,
            actividad_economica=random.choice(ACTIVIDADES),
            danos=random.sample(DANOS, k=2),
            puede_operar=False,
            necesidades=[random.choice(["financiamiento", "financiamiento", "equipamiento"]),
                         random.choice(["insumos", "equipamiento"])],
        )
    if random.random() < 0.45:
        return DiagnosticoVivienda(
            municipio=municipio,
            tipo_afectacion=random.sample(AFECTACIONES, k=2),
            habitabilidad=random.choice(["no habitable", "parcialmente habitable"]),
            servicios_afectados=random.choice(SERVICIOS),
            evidencia="evidencia_foto" if random.random() > 0.4 else "",
        )
    return DiagnosticoAyudaInmediata(
        municipio=municipio,
        personas_hogar=random.randint(2, 8),
        necesidad=random.choice(NECESIDADES_INMEDIATAS),
        urgencia=random.choice(["alta", "alta", "media"]),
        evidencia="foto_adjunta_demo" if random.random() > 0.35 else "",
    )


def _caso_valle_norte(municipio: str):
    """Amarillo: mezcla vivienda + ingresos con urgencia media."""
    roll = random.random()
    if roll < 0.45:
        return DiagnosticoVivienda(
            municipio=municipio,
            tipo_afectacion=random.sample(AFECTACIONES, k=random.randint(1, 2)),
            habitabilidad=random.choice(["parcialmente habitable", "no habitable", "habitable"]),
            servicios_afectados=random.choice(SERVICIOS),
            evidencia="evidencia_foto" if random.random() > 0.5 else "",
        )
    if roll < 0.75:
        return DiagnosticoIngresos(
            municipio=municipio,
            actividad_economica=random.choice(ACTIVIDADES),
            danos=random.sample(DANOS, k=random.randint(1, 2)),
            puede_operar=random.random() > 0.5,
            necesidades=random.sample(NECESIDADES_INGRESOS, k=2),
        )
    return DiagnosticoAyudaInmediata(
        municipio=municipio,
        personas_hogar=random.randint(1, 6),
        necesidad=random.choice(NECESIDADES_INMEDIATAS),
        urgencia=random.choice(["media", "alta", "baja"]),
        evidencia="",
    )


def _caso_cauca(municipio: str):
    """Verde: menor presión — ayuda inmediata baja/media y vivienda habitable parcial."""
    roll = random.random()
    if roll < 0.4:
        return DiagnosticoAyudaInmediata(
            municipio=municipio,
            personas_hogar=random.randint(1, 5),
            necesidad=random.choice(NECESIDADES_INMEDIATAS),
            urgencia=random.choice(["baja", "media", "baja"]),
            evidencia="",
        )
    if roll < 0.7:
        return DiagnosticoVivienda(
            municipio=municipio,
            tipo_afectacion=random.sample(AFECTACIONES, k=1),
            habitabilidad=random.choice(["habitable", "parcialmente habitable"]),
            servicios_afectados=random.choice(SERVICIOS),
            evidencia="",
        )
    return DiagnosticoIngresos(
        municipio=municipio,
        actividad_economica=random.choice(ACTIVIDADES),
        danos=random.sample(DANOS, k=1),
        puede_operar=random.random() > 0.35,
        necesidades=random.sample(NECESIDADES_INGRESOS, k=1),
    )


def _caso_perfil_b(zona: str, municipio: str):
    """Escenario B: vivienda/agua en Cauca y Norte; equipamiento en Sur sin Cali."""
    if zona == "Cauca":
        if municipio in ("Popayán", "Quibdó"):
            if random.random() < 0.55:
                return DiagnosticoVivienda(
                    municipio=municipio,
                    tipo_afectacion=["estructural", "grietas"],
                    habitabilidad="no habitable",
                    servicios_afectados=["agua", "luz"],
                    evidencia="evidencia_foto",
                )
            return DiagnosticoAyudaInmediata(
                municipio=municipio,
                personas_hogar=random.randint(3, 9),
                necesidad=random.choice(["agua", "alojamiento", "medicamentos"]),
                urgencia="alta",
                evidencia="foto_adjunta_demo",
            )
        return DiagnosticoVivienda(
            municipio=municipio,
            tipo_afectacion=random.sample(AFECTACIONES, k=2),
            habitabilidad=random.choice(["no habitable", "parcialmente habitable"]),
            servicios_afectados=random.choice(SERVICIOS),
            evidencia="evidencia_foto" if random.random() > 0.4 else "",
        )

    if zona == "Valle Norte":
        if random.random() < 0.6:
            return DiagnosticoVivienda(
                municipio=municipio,
                tipo_afectacion=["estructural", "techo"],
                habitabilidad=random.choice(["no habitable", "parcialmente habitable"]),
                servicios_afectados=["agua", "gas"],
                evidencia="evidencia_foto",
            )
        return DiagnosticoAyudaInmediata(
            municipio=municipio,
            personas_hogar=random.randint(2, 7),
            necesidad=random.choice(["agua", "alimentación", "alojamiento"]),
            urgencia=random.choice(["alta", "media"]),
            evidencia="",
        )

    return DiagnosticoIngresos(
        municipio=municipio,
        actividad_economica=random.choice(ACTIVIDADES),
        danos=random.sample(DANOS, k=2),
        puede_operar=random.random() > 0.55,
        necesidades=[random.choice(["equipamiento", "insumos"]),
                     random.choice(["reparación", "transporte"])],
    )


def _generar_caso(zona: str, municipio: str, perfil: str = "a"):
    if perfil == "b":
        return _caso_perfil_b(zona, municipio)
    if zona == "Valle Sur":
        return _caso_valle_sur(municipio)
    if zona == "Valle Norte":
        return _caso_valle_norte(municipio)
    return _caso_cauca(municipio)


def generar_casos(cantidad: int = 250, reemplazar: bool = False, perfil: str = "a") -> dict:
    perfil = perfil.lower().strip()
    if perfil not in DESCRIPCION_PERFILES:
        perfil = "a"

    if reemplazar:
        limpiar_pasaportes()

    establecer_perfil_demo(perfil)
    pesos_zona = PESOS_ZONA_B if perfil == "b" else PESOS_ZONA_A
    creados = []
    conteo_zona: dict[str, int] = {z: 0 for z in pesos_zona}
    conteo_municipio: dict[str, int] = {}

    for _ in range(cantidad):
        zona, municipio = _asignar_zona_municipio(perfil)
        datos = _generar_caso(zona, municipio, perfil)
        resultado = generar_ruta(datos)
        pasaporte = crear_pasaporte(datos, resultado)

        if random.random() < 0.22:
            acciones = random.randint(1, len(pasaporte["ruta"]))
            for j in range(acciones):
                pasaporte = marcar_accion_completada(pasaporte["id"], j)

        creados.append(pasaporte["id"])
        conteo_zona[zona] = conteo_zona.get(zona, 0) + 1
        conteo_municipio[municipio] = conteo_municipio.get(municipio, 0) + 1

    lista = listar_pasaportes()
    registrar_snapshot_demo_previo(lista)
    registrar_snapshot(lista)

    hotspot = max(conteo_municipio, key=conteo_municipio.get) if conteo_municipio else "Cali"

    return {
        "generados": len(creados),
        "perfil": perfil,
        "perfil_descripcion": DESCRIPCION_PERFILES[perfil],
        "ids_muestra": creados[:5],
        "mensaje": (
            f"Escenario {perfil.upper()}: {len(creados)} casos — {DESCRIPCION_PERFILES[perfil]} "
            f"Hotspot: {hotspot}."
        ),
        "distribucion_zonas": conteo_zona,
        "distribucion_municipios": dict(
            sorted(conteo_municipio.items(), key=lambda x: x[1], reverse=True)
        ),
        "municipio_hotspot": hotspot,
    }
