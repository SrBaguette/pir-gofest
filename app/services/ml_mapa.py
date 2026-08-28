"""
ML 2 — Mapa inteligente de afectación (v1 clusters + semáforo por zona sísmica).

Agrupa casos por municipio y zona (Valle Sur / Valle Norte / Cauca) para
identificar hotspots en OpenStreetMap/Leaflet.
"""

from app.services.catalogo_recursos import ZONAS_SISMICAS, obtener_zona_municipio

COORDENADAS_MUNICIPIOS: dict[str, tuple[float, float]] = {
    "popayán": (2.4448, -76.6147),
    "popayan": (2.4448, -76.6147),
    "quibdó": (5.6947, -76.6611),
    "quibdo": (5.6947, -76.6611),
    "santander de quilichao": (3.0094, -76.4842),
    "puerto tejada": (3.2331, -76.4167),
    "cali": (3.4516, -76.5320),
    "buga": (3.9004, -76.2975),
    "palmira": (3.5394, -76.3036),
    "tuluá": (4.0847, -76.1954),
    "tulua": (4.0847, -76.1954),
    "jamundí": (3.2607, -76.5447),
    "jamundi": (3.2607, -76.5447),
    "yumbo": (3.5825, -76.4956),
    "cartago": (4.7464, -75.9117),
    "florida": (3.3275, -76.2342),
}

CENTRO_VALLE = {"lat": 3.45, "lng": -76.53}

# Centro aproximado por zona (para etiquetas en mapa)
CENTROS_ZONA: dict[str, dict] = {
    "Valle Sur": {"lat": 3.42, "lng": -76.50, "zoom_hint": 9},
    "Valle Norte": {"lat": 4.05, "lng": -76.05, "zoom_hint": 9},
    "Cauca": {"lat": 3.15, "lng": -76.55, "zoom_hint": 8},
}

# Prioridad fija por zona sísmica en contexto demo
NIVEL_ZONA_BASE = {
    "Valle Sur": "rojo",
    "Valle Norte": "amarillo",
    "Cauca": "verde",
}


def _coords(municipio: str) -> tuple[float, float]:
    clave = municipio.lower().strip()
    return COORDENADAS_MUNICIPIOS.get(
        clave,
        (CENTRO_VALLE["lat"], CENTRO_VALLE["lng"]),
    )


def _nivel_cluster(total: int, max_total: int) -> str:
    if max_total <= 0:
        return "verde"
    ratio = total / max_total
    if ratio >= 0.55:
        return "rojo"
    if ratio >= 0.28:
        return "amarillo"
    return "verde"


def _nivel_zona(zona: str) -> str:
    """Prioridad fija por zona sísmica en el contexto demo del hackathon."""
    return NIVEL_ZONA_BASE.get(zona, "verde")


def _perfil_dominante(casos: list[dict]) -> dict:
    conteo_ruta: dict[str, int] = {}
    conteo_nec: dict[str, int] = {}
    recuperables = 0

    for caso in casos:
        ruta = caso.get("ruta_nombre", "Otro")
        conteo_ruta[ruta] = conteo_ruta.get(ruta, 0) + 1
        for nec in caso.get("necesidades", []):
            clave = nec.lower()
            conteo_nec[clave] = conteo_nec.get(clave, 0) + 1
        if caso.get("puede_operar") or caso.get("progreso", 0) > 0:
            recuperables += 1

    ruta_top = max(conteo_ruta, key=conteo_ruta.get) if conteo_ruta else "Mixto"
    nec_top = max(conteo_nec, key=conteo_nec.get) if conteo_nec else "variadas"

    return {
        "ruta_dominante": ruta_top,
        "necesidad_dominante": nec_top,
        "recuperables": recuperables,
    }


def _descripcion_cluster(municipio: str, total: int, perfil: dict, zona: str) -> str:
    ruta = perfil["ruta_dominante"]
    nec = perfil["necesidad_dominante"]
    rec = perfil["recuperables"]

    if "vivienda" in ruta.lower():
        return (
            f"[{zona}] En {municipio}: {total} hogares con afectación de vivienda "
            f"(necesidad principal: {nec})."
        )
    if "ingreso" in ruta.lower():
        return (
            f"[{zona}] {total} actividades económicas afectadas en {municipio}; "
            f"{rec} con potencial de recuperación."
        )
    return (
        f"[{zona}] {total} casos con necesidad urgente de {nec} en {municipio}."
    )


def _resumir_zonas(por_zona: dict[str, list[dict]]) -> list[dict]:
    totales = {z: len(casos) for z, casos in por_zona.items()}
    resumen = []

    for zona in ("Valle Sur", "Valle Norte", "Cauca"):
        casos = por_zona.get(zona, [])
        total = len(casos)
        nivel = _nivel_zona(zona)
        centro = CENTROS_ZONA.get(zona, CENTRO_VALLE)
        municipios_activos = len({c["municipio"] for c in casos})
        perfil = _perfil_dominante(casos) if casos else {}

        resumen.append({
            "zona": zona,
            "total": total,
            "nivel": nivel,
            "prioridad_label": (
                "Prioridad alta" if nivel == "rojo"
                else "Prioridad media" if nivel == "amarillo"
                else "Prioridad baja"
            ),
            "municipios_activos": municipios_activos,
            "lat": centro["lat"],
            "lng": centro["lng"],
            "necesidad_dominante": perfil.get("necesidad_dominante", "—"),
            "descripcion": (
                f"{total} casos en {zona} ({municipios_activos} municipios). "
                f"Necesidad dominante: {perfil.get('necesidad_dominante', '—')}."
            ),
        })

    return resumen


def generar_mapa_inteligente(pasaportes: list[dict]) -> dict:
    if not pasaportes:
        return {
            "centro": CENTRO_VALLE,
            "zoom": 8,
            "clusters": [],
            "subclusters": [],
            "zonas_resumen": [],
            "resumen": "Sin datos geográficos para mapear.",
        }

    por_municipio: dict[str, list[dict]] = {}
    por_zona: dict[str, list[dict]] = {}

    for p in pasaportes:
        municipio = p["municipio"]
        zona = obtener_zona_municipio(municipio)
        por_municipio.setdefault(municipio, []).append(p)
        por_zona.setdefault(zona, []).append(p)

    max_total = max(len(v) for v in por_municipio.values())
    clusters = []
    subclusters = []

    for municipio, casos in sorted(por_municipio.items(), key=lambda x: len(x[1]), reverse=True):
        total = len(casos)
        lat, lng = _coords(municipio)
        zona = obtener_zona_municipio(municipio)
        nivel_mun = _nivel_cluster(total, max_total)
        nivel_zona = _nivel_zona(zona)
        nivel = (
            nivel_mun
            if _prioridad_num(nivel_mun) >= _prioridad_num(nivel_zona)
            else nivel_zona
        )
        perfil = _perfil_dominante(casos)

        clusters.append({
            "municipio": municipio,
            "zona_sismica": zona,
            "lat": lat,
            "lng": lng,
            "total": total,
            "nivel": nivel,
            "etiqueta": f"{municipio} — {total} casos",
            "descripcion": _descripcion_cluster(municipio, total, perfil, zona),
            "ruta_dominante": perfil["ruta_dominante"],
            "necesidad_dominante": perfil["necesidad_dominante"],
            "recuperables": perfil["recuperables"],
        })

        por_ruta: dict[str, list[dict]] = {}
        for caso in casos:
            ruta = caso.get("tipo_ruta", "otro")
            por_ruta.setdefault(ruta, []).append(caso)

        for tipo_ruta, grupo in por_ruta.items():
            if len(grupo) < 2:
                continue
            offset = {"ayuda_inmediata": 0.04, "vivienda": -0.04, "ingresos": 0.02}.get(tipo_ruta, 0)
            sub_perfil = _perfil_dominante(grupo)
            subclusters.append({
                "municipio": municipio,
                "zona_sismica": zona,
                "tipo": tipo_ruta,
                "lat": lat + offset,
                "lng": lng + offset,
                "total": len(grupo),
                "nivel": _nivel_cluster(len(grupo), total),
                "etiqueta": f"{len(grupo)} casos similares — {sub_perfil['necesidad_dominante']}",
                "descripcion": (
                    f"Subcluster [{zona}] en {municipio}: {len(grupo)} perfiles "
                    f"de {tipo_ruta.replace('_', ' ')}."
                ),
            })

    zonas_resumen = _resumir_zonas(por_zona)
    municipio_top = clusters[0]["municipio"] if clusters else "región"
    total_hotspot = clusters[0]["total"] if clusters else 0
    zona_top = clusters[0]["zona_sismica"] if clusters else ""

    return {
        "centro": CENTRO_VALLE,
        "zoom": 8,
        "clusters": clusters,
        "subclusters": subclusters[:12],
        "zonas_resumen": zonas_resumen,
        "resumen": (
            f"Hotspot: {municipio_top} ({total_hotspot} casos, {zona_top}). "
            f"Valle Sur = prioridad alta · Valle Norte = media · Cauca = baja."
        ),
    }


def _prioridad_num(nivel: str) -> int:
    return {"rojo": 3, "amarillo": 2, "verde": 1}.get(nivel, 0)
