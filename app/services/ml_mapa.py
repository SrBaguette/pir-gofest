"""
ML 2 — Mapa inteligente de afectación (v1 clusters).

Agrupa casos por municipio y perfil dominante para identificar hotspots
de recuperación sin depender aún de Google Maps Platform.
"""

COORDENADAS_MUNICIPIOS: dict[str, tuple[float, float]] = {
    "popayán": (2.4448, -76.6147),
    "popayan": (2.4448, -76.6147),
    "pasto": (1.2136, -77.2811),
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


def _coords(municipio: str) -> tuple[float, float]:
    clave = municipio.lower().strip()
    return COORDENADAS_MUNICIPIOS.get(clave, CENTRO_VALLE)


def _nivel_cluster(total: int, max_total: int) -> str:
    if max_total <= 0:
        return "verde"
    ratio = total / max_total
    if ratio >= 0.55:
        return "rojo"
    if ratio >= 0.3:
        return "amarillo"
    return "verde"


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


def _descripcion_cluster(municipio: str, total: int, perfil: dict) -> str:
    ruta = perfil["ruta_dominante"]
    nec = perfil["necesidad_dominante"]
    rec = perfil["recuperables"]

    if "vivienda" in ruta.lower():
        return (
            f"En {municipio} hay {total} hogares con afectación predominante de vivienda "
            f"(necesidad principal: {nec})."
        )
    if "ingreso" in ruta.lower():
        return (
            f"En {municipio} se detectaron {total} actividades económicas afectadas; "
            f"{rec} con potencial de recuperación rápida."
        )
    return (
        f"En {municipio} concentración de {total} casos con necesidad urgente de {nec}."
    )


def generar_mapa_inteligente(pasaportes: list[dict]) -> dict:
    if not pasaportes:
        return {
            "centro": CENTRO_VALLE,
            "zoom": 8,
            "clusters": [],
            "subclusters": [],
            "resumen": "Sin datos geográficos para mapear.",
        }

    por_municipio: dict[str, list[dict]] = {}
    for p in pasaportes:
        municipio = p["municipio"]
        por_municipio.setdefault(municipio, []).append(p)

    max_total = max(len(v) for v in por_municipio.values())
    clusters = []
    subclusters = []

    for municipio, casos in sorted(por_municipio.items(), key=lambda x: len(x[1]), reverse=True):
        total = len(casos)
        lat, lng = _coords(municipio)
        nivel = _nivel_cluster(total, max_total)
        perfil = _perfil_dominante(casos)

        clusters.append({
            "municipio": municipio,
            "lat": lat,
            "lng": lng,
            "total": total,
            "nivel": nivel,
            "etiqueta": f"{municipio} — {total} casos",
            "descripcion": _descripcion_cluster(municipio, total, perfil),
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
                "tipo": tipo_ruta,
                "lat": lat + offset,
                "lng": lng + offset,
                "total": len(grupo),
                "nivel": _nivel_cluster(len(grupo), total),
                "etiqueta": f"{len(grupo)} casos similares — {sub_perfil['necesidad_dominante']}",
                "descripcion": (
                    f"Subcluster en {municipio}: {len(grupo)} personas con perfil "
                    f"de {tipo_ruta.replace('_', ' ')} y necesidad de {sub_perfil['necesidad_dominante']}."
                ),
            })

    municipio_top = clusters[0]["municipio"] if clusters else "región"
    total_hotspot = clusters[0]["total"] if clusters else 0

    return {
        "centro": CENTRO_VALLE,
        "zoom": 8,
        "clusters": clusters,
        "subclusters": subclusters[:12],
        "resumen": (
            f"Hotspot principal: {municipio_top} ({total_hotspot} casos). "
            f"{len(subclusters)} subclusters de perfiles similares detectados."
        ),
    }
