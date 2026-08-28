"""
Cálculo de prioridad, confianza y niveles de semáforo para pasaportes y dashboard.
"""

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
)

NIVELES = ("verde", "amarillo", "rojo")


def _nivel_brecha(brecha: int, solicitudes: int) -> str:
    if brecha <= 0:
        return "verde"
    ratio = brecha / max(solicitudes, 1)
    if ratio >= 0.5 or brecha >= 10:
        return "rojo"
    if ratio >= 0.2 or brecha >= 3:
        return "amarillo"
    return "verde"


def calcular_prioridad(datos) -> tuple[str, str]:
    """Retorna (nivel semáforo, etiqueta legible)."""
    if isinstance(datos, DiagnosticoAyudaInmediata):
        urgencia = datos.urgencia.lower()
        if urgencia == "alta":
            return "rojo", "Alta"
        if urgencia == "media":
            return "amarillo", "Media"
        return "verde", "Baja"

    if isinstance(datos, DiagnosticoVivienda):
        hab = datos.habitabilidad.lower()
        if "no" in hab:
            return "rojo", "Alta"
        if "parcial" in hab:
            return "amarillo", "Media"
        return "verde", "Baja"

    if isinstance(datos, DiagnosticoIngresos):
        if not datos.puede_operar:
            return "rojo", "Alta"
        if any(n.lower() in ("dinero", "financiamiento", "capital") for n in datos.necesidades):
            return "amarillo", "Media"
        return "verde", "Baja"

    return "amarillo", "Media"


def calcular_confianza(datos) -> tuple[str, str]:
    """Índice de confianza del reporte (sin ML, reglas transparentes)."""
    puntos = 0
    max_puntos = 4

    if isinstance(datos, DiagnosticoAyudaInmediata):
        if datos.municipio.strip():
            puntos += 1
        if datos.personas_hogar and datos.personas_hogar > 0:
            puntos += 1
        if datos.necesidad.strip():
            puntos += 1
        if datos.evidencia.strip():
            puntos += 1
    elif isinstance(datos, DiagnosticoVivienda):
        if datos.municipio.strip():
            puntos += 1
        if datos.tipo_afectacion:
            puntos += 1
        if datos.habitabilidad.strip():
            puntos += 1
        if datos.evidencia.strip():
            puntos += 1
    elif isinstance(datos, DiagnosticoIngresos):
        if datos.municipio.strip():
            puntos += 1
        if datos.actividad_economica.strip():
            puntos += 1
        if datos.danos:
            puntos += 1
        if datos.necesidades:
            puntos += 1

    ratio = puntos / max_puntos
    if ratio >= 0.75:
        return "verde", "Alta confianza"
    if ratio >= 0.5:
        return "amarillo", "Requiere validación"
    return "rojo", "Evidencia parcial"


def semaforo_municipio(total_casos: int, max_municipio: int) -> str:
    if max_municipio <= 0:
        return "verde"
    ratio = total_casos / max_municipio
    if ratio >= 0.6:
        return "rojo"
    if ratio >= 0.35:
        return "amarillo"
    return "verde"


def enriquecer_brechas(brechas: list[dict]) -> list[dict]:
    for item in brechas:
        item["nivel"] = _nivel_brecha(item["brecha"], item["solicitudes"])
    return brechas


def detectar_tendencia_emergente(pasaportes: list[dict]) -> dict | None:
    """Detecta concentración de una necesidad en un municipio (v1 reglas)."""
    if len(pasaportes) < 5:
        return None

    conteo: dict[str, dict[str, int]] = {}
    total_por_necesidad: dict[str, int] = {}

    for p in pasaportes:
        municipio = p["municipio"]
        for nec in p["necesidades"]:
            clave = nec.lower()
            total_por_necesidad[clave] = total_por_necesidad.get(clave, 0) + 1
            if municipio not in conteo:
                conteo[municipio] = {}
            conteo[municipio][clave] = conteo[municipio].get(clave, 0) + 1

    mejor = None
    for municipio, necesidades in conteo.items():
        for nec, cantidad in necesidades.items():
            total = total_por_necesidad.get(nec, 1)
            pct = int(cantidad / total * 100)
            if cantidad >= 3 and pct >= 25:
                if mejor is None or pct > mejor["porcentaje"]:
                    mejor = {
                        "municipio": municipio,
                        "necesidad": nec,
                        "casos": cantidad,
                        "porcentaje": pct,
                        "nivel": "rojo" if pct >= 40 else "amarillo",
                    }
    return mejor
