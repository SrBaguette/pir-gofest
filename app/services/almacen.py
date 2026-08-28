"""
Almacenamiento temporal en memoria para Pasaportes de Recuperación.
"""

import json

from fastapi import HTTPException
from sqlalchemy import text

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
)
from app.services.semaforo import (
    calcular_confianza,
    calcular_prioridad,
    detectar_tendencia_emergente,
    enriquecer_brechas,
    semaforo_municipio,
)
from app.services.ml_necesidades import (
    detectar_necesidades_emergentes,
    limpiar_historial,
    registrar_snapshot,
)
from app.services.ml_mapa import generar_mapa_inteligente
from app.services.base_datos import engine, inicializar_base_datos, usar_cloud_sql

_pasaportes: dict[str, dict] = {}
_contador = 0
_resumen_anterior: dict | None = None

inicializar_base_datos()


def _calcular_progreso(pasaporte: dict) -> int:
    total = len(pasaporte["ruta"])
    if total == 0:
        return 0
    completadas = len(pasaporte["acciones_completadas"])
    return int(completadas / total * 100)


def _actualizar_estado(pasaporte: dict) -> None:
    progreso = _calcular_progreso(pasaporte)
    pasaporte["progreso"] = progreso
    pasaporte["estado"] = "Ruta completada" if progreso == 100 else "En recuperación"


def limpiar_pasaportes() -> None:
    global _contador, _resumen_anterior
    _pasaportes.clear()
    if engine is not None:
        with engine.begin() as connection:
            connection.exec_driver_sql("DELETE FROM pasaportes")
    _contador = 0
    _resumen_anterior = None
    limpiar_historial()


def _extraer_datos_pasaporte(datos):
    if isinstance(datos, DiagnosticoAyudaInmediata):
        return {
            "tipo_ruta": "ayuda_inmediata",
            "municipio": datos.municipio,
            "ruta_nombre": "Ayuda inmediata",
            "actividad_economica": "Ayuda inmediata",
            "danos": [],
            "necesidades": [datos.necesidad.lower()],
            "puede_operar": False,
            "urgencia": datos.urgencia.lower(),
        }
    if isinstance(datos, DiagnosticoVivienda):
        habitable = (
            "no" not in datos.habitabilidad.lower()
            and "parcial" not in datos.habitabilidad.lower()
        )
        return {
            "tipo_ruta": "vivienda",
            "municipio": datos.municipio,
            "ruta_nombre": "Recuperar vivienda",
            "actividad_economica": "Vivienda",
            "danos": [item.lower() for item in datos.tipo_afectacion],
            "necesidades": ["reparacion", "vivienda"],
            "puede_operar": habitable,
        }
    return {
        "tipo_ruta": "ingresos",
        "municipio": datos.municipio,
        "ruta_nombre": "Recuperar ingresos",
        "actividad_economica": datos.actividad_economica,
        "danos": list(datos.danos),
        "necesidades": list(datos.necesidades),
        "puede_operar": datos.puede_operar,
    }


def _pasaporte_publico(pasaporte: dict) -> dict:
    return {
        "id": pasaporte["id"],
        "tipo_ruta": pasaporte["tipo_ruta"],
        "ruta_nombre": pasaporte["ruta_nombre"],
        "municipio": pasaporte["municipio"],
        "actividad_economica": pasaporte["actividad_economica"],
        "danos": pasaporte["danos"],
        "necesidades": pasaporte["necesidades"],
        "puede_operar": pasaporte["puede_operar"],
        "que_hacer_primero": pasaporte["que_hacer_primero"],
        "ruta": pasaporte["ruta"],
        "progreso": pasaporte["progreso"],
        "estado": pasaporte["estado"],
        "acciones_completadas": sorted(pasaporte["acciones_completadas"]),
        "ayudas": pasaporte.get("ayudas", []),
        "prioridad_nivel": pasaporte.get("prioridad_nivel", "amarillo"),
        "prioridad_etiqueta": pasaporte.get("prioridad_etiqueta", "Media"),
        "confianza_nivel": pasaporte.get("confianza_nivel", "amarillo"),
        "confianza_etiqueta": pasaporte.get("confianza_etiqueta", "Requiere validación"),
        "urgencia": pasaporte.get("urgencia"),
    }


def crear_pasaporte(datos, resultado: dict) -> dict:
    global _contador
    if engine is not None:
        with engine.connect() as connection:
            ultimo_id = connection.execute(text("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(id FROM 5) AS INTEGER)), 0)
                FROM pasaportes
            """)).scalar_one()
        _contador = max(_contador, ultimo_id)
    _contador += 1
    pasaporte_id = f"PAS-{str(_contador).zfill(4)}"
    base = _extraer_datos_pasaporte(datos)
    prioridad_nivel, prioridad_etiqueta = calcular_prioridad(datos)
    confianza_nivel, confianza_etiqueta = calcular_confianza(datos)

    pasaporte = {
        "id": pasaporte_id,
        **base,
        "que_hacer_primero": resultado["que_hacer_primero"],
        "ruta": list(resultado["ruta"]),
        "progreso": 0,
        "estado": "En recuperación",
        "acciones_completadas": set(),
        "ayudas": list(resultado.get("ayudas", [])),
        "prioridad_nivel": prioridad_nivel,
        "prioridad_etiqueta": prioridad_etiqueta,
        "confianza_nivel": confianza_nivel,
        "confianza_etiqueta": confianza_etiqueta,
    }

    if engine is not None:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO pasaportes (
                        id, tipo_ruta, ruta_nombre, municipio, personas_hogar,
                        actividad_economica, danos, necesidades, puede_operar,
                        urgencia, que_hacer_primero, ruta, ayudas,
                        prioridad_nivel, prioridad_etiqueta, confianza_nivel,
                        confianza_etiqueta
                    ) VALUES (
                        :id, :tipo_ruta, :ruta_nombre, :municipio, :personas_hogar,
                        :actividad_economica, CAST(:danos AS jsonb), CAST(:necesidades AS jsonb),
                        :puede_operar, :urgencia, :que_hacer_primero, CAST(:ruta AS jsonb),
                        CAST(:ayudas AS jsonb), :prioridad_nivel, :prioridad_etiqueta,
                        :confianza_nivel, :confianza_etiqueta
                    )
                """),
                {**pasaporte,
                 "personas_hogar": getattr(datos, "personas_hogar", None),
                 "urgencia": pasaporte.get("urgencia"),
                 "danos": json.dumps(pasaporte["danos"]),
                 "necesidades": json.dumps(pasaporte["necesidades"]),
                 "ruta": json.dumps(pasaporte["ruta"]),
                 "ayudas": json.dumps(pasaporte["ayudas"])},
            )
            connection.execute(
                text("""
                    INSERT INTO acciones_ruta (pasaporte_id, numero, descripcion)
                    SELECT :id, numero, descripcion
                    FROM jsonb_to_recordset(CAST(:acciones AS jsonb))
                        AS acciones(numero INTEGER, descripcion TEXT)
                    ON CONFLICT (pasaporte_id, numero) DO NOTHING
                """),
                {
                    "id": pasaporte_id,
                    "acciones": json.dumps([
                        {"numero": numero, "descripcion": descripcion}
                        for numero, descripcion in enumerate(pasaporte["ruta"])
                    ]),
                },
            )
    else:
        _pasaportes[pasaporte_id] = pasaporte
    return _pasaporte_publico(pasaporte)


def listar_pasaportes() -> list[dict]:
    if engine is not None:
        with engine.connect() as connection:
            rows = connection.execute(text("SELECT * FROM pasaportes ORDER BY creado_en")).mappings()
            return [_fila_a_pasaporte(row, connection) for row in rows]
    return list(_pasaportes.values())


def _fila_a_pasaporte(row, connection) -> dict:
    pasaporte = dict(row)
    completadas = connection.execute(
        text("SELECT numero FROM acciones_ruta WHERE pasaporte_id = :id AND completada"),
        {"id": pasaporte["id"]},
    ).scalars()
    pasaporte["acciones_completadas"] = set(completadas)
    return pasaporte


def obtener_pasaporte(pasaporte_id: str) -> dict:
    if engine is not None:
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM pasaportes WHERE id = :id"), {"id": pasaporte_id}
            ).mappings().first()
            pasaporte = _fila_a_pasaporte(row, connection) if row else None
    else:
        pasaporte = _pasaportes.get(pasaporte_id)
    if pasaporte is None:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado")
    return _pasaporte_publico(pasaporte)


def marcar_accion_completada(pasaporte_id: str, numero: int) -> dict:
    if engine is not None:
        with engine.begin() as connection:
            row = connection.execute(
                text("SELECT ruta FROM pasaportes WHERE id = :id"), {"id": pasaporte_id}
            ).mappings().first()
            if row is None:
                raise HTTPException(status_code=404, detail="Pasaporte no encontrado")
            if numero < 0 or numero >= len(row["ruta"]):
                raise HTTPException(status_code=400, detail="Número de acción inválido")
            connection.execute(text("""
                UPDATE acciones_ruta
                SET completada = TRUE, completada_en = CURRENT_TIMESTAMP
                WHERE pasaporte_id = :id AND numero = :numero
            """), {"id": pasaporte_id, "numero": numero})
            completadas = connection.execute(text("""
                SELECT COUNT(*) FROM acciones_ruta
                WHERE pasaporte_id = :id AND completada
            """), {"id": pasaporte_id}).scalar_one()
            progreso = int(completadas / len(row["ruta"]) * 100) if row["ruta"] else 0
            connection.execute(text("""
                UPDATE pasaportes
                SET progreso = :progreso,
                    estado = CASE WHEN :progreso = 100 THEN 'Ruta completada' ELSE 'En recuperación' END,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {"id": pasaporte_id, "progreso": progreso})
        return obtener_pasaporte(pasaporte_id)

    pasaporte = _pasaportes.get(pasaporte_id)
    if pasaporte is None:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado")

    total = len(pasaporte["ruta"])
    if numero < 0 or numero >= total:
        raise HTTPException(status_code=400, detail="Número de acción inválido")

    pasaporte["acciones_completadas"].add(numero)
    _actualizar_estado(pasaporte)
    return _pasaporte_publico(pasaporte)


def _contar_items(listas: list[list[str]]) -> dict[str, int]:
    conteo: dict[str, int] = {}
    for items in listas:
        for item in items:
            clave = item.lower().strip()
            conteo[clave] = conteo.get(clave, 0) + 1
    return conteo


def _contar_campo(pasaportes: list[dict], campo: str) -> dict[str, int]:
    conteo: dict[str, int] = {}
    for pasaporte in pasaportes:
        valor = pasaporte[campo]
        conteo[valor] = conteo.get(valor, 0) + 1
    return conteo


MAPEO_NECESIDAD_RECURSO = {
    "equipamiento": "equipamiento",
    "equipos": "equipamiento",
    "dinero": "financiamiento",
    "financiamiento": "financiamiento",
    "capital": "financiamiento",
    "reparacion": "reparación",
    "reparación": "reparación",
    "vivienda": "reparación",
    "alojamiento": "alojamiento",
    "alimentacion": "alimentación",
    "alimentación": "alimentación",
    "agua": "agua",
    "medicamentos": "salud",
    "salud": "salud",
    "insumos": "insumos",
    "transporte": "transporte",
    "espacio": "espacio",
}


def _contar_recursos_por_categoria(recursos: list[dict]) -> dict[str, int]:
    conteo: dict[str, int] = {}
    for recurso in recursos:
        clave = recurso["categoria"].lower()
        conteo[clave] = conteo.get(clave, 0) + 1
    return conteo


def _calcular_brechas_detalladas(
    por_necesidad: dict[str, int],
    recursos_disponibles: list[dict],
) -> list[dict]:
    recursos_por_categoria = _contar_recursos_por_categoria(recursos_disponibles)
    brechas = []

    for necesidad, solicitudes in sorted(
        por_necesidad.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        categoria = MAPEO_NECESIDAD_RECURSO.get(necesidad.lower(), necesidad.lower())
        recursos = recursos_por_categoria.get(categoria, 0)
        brechas.append({
            "necesidad": necesidad,
            "solicitudes": solicitudes,
            "recursos": recursos,
            "brecha": max(0, solicitudes - recursos),
        })

    return brechas


def _generar_alertas(resumen: dict, tendencias: dict) -> list[dict]:
    alertas = []

    if resumen["total_afectados"] == 0:
        return [{
            "nivel": "info",
            "mensaje": "Aún no hay diagnósticos registrados en el sistema.",
        }]

    nuevos = tendencias.get("total_afectados", 0)
    if nuevos > 0:
        alertas.append({
            "nivel": "alta",
            "mensaje": f"Se registraron {nuevos} nuevo(s) caso(s) desde la última consulta.",
        })

    nuevos_no_operativos = tendencias.get("total_no_operativos", 0)
    if nuevos_no_operativos > 0:
        alertas.append({
            "nivel": "alta",
            "mensaje": f"Aumento de {nuevos_no_operativos} negocio(s) o actividad(es) no operativa(s).",
        })

    por_municipio = resumen.get("por_municipio", {})
    if por_municipio:
        municipio_top = max(por_municipio, key=por_municipio.get)
        total_top = por_municipio[municipio_top]
        if total_top >= 2:
            alertas.append({
                "nivel": "media",
                "mensaje": f"Concentración de afectados en {municipio_top} ({total_top} casos).",
            })

    por_necesidad = resumen.get("por_necesidad", {})
    if por_necesidad:
        necesidad_top = max(por_necesidad, key=por_necesidad.get)
        alertas.append({
            "nivel": "media",
            "mensaje": f"Necesidad principal: {necesidad_top} ({por_necesidad[necesidad_top]} solicitudes).",
        })

    brechas_altas = [
        item for item in resumen.get("brechas", [])
        if item.get("brecha", 0) > 0
    ]
    if brechas_altas:
        mayor = brechas_altas[0]
        nivel = mayor.get("nivel", "rojo")
        alertas.append({
            "nivel": "alta" if nivel == "rojo" else "media",
            "mensaje": (
                f"Brecha detectada en {mayor['necesidad']}: "
                f"{mayor['solicitudes']} solicitudes vs {mayor['recursos']} recursos demo."
            ),
        })

    tendencia = resumen.get("tendencia_emergente")
    if tendencia:
        alertas.insert(0, {
            "nivel": "alta" if tendencia["nivel"] == "rojo" else "media",
            "mensaje": (
                f"Tendencia emergente: {tendencia['porcentaje']}% de reportes de "
                f"{tendencia['necesidad']} concentrados en {tendencia['municipio']} "
                f"({tendencia['casos']} casos)."
            ),
        })

    for ml1 in resumen.get("ml_necesidades_emergentes", [])[:3]:
        alertas.insert(0, {
            "nivel": "alta" if ml1["nivel"] == "rojo" else "media",
            "mensaje": ml1["mensaje"],
            "accion_recomendada": ml1.get("accion_recomendada"),
        })

    if not alertas:
        alertas.append({
            "nivel": "info",
            "mensaje": "Sin cambios significativos desde la última consulta.",
        })

    return alertas


def obtener_resumen_dashboard(recursos_disponibles: list[dict]) -> dict:
    global _resumen_anterior

    lista = listar_pasaportes() if usar_cloud_sql() else list(_pasaportes.values())
    total = len(lista)
    no_operativos = sum(1 for p in lista if not p["puede_operar"])
    operativos = total - no_operativos
    completadas = sum(1 for p in lista if p["progreso"] == 100)
    progreso_promedio = (
        int(sum(p["progreso"] for p in lista) / total) if total > 0 else 0
    )

    por_necesidad = _contar_items([p["necesidades"] for p in lista])
    por_tipo_de_dano = _contar_items([p["danos"] for p in lista])
    brechas = enriquecer_brechas(
        _calcular_brechas_detalladas(por_necesidad, recursos_disponibles)
    )

    por_municipio = _contar_campo(lista, "municipio")
    max_municipio = max(por_municipio.values()) if por_municipio else 0
    municipios_detalle = [
        {
            "nombre": nombre,
            "total": total,
            "nivel": semaforo_municipio(total, max_municipio),
        }
        for nombre, total in sorted(por_municipio.items(), key=lambda x: x[1], reverse=True)
    ]

    por_prioridad = _contar_campo(lista, "prioridad_etiqueta")
    tendencia_emergente = detectar_tendencia_emergente(lista)
    registrar_snapshot(lista)
    ml_necesidades_emergentes = detectar_necesidades_emergentes(lista)
    mapa_inteligente = generar_mapa_inteligente(lista)

    resumen = {
        "total_afectados": total,
        "total_no_operativos": no_operativos,
        "total_operativos": operativos,
        "total_rutas_completadas": completadas,
        "progreso_promedio": progreso_promedio,
        "por_municipio": por_municipio,
        "municipios_detalle": municipios_detalle,
        "por_actividad": _contar_campo(lista, "actividad_economica"),
        "por_ruta": _contar_campo(lista, "ruta_nombre"),
        "por_necesidad": por_necesidad,
        "por_prioridad": por_prioridad,
        "por_tipo_de_dano": por_tipo_de_dano,
        "brechas": brechas,
        "tendencia_emergente": tendencia_emergente,
        "ml_necesidades_emergentes": ml_necesidades_emergentes,
        "mapa_inteligente": mapa_inteligente,
        "recursos_disponibles": recursos_disponibles,
    }

    if _resumen_anterior is None:
        tendencias = {
            "total_afectados": 0,
            "total_no_operativos": 0,
            "total_operativos": 0,
            "total_rutas_completadas": 0,
            "progreso_promedio": 0,
        }
    else:
        tendencias = {
            "total_afectados": resumen["total_afectados"] - _resumen_anterior["total_afectados"],
            "total_no_operativos": resumen["total_no_operativos"] - _resumen_anterior["total_no_operativos"],
            "total_operativos": resumen["total_operativos"] - _resumen_anterior["total_operativos"],
            "total_rutas_completadas": resumen["total_rutas_completadas"] - _resumen_anterior["total_rutas_completadas"],
            "progreso_promedio": resumen["progreso_promedio"] - _resumen_anterior["progreso_promedio"],
        }

    _resumen_anterior = {
        key: resumen[key]
        for key in (
            "total_afectados",
            "total_no_operativos",
            "total_operativos",
            "total_rutas_completadas",
            "progreso_promedio",
        )
    }

    resumen["tendencias"] = tendencias
    resumen["alertas"] = _generar_alertas(resumen, tendencias)
    return resumen
