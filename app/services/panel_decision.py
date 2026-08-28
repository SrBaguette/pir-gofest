"""
Priorización territorial para entidades — sustituye el simulador abstracto.

Traduce brechas y casos en acciones concretas que un alcalde o equipo
de respuesta puede entender sin ajustar sliders ni interpretar fórmulas.
"""

from app.services.catalogo_recursos import obtener_zona_municipio

ETIQUETAS_PROGRAMA = {
    "alojamiento": "Alojamiento temporal",
    "alimentación": "Kits de alimentación",
    "alimentacion": "Kits de alimentación",
    "agua": "Agua potable",
    "medicamentos": "Salud y medicamentos",
    "salud": "Salud y medicamentos",
    "reparación": "Reparación de vivienda",
    "reparacion": "Reparación de vivienda",
    "vivienda": "Reparación de vivienda",
    "equipamiento": "Equipamiento productivo",
    "equipos": "Equipamiento productivo",
    "financiamiento": "Capital de trabajo",
    "dinero": "Capital de trabajo",
    "capital": "Capital de trabajo",
    "insumos": "Insumos productivos",
    "transporte": "Transporte de apoyo",
    "espacio": "Espacio comercial temporal",
    "servicios básicos": "Servicios básicos",
}


def _municipio_mayor_demanda(por_municipio: dict[str, int]) -> tuple[str, int]:
    if not por_municipio:
        return "Cali", 0
    nombre = max(por_municipio, key=por_municipio.get)
    return nombre, por_municipio[nombre]


def resumir_brechas(brechas: list[dict]) -> dict:
    con_deficit = [b for b in brechas if b.get("brecha", 0) > 0]
    cubiertas = [b for b in brechas if b.get("brecha", 0) <= 0 and b.get("solicitudes", 0) > 0]
    deficit_total = sum(b.get("brecha", 0) for b in con_deficit)

    if not brechas:
        mensaje = "Aún no hay solicitudes registradas para calcular brechas."
    elif not con_deficit:
        mensaje = "Todas las necesidades reportadas tienen cupos demostrativos suficientes."
    else:
        mensaje = (
            f"{len(con_deficit)} de {len(brechas)} necesidades tienen menos cupos que solicitudes. "
            f"Faltan al menos {deficit_total} cupos en total (datos demo)."
        )

    return {
        "necesidades_analizadas": len(brechas),
        "con_deficit": len(con_deficit),
        "cubiertas": len(cubiertas),
        "deficit_total_cupos": deficit_total,
        "mensaje": mensaje,
    }


def generar_prioridades_entidad(
    brechas: list[dict],
    por_municipio: dict[str, int],
    por_ruta: dict[str, int] | None = None,
) -> dict:
    municipio_foco, casos_foco = _municipio_mayor_demanda(por_municipio)
    zona_foco = obtener_zona_municipio(municipio_foco)

    prioridades = []
    for i, brecha in enumerate([b for b in brechas if b.get("brecha", 0) > 0][:5], start=1):
        programa = brecha.get("programa", brecha.get("necesidad", ""))
        faltan = brecha["brecha"]
        prioridades.append({
            "orden": i,
            "necesidad": brecha["necesidad"],
            "programa": programa,
            "solicitudes": brecha["solicitudes"],
            "cupos_disponibles": brecha["recursos"],
            "faltan_cupos": faltan,
            "cobertura_pct": brecha.get("cobertura_pct", 0),
            "nivel": brecha.get("nivel", "amarillo"),
            "accion_sugerida": (
                f"Movilizar {faltan} cupo(s) adicionales de «{programa}» "
                f"en {municipio_foco} (zona {zona_foco})."
            ),
            "justificacion": brecha.get(
                "explicacion",
                f"{brecha['solicitudes']} solicitudes vs {brecha['recursos']} cupos demo.",
            ),
        })

    rutas = por_ruta or {}
    contexto_rutas = []
    if rutas:
        for nombre, total in sorted(rutas.items(), key=lambda x: x[1], reverse=True):
            contexto_rutas.append({"ruta": nombre, "casos": total})

    return {
        "municipio_foco": municipio_foco,
        "zona_sismica": zona_foco,
        "casos_en_foco": casos_foco,
        "prioridades": prioridades,
        "rutas_activas": contexto_rutas[:3],
        "mensaje_general": (
            f"Concentra recursos en {municipio_foco} ({casos_foco} casos). "
            + (
                f"Atiende primero: {prioridades[0]['programa']}."
                if prioridades
                else "No hay déficit de cupos en este momento."
            )
        ),
        "disclaimer": "Recomendaciones basadas en solicitudes registradas y catálogo demostrativo.",
    }
