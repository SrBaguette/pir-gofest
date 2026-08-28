"""
Simulador de escenarios WOW (intru2 §14):
cruza recursos disponibles + necesidades + ubicación + prioridad.
"""

from app.services.catalogo_recursos import obtener_zona_municipio


def _contar_por_tipo(pasaportes: list[dict]) -> dict:
    ayuda = vivienda = ingresos = 0
    urgentes = 0
    no_habitable = 0
    no_operativos = 0
    empleos_estimados = 0

    for p in pasaportes:
        tipo = p.get("tipo_ruta", "")
        if tipo == "ayuda_inmediata":
            ayuda += 1
            if p.get("urgencia", "").lower() == "alta":
                urgentes += 1
        elif tipo == "vivienda":
            vivienda += 1
            prio = (p.get("prioridad_etiqueta") or "").lower()
            if "alta" in prio:
                no_habitable += 1
        elif tipo == "ingresos":
            ingresos += 1
            if not p.get("puede_operar", True):
                no_operativos += 1
            empleos_estimados += max(1, p.get("num_empleados", 0) or 1)

    return {
        "ayuda_inmediata": ayuda,
        "vivienda": vivienda,
        "ingresos": ingresos,
        "urgentes": urgentes,
        "vivienda_prioridad_alta": no_habitable,
        "no_operativos": no_operativos,
        "empleos_vinculados": empleos_estimados,
        "total": len(pasaportes),
    }


def _municipio_mayor_demanda(pasaportes: list[dict]) -> str:
    conteo: dict[str, int] = {}
    for p in pasaportes:
        m = p.get("municipio", "—")
        conteo[m] = conteo.get(m, 0) + 1
    if not conteo:
        return "Cali"
    return max(conteo, key=conteo.get)


def simular_escenarios(
    pasaportes: list[dict],
    brechas: list[dict],
    presupuesto_millones: float = 500,
    kits_emergencia: int = 500,
    tecnicos: int = 30,
) -> dict:
    """
    Lógica transparente (no IA):
    - Escenario A: kits + presupuesto orientado a ayuda inmediata / familias vulnerables
    - Escenario B: técnicos × capacidad mensual de visitas de vivienda
    - Escenario C: presupuesto productivo / cupos financiamiento para reactivación
    """
    stats = _contar_por_tipo(pasaportes)
    municipio_foco = _municipio_mayor_demanda(pasaportes)
    zona_foco = obtener_zona_municipio(municipio_foco)

    # Costos unitarios demostrativos (millones COP)
    costo_kit_familia = 0.8  # millones por kit completo familiar
    costo_vivienda_basica = 3.5  # millones por intervención básica
    costo_reactivacion_negocio = 7.0  # millones por negocio

    familias_por_kits = min(stats["urgentes"] or stats["ayuda_inmediata"], kits_emergencia)
    familias_por_presupuesto = int((presupuesto_millones * 0.6) / costo_kit_familia)
    impacto_a_personas = min(
        stats["ayuda_inmediata"] + stats["vivienda_prioridad_alta"],
        familias_por_kits + familias_por_presupuesto,
    )

    capacidad_tecnico_mes = 7  # viviendas evaluadas/reparadas por técnico al mes
    viviendas_posibles = min(stats["vivienda"], tecnicos * capacidad_tecnico_mes)
    presupuesto_vivienda = int((presupuesto_millones * 0.25) / costo_vivienda_basica)
    impacto_b_viviendas = min(stats["vivienda"], viviendas_posibles + presupuesto_vivienda)

    negocios_por_presupuesto = int((presupuesto_millones * 0.35) / costo_reactivacion_negocio)
    kits_productivos = int(kits_emergencia * 0.15)
    impacto_c_negocios = min(stats["no_operativos"] or stats["ingresos"], negocios_por_presupuesto + kits_productivos)
    empleos_recuperables = min(stats["empleos_vinculados"], impacto_c_negocios * 2)

    brecha_top = brechas[0] if brechas else None

    escenarios = [
        {
            "id": "A",
            "titulo": "Priorizar familias vulnerables",
            "descripcion": "Orienta kits de emergencia y presupuesto (60%) a ayuda inmediata y hogares en riesgo.",
            "impacto_principal": f"{impacto_a_personas} personas atendidas",
            "impacto_detalle": (
                f"Cubre hasta {familias_por_kits} familias con kits y "
                f"{familias_por_presupuesto} con subsidio demostrativo."
            ),
            "zona_sugerida": zona_foco,
            "municipio_foco": municipio_foco,
            "criterio": "Urgencia + ayuda inmediata registrada",
        },
        {
            "id": "B",
            "titulo": "Priorizar reparación básica de vivienda",
            "descripcion": f"Usa {tecnicos} técnicos ({capacidad_tecnico_mes} viviendas/mes c/u) + 25% del presupuesto.",
            "impacto_principal": f"{impacto_b_viviendas} viviendas intervenidas",
            "impacto_detalle": f"De {stats['vivienda']} casos de vivienda registrados en el sistema.",
            "zona_sugerida": zona_foco,
            "municipio_foco": municipio_foco,
            "criterio": "Casos de ruta vivienda + prioridad estructural",
        },
        {
            "id": "C",
            "titulo": "Priorizar recuperación productiva",
            "descripcion": "35% del presupuesto a capital de trabajo + kits productivos (15% de kits totales).",
            "impacto_principal": f"{impacto_c_negocios} negocios reactivados",
            "impacto_detalle": f"Hasta {empleos_recuperables} empleos potencialmente recuperados.",
            "zona_sugerida": zona_foco,
            "municipio_foco": municipio_foco,
            "criterio": "Negocios no operativos + necesidad de financiamiento",
        },
    ]

    # Recomendación según brecha dominante
    recomendacion = "A"
    if brecha_top:
        nec = brecha_top.get("necesidad", "").lower()
        if any(x in nec for x in ("reparacion", "reparación", "vivienda", "evaluacion", "evaluación")):
            recomendacion = "B"
        elif any(x in nec for x in ("financiamiento", "dinero", "equipamiento", "capital", "insumos")):
            recomendacion = "C"

    return {
        "entrada": {
            "presupuesto_millones": presupuesto_millones,
            "kits_emergencia": kits_emergencia,
            "tecnicos": tecnicos,
        },
        "contexto": {
            "casos_registrados": stats,
            "municipio_mayor_demanda": municipio_foco,
            "zona_sismica_foco": zona_foco,
            "brecha_principal": brecha_top,
        },
        "escenarios": escenarios,
        "recomendacion": recomendacion,
        "disclaimer": "Escenarios calculados con reglas transparentes. La entidad decide la asignación final.",
    }
