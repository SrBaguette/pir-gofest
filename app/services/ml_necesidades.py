"""
ML 1 — Detector de necesidades emergentes (v1 estadístico).

Compara ventanas temporales y concentración geográfica para alertar
cuando una necesidad crece en una zona específica.
"""

from datetime import datetime, timezone

_historial: list[dict] = []
MAX_SNAPSHOTS = 30


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conteo_necesidad_por_municipio(pasaportes: list[dict]) -> dict[str, dict[str, int]]:
    resultado: dict[str, dict[str, int]] = {}
    for p in pasaportes:
        municipio = p["municipio"]
        if municipio not in resultado:
            resultado[municipio] = {}
        for nec in p["necesidades"]:
            clave = nec.lower().strip()
            resultado[municipio][clave] = resultado[municipio].get(clave, 0) + 1
    return resultado


def _conteo_necesidad_global(pasaportes: list[dict]) -> dict[str, int]:
    total: dict[str, int] = {}
    for p in pasaportes:
        for nec in p["necesidades"]:
            clave = nec.lower().strip()
            total[clave] = total.get(clave, 0) + 1
    return total


def registrar_snapshot(pasaportes: list[dict]) -> None:
    global _historial
    snapshot = {
        "timestamp": _ahora_iso(),
        "total_casos": len(pasaportes),
        "por_necesidad": _conteo_necesidad_global(pasaportes),
        "por_municipio_necesidad": _conteo_necesidad_por_municipio(pasaportes),
    }
    _historial.append(snapshot)
    if len(_historial) > MAX_SNAPSHOTS:
        _historial = _historial[-MAX_SNAPSHOTS:]


def registrar_snapshot_demo_previo(pasaportes: list[dict]) -> None:
    """Crea un snapshot simulado anterior para demostrar crecimiento temporal en demos."""
    global _historial
    actual_global = _conteo_necesidad_global(pasaportes)
    actual_geo = _conteo_necesidad_por_municipio(pasaportes)
    prev_global = {k: max(0, int(v * 0.55)) for k, v in actual_global.items()}
    prev_geo: dict[str, dict[str, int]] = {}
    for municipio, necesidades in actual_geo.items():
        prev_geo[municipio] = {k: max(0, int(v * 0.55)) for k, v in necesidades.items()}
    _historial.append({
        "timestamp": _ahora_iso(),
        "total_casos": int(len(pasaportes) * 0.55),
        "por_necesidad": prev_global,
        "por_municipio_necesidad": prev_geo,
        "demo": True,
    })


def limpiar_historial() -> None:
    global _historial
    _historial = []


def _variacion_porcentual(actual: int, anterior: int) -> int | None:
    if anterior <= 0:
        return None if actual <= 0 else 100
    return int((actual - anterior) / anterior * 100)


def detectar_necesidades_emergentes(pasaportes: list[dict]) -> list[dict]:
    """
    Retorna lista de alertas ML1 ordenadas por severidad.
    Combina crecimiento temporal + concentración geográfica.
    """
    if len(pasaportes) < 3:
        return []

    actual_global = _conteo_necesidad_global(pasaportes)
    actual_geo = _conteo_necesidad_por_municipio(pasaportes)
    alertas: list[dict] = []

    if len(_historial) >= 2:
        anterior = _historial[-2]
        prev_global = anterior.get("por_necesidad", {})
        for necesidad, cantidad in actual_global.items():
            prev = prev_global.get(necesidad, 0)
            variacion = _variacion_porcentual(cantidad, prev)
            if variacion is not None and variacion >= 20 and cantidad >= 3:
                nivel = "rojo" if variacion >= 35 else "amarillo"
                alertas.append({
                    "tipo": "crecimiento_temporal",
                    "necesidad": necesidad,
                    "variacion_pct": variacion,
                    "casos_actuales": cantidad,
                    "casos_anteriores": prev,
                    "nivel": nivel,
                    "mensaje": (
                        f"En las últimas consultas aumentaron {variacion}% los reportes "
                        f"relacionados con {necesidad} ({prev} → {cantidad})."
                    ),
                    "accion_recomendada": (
                        f"Revisar disponibilidad de programas para {necesidad} en la región."
                    ),
                })

    for municipio, necesidades in actual_geo.items():
        for necesidad, cantidad in necesidades.items():
            total_nec = actual_global.get(necesidad, 1)
            pct_zona = int(cantidad / total_nec * 100)
            if cantidad >= 3 and pct_zona >= 25:
                nivel = "rojo" if pct_zona >= 40 else "amarillo"
                alertas.append({
                    "tipo": "concentracion_geografica",
                    "municipio": municipio,
                    "necesidad": necesidad,
                    "casos": cantidad,
                    "porcentaje_zona": pct_zona,
                    "nivel": nivel,
                    "mensaje": (
                        f"Concentración en {municipio}: {cantidad} casos de {necesidad} "
                        f"({pct_zona}% del total reportado)."
                    ),
                    "accion_recomendada": (
                        f"Priorizar despliegue de recursos de {necesidad} en {municipio}."
                    ),
                })

    orden = {"rojo": 0, "amarillo": 1, "verde": 2}
    alertas.sort(key=lambda a: (orden.get(a["nivel"], 9), -a.get("variacion_pct", a.get("porcentaje_zona", 0))))
    return alertas[:8]
