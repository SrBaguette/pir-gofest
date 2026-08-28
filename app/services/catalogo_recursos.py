"""
Catálogo demostrativo de 150 recursos distribuidos por zona de afectación sísmica
(Valle del Cauca y Cauca — contexto GoFest / intru2).

Cada recurso tiene unidades disponibles por municipio. Las brechas del dashboard
comparan solicitudes reales vs cupos disponibles en la misma zona/categoría.
"""

from __future__ import annotations

ZONAS_SISMICAS = {
    "Valle Norte": ["Palmira", "Buga", "Cartago", "Tuluá"],
    "Valle Sur": ["Cali", "Yumbo", "Jamundí", "Florida"],
    "Cauca": ["Popayán", "Quibdó", "Santander de Quilichao", "Puerto Tejada"],
}

MUNICIPIO_A_ZONA: dict[str, str] = {}
for zona, municipios in ZONAS_SISMICAS.items():
    for m in municipios:
        MUNICIPIO_A_ZONA[m.lower()] = zona

# Plantillas por categoría (alineadas a intru2 / instruccion.md)
PLANTILLAS_CATEGORIA = [
    {
        "categoria": "Alojamiento",
        "prefijo": "Cupos alojamiento temporal",
        "descripcion": "Alojamiento de emergencia para familias desplazadas por afectación sísmica.",
        "necesidades_compatibles": ["alojamiento", "vivienda", "servicios básicos"],
        "rutas_compatibles": ["ayuda_inmediata"],
        "unidades_base": (2, 5),
    },
    {
        "categoria": "Alimentación",
        "prefijo": "Kit alimentación",
        "descripcion": "Kit demostrativo de alimentación para hogares afectados.",
        "necesidades_compatibles": ["alimentacion", "alimentación"],
        "rutas_compatibles": ["ayuda_inmediata"],
        "unidades_base": (8, 20),
    },
    {
        "categoria": "Agua",
        "prefijo": "Punto de agua potable",
        "descripcion": "Suministro demostrativo de agua en zona de afectación.",
        "necesidades_compatibles": ["agua"],
        "rutas_compatibles": ["ayuda_inmediata"],
        "unidades_base": (3, 8),
    },
    {
        "categoria": "Salud",
        "prefijo": "Bolsa medicamentos básicos",
        "descripcion": "Apoyo demostrativo en medicamentos y primeros auxilios.",
        "necesidades_compatibles": ["medicamentos", "salud"],
        "rutas_compatibles": ["ayuda_inmediata"],
        "unidades_base": (4, 12),
    },
    {
        "categoria": "Evaluación",
        "prefijo": "Visita técnica habitabilidad",
        "descripcion": "Cupos demostrativos para evaluación técnica de vivienda.",
        "necesidades_compatibles": ["evaluacion", "evaluación", "reparacion", "reparación", "vivienda"],
        "rutas_compatibles": ["vivienda"],
        "unidades_base": (2, 6),
    },
    {
        "categoria": "Reparación",
        "prefijo": "Kit reparación básica vivienda",
        "descripcion": "Materiales demostrativos para reparación estructural menor.",
        "necesidades_compatibles": ["reparacion", "reparación", "vivienda"],
        "rutas_compatibles": ["vivienda"],
        "unidades_base": (3, 10),
    },
    {
        "categoria": "Reparación",
        "prefijo": "Cupos techo provisional",
        "descripcion": "Cobertura provisional de techo en viviendas afectadas.",
        "necesidades_compatibles": ["reparacion", "reparación", "vivienda"],
        "rutas_compatibles": ["vivienda"],
        "unidades_base": (2, 7),
    },
    {
        "categoria": "Equipamiento",
        "prefijo": "Kit equipamiento productivo",
        "descripcion": "Herramientas y equipos para reactivar actividad económica.",
        "necesidades_compatibles": ["equipamiento", "equipos"],
        "rutas_compatibles": ["ingresos"],
        "unidades_base": (2, 8),
    },
    {
        "categoria": "Financiamiento",
        "prefijo": "Cupo microcrédito recuperación",
        "descripcion": "Capital de trabajo demostrativo para negocios afectados.",
        "necesidades_compatibles": ["dinero", "financiamiento", "capital"],
        "rutas_compatibles": ["ingresos"],
        "unidades_base": (1, 4),
    },
    {
        "categoria": "Insumos",
        "prefijo": "Paquete insumos productivos",
        "descripcion": "Insumos para retomar operación comercial o productiva.",
        "necesidades_compatibles": ["insumos"],
        "rutas_compatibles": ["ingresos"],
        "unidades_base": (4, 12),
    },
    {
        "categoria": "Transporte",
        "prefijo": "Auxilio transporte temporal",
        "descripcion": "Apoyo logístico demostrativo durante la recuperación.",
        "necesidades_compatibles": ["transporte"],
        "rutas_compatibles": ["ingresos", "ayuda_inmediata"],
        "unidades_base": (3, 9),
    },
    {
        "categoria": "Espacio",
        "prefijo": "Espacio temporal comercial",
        "descripcion": "Local alterno demostrativo mientras se recupera el punto de venta.",
        "necesidades_compatibles": ["espacio"],
        "rutas_compatibles": ["ingresos"],
        "unidades_base": (1, 3),
    },
    {
        "categoria": "Equipamiento",
        "prefijo": "Kit herramientas taller",
        "descripcion": "Herramientas para talleres y oficios afectados.",
        "necesidades_compatibles": ["equipamiento", "equipos"],
        "rutas_compatibles": ["ingresos"],
        "unidades_base": (2, 6),
    },
    {
        "categoria": "Evaluación",
        "prefijo": "Asesoría técnica productiva",
        "descripcion": "Acompañamiento demostrativo para plan de reactivación económica.",
        "necesidades_compatibles": ["equipamiento", "financiamiento", "dinero"],
        "rutas_compatibles": ["ingresos"],
        "unidades_base": (2, 5),
    },
    {
        "categoria": "Alimentación",
        "prefijo": "Comedor comunitario temporal",
        "descripcion": "Raciones demostrativas en punto de atención municipal.",
        "necesidades_compatibles": ["alimentacion", "alimentación", "servicios básicos"],
        "rutas_compatibles": ["ayuda_inmediata"],
        "unidades_base": (5, 15),
    },
]

_CATALOGO_COMPLETO: list[dict] | None = None


def _generar_catalogo() -> list[dict]:
    recursos: list[dict] = []
    contador = 1
    municipios_orden = [m for zona in ZONAS_SISMICAS.values() for m in zona]

    for municipio in municipios_orden:
        zona = MUNICIPIO_A_ZONA[municipio.lower()]
        for plantilla in PLANTILLAS_CATEGORIA:
            min_u, max_u = plantilla["unidades_base"]
            # Variación determinística por municipio + categoría
            seed = sum(ord(c) for c in municipio + plantilla["categoria"]) % (max_u - min_u + 1)
            unidades = min_u + seed
            rec_id = f"REC-{str(contador).zfill(3)}"
            recursos.append({
                "id": rec_id,
                "nombre": f"{plantilla['prefijo']} — {municipio}",
                "descripcion": plantilla["descripcion"],
                "categoria": plantilla["categoria"],
                "zona_sismica": zona,
                "municipio": municipio,
                "unidades_disponibles": unidades,
                "unidades_totales": unidades,
                "necesidades_compatibles": list(plantilla["necesidades_compatibles"]),
                "danos_compatibles": [],
                "rutas_compatibles": list(plantilla["rutas_compatibles"]),
                "demostrativo": True,
            })
            contador += 1

    return recursos


def obtener_catalogo_completo() -> list[dict]:
    global _CATALOGO_COMPLETO
    if _CATALOGO_COMPLETO is None:
        _CATALOGO_COMPLETO = _generar_catalogo()
    return _CATALOGO_COMPLETO


def obtener_catalogo_publico() -> list[dict]:
    """Vista para dashboard y API (150 recursos con ubicación)."""
    return [
        {
            "id": r["id"],
            "nombre": r["nombre"],
            "descripcion": r["descripcion"],
            "categoria": r["categoria"],
            "zona_sismica": r["zona_sismica"],
            "municipio": r["municipio"],
            "unidades_disponibles": r["unidades_disponibles"],
            "demostrativo": True,
        }
        for r in obtener_catalogo_completo()
    ]


def obtener_zona_municipio(municipio: str) -> str:
    return MUNICIPIO_A_ZONA.get(municipio.lower().strip(), "Valle Sur")


def resumen_por_zona() -> list[dict]:
    por_zona: dict[str, dict] = {}
    for r in obtener_catalogo_completo():
        zona = r["zona_sismica"]
        if zona not in por_zona:
            por_zona[zona] = {"zona": zona, "recursos": 0, "unidades": 0, "municipios": set()}
        por_zona[zona]["recursos"] += 1
        por_zona[zona]["unidades"] += r["unidades_disponibles"]
        por_zona[zona]["municipios"].add(r["municipio"])
    return [
        {
            "zona": v["zona"],
            "recursos": v["recursos"],
            "unidades_totales": v["unidades"],
            "municipios": sorted(v["municipios"]),
        }
        for v in por_zona.values()
    ]
