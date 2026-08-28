from dataclasses import dataclass

from app.services.catalogo_recursos import obtener_catalogo_completo, obtener_catalogo_publico

TERMINOS_EQUIPAMIENTO = ("maquinaria", "equipos", "herramientas")
TERMINOS_ESPACIO = ("local", "infraestructura", "vivienda", "espacio")
TERMINOS_ECONOMICO = ("dinero", "financiamiento", "capital")

CATALOGO_RECURSOS = [
    {
        "nombre": "Apoyo demostrativo de alojamiento temporal",
        "descripcion": "Recurso demostrativo para necesidades urgentes de vivienda temporal.",
        "categoria": "Alojamiento",
        "necesidades_compatibles": ["alojamiento", "vivienda"],
        "danos_compatibles": [],
        "rutas_compatibles": ["ayuda_inmediata"],
    },
    {
        "nombre": "Apoyo demostrativo de alimentación",
        "descripcion": "Recurso demostrativo para cubrir necesidades alimentarias urgentes.",
        "categoria": "Alimentación",
        "necesidades_compatibles": ["alimentacion", "alimentación"],
        "danos_compatibles": [],
        "rutas_compatibles": ["ayuda_inmediata"],
    },
    {
        "nombre": "Apoyo demostrativo de agua potable",
        "descripcion": "Recurso demostrativo para acceso a agua en situaciones de emergencia.",
        "categoria": "Agua",
        "necesidades_compatibles": ["agua"],
        "danos_compatibles": [],
        "rutas_compatibles": ["ayuda_inmediata"],
    },
    {
        "nombre": "Apoyo demostrativo de medicamentos",
        "descripcion": "Recurso demostrativo para necesidades de salud y medicamentos.",
        "categoria": "Salud",
        "necesidades_compatibles": ["medicamentos", "salud"],
        "danos_compatibles": [],
        "rutas_compatibles": ["ayuda_inmediata"],
    },
    {
        "nombre": "Apoyo demostrativo para evaluación de vivienda",
        "descripcion": "Recurso demostrativo para solicitar evaluación técnica del inmueble.",
        "categoria": "Evaluación",
        "necesidades_compatibles": ["evaluacion", "evaluación", "reparacion", "reparación"],
        "danos_compatibles": ["estructural", "grietas", "techo", "vivienda"],
        "rutas_compatibles": ["vivienda"],
    },
    {
        "nombre": "Apoyo demostrativo para reparación de vivienda",
        "descripcion": "Recurso demostrativo orientado a reparaciones básicas del hogar.",
        "categoria": "Reparación",
        "necesidades_compatibles": ["reparacion", "reparación", "vivienda"],
        "danos_compatibles": ["estructural", "grietas", "techo", "servicios", "vivienda"],
        "rutas_compatibles": ["vivienda"],
    },
    {
        "nombre": "Apoyo demostrativo para recuperación de equipamiento",
        "descripcion": "Recurso demostrativo relacionado con la recuperación de maquinaria y herramientas.",
        "categoria": "Equipamiento",
        "necesidades_compatibles": ["equipamiento", "equipos"],
        "danos_compatibles": ["maquinaria", "equipos", "herramientas"],
        "rutas_compatibles": ["ingresos"],
    },
    {
        "nombre": "Apoyo demostrativo para reparación del espacio de trabajo",
        "descripcion": "Recurso demostrativo orientado a reparar el local o espacio donde se realiza la actividad.",
        "categoria": "Reparación",
        "necesidades_compatibles": ["reparacion", "reparación", "espacio"],
        "danos_compatibles": ["local", "infraestructura", "vivienda", "espacio"],
        "rutas_compatibles": ["ingresos"],
    },
    {
        "nombre": "Apoyo demostrativo para reactivación económica",
        "descripcion": "Recurso demostrativo relacionado con necesidades de financiación para la recuperación.",
        "categoria": "Financiamiento",
        "necesidades_compatibles": ["dinero", "financiamiento", "capital"],
        "danos_compatibles": ["mercancía", "mercancia"],
        "rutas_compatibles": ["ingresos"],
    },
    {
        "nombre": "Apoyo demostrativo para adquisición de insumos",
        "descripcion": "Recurso demostrativo para obtener insumos necesarios y retomar la actividad.",
        "categoria": "Insumos",
        "necesidades_compatibles": ["insumos"],
        "danos_compatibles": ["mercancía", "mercancia"],
        "rutas_compatibles": ["ingresos"],
    },
    {
        "nombre": "Apoyo demostrativo de transporte temporal",
        "descripcion": "Recurso demostrativo para cubrir necesidades de transporte durante la recuperación.",
        "categoria": "Transporte",
        "necesidades_compatibles": ["transporte"],
        "danos_compatibles": [],
        "rutas_compatibles": ["ingresos", "ayuda_inmediata"],
    },
    {
        "nombre": "Espacio temporal demostrativo para continuar la actividad",
        "descripcion": "Recurso demostrativo que ofrece un espacio alterno mientras se recupera el local habitual.",
        "categoria": "Espacio",
        "necesidades_compatibles": ["espacio"],
        "danos_compatibles": ["local", "espacio", "infraestructura"],
        "rutas_compatibles": ["ingresos"],
    },
]


@dataclass
class ContextoMatching:
    tipo_ruta: str
    necesidades: list[str]
    danos: list[str]


def _contiene_termino(items, terminos):
    for item in items:
        item_lower = item.lower()
        for termino in terminos:
            if termino in item_lower:
                return True
    return False


def _coincide_con_terminos(items_usuario, terminos_recurso):
    for item in items_usuario:
        item_lower = item.lower()
        for termino in terminos_recurso:
            if termino in item_lower:
                return True
    return False


def _contexto_ingresos(datos):
    return ContextoMatching(
        tipo_ruta="ingresos",
        necesidades=list(datos.necesidades),
        danos=list(datos.danos),
    )


def _contexto_ayuda_inmediata(datos):
    return ContextoMatching(
        tipo_ruta="ayuda_inmediata",
        necesidades=[datos.necesidad.lower()],
        danos=[],
    )


def _contexto_vivienda(datos):
    return ContextoMatching(
        tipo_ruta="vivienda",
        necesidades=["reparacion", "vivienda"],
        danos=[item.lower() for item in datos.tipo_afectacion],
    )


def _determinar_categoria_principal(contexto: ContextoMatching, datos):
    if contexto.tipo_ruta == "ayuda_inmediata":
        mapeo = {
            "alojamiento": "Alojamiento",
            "alimentacion": "Alimentación",
            "alimentación": "Alimentación",
            "agua": "Agua",
            "medicamentos": "Salud",
            "servicios": "Servicios básicos",
        }
        for necesidad in contexto.necesidades:
            for termino, categoria in mapeo.items():
                if termino in necesidad:
                    return categoria
        return "Servicios básicos"

    if contexto.tipo_ruta == "vivienda":
        habitabilidad = datos.habitabilidad.lower()
        if "no" in habitabilidad:
            return "Evaluación"
        if "parcial" in habitabilidad:
            return "Reparación"
        return "Reparación"

    if not datos.puede_operar and _contiene_termino(datos.danos, TERMINOS_EQUIPAMIENTO):
        return "Equipamiento"
    if not datos.puede_operar and _contiene_termino(datos.danos, TERMINOS_ESPACIO):
        return "Reparación"
    if datos.puede_operar and _contiene_termino(datos.necesidades, TERMINOS_ECONOMICO):
        return "Financiamiento"

    mapeo_necesidad = {
        "equipamiento": "Equipamiento",
        "dinero": "Financiamiento",
        "reparacion": "Reparación",
        "insumos": "Insumos",
        "transporte": "Transporte",
        "espacio": "Espacio",
    }
    for necesidad in contexto.necesidades:
        for termino, categoria in mapeo_necesidad.items():
            if termino in necesidad.lower():
                return categoria
    return None


def _recurso_es_compatible(recurso, contexto: ContextoMatching):
    if contexto.tipo_ruta not in recurso.get("rutas_compatibles", []):
        return False
    coincide_necesidad = _coincide_con_terminos(
        contexto.necesidades,
        recurso["necesidades_compatibles"],
    )
    coincide_dano = _coincide_con_terminos(
        contexto.danos,
        recurso["danos_compatibles"],
    )
    return coincide_necesidad or coincide_dano


def _puntuar_recurso(recurso, contexto, categoria_principal):
    puntuacion = 0
    if categoria_principal and recurso["categoria"] == categoria_principal:
        puntuacion += 100
    for termino in recurso["necesidades_compatibles"]:
        if _coincide_con_terminos(contexto.necesidades, [termino]):
            puntuacion += 10
    for termino in recurso["danos_compatibles"]:
        if _coincide_con_terminos(contexto.danos, [termino]):
            puntuacion += 10
    return puntuacion


def buscar_ayudas_compatibles(contexto: ContextoMatching, datos, categoria_principal=None):
    if categoria_principal is None:
        categoria_principal = _determinar_categoria_principal(contexto, datos)

    municipio = getattr(datos, "municipio", "").strip().lower()
    catalogo = obtener_catalogo_completo()
    en_municipio = [r for r in catalogo if r["municipio"].lower() == municipio]
    pool = en_municipio if en_municipio else catalogo

    compatibles = [
        recurso for recurso in pool
        if _recurso_es_compatible(recurso, contexto)
    ]
    compatibles.sort(
        key=lambda recurso: (
            _puntuar_recurso(recurso, contexto, categoria_principal),
            recurso.get("unidades_disponibles", 0),
        ),
        reverse=True,
    )
    return [
        {
            "nombre": recurso["nombre"],
            "descripcion": recurso["descripcion"],
            "categoria": recurso["categoria"],
            "municipio": recurso["municipio"],
            "zona_sismica": recurso["zona_sismica"],
            "unidades_disponibles": recurso["unidades_disponibles"],
            "demostrativo": True,
        }
        for recurso in compatibles[:5]
    ]


def _resultado(que_hacer_primero, ruta, ayudas, ruta_nombre, barrera_principal=None):
    resultado = {
        "que_hacer_primero": que_hacer_primero,
        "ruta": ruta,
        "ayudas": ayudas,
        "ruta_nombre": ruta_nombre,
    }
    if barrera_principal:
        resultado["barrera_principal"] = barrera_principal
    return resultado


def generar_ruta_ayuda_inmediata(datos):
    contexto = _contexto_ayuda_inmediata(datos)
    categoria = _determinar_categoria_principal(contexto, datos)
    necesidad = datos.necesidad.lower()
    urgencia = datos.urgencia.lower()

    if "alojamiento" in necesidad:
        que_hacer = "Tu necesidad prioritaria es alojamiento temporal"
        barrera = "Falta de vivienda segura"
    elif "aliment" in necesidad:
        que_hacer = "Tu necesidad prioritaria es acceso a alimentación"
        barrera = "Falta de alimentos"
    elif "agua" in necesidad:
        que_hacer = "Tu necesidad prioritaria es acceso a agua potable"
        barrera = "Falta de agua"
    elif "medic" in necesidad:
        que_hacer = "Tu necesidad prioritaria es atención y medicamentos"
        barrera = "Necesidad de salud urgente"
    else:
        que_hacer = "Tu necesidad prioritaria es apoyo de servicios básicos"
        barrera = "Servicios básicos afectados"

    if urgencia == "alta":
        que_hacer += ". Urgencia: alta"

    ruta = [
        "Confirmar ubicación y personas del hogar",
        "Identificar la necesidad más urgente",
        "Buscar apoyo demostrativo compatible disponible",
        "Realizar la siguiente acción recomendada",
    ]
    ayudas = buscar_ayudas_compatibles(contexto, datos, categoria)
    return _resultado(que_hacer, ruta, ayudas, "Ayuda inmediata", barrera)


def generar_ruta_vivienda(datos):
    contexto = _contexto_vivienda(datos)
    categoria = _determinar_categoria_principal(contexto, datos)
    habitabilidad = datos.habitabilidad.lower()

    if "no" in habitabilidad:
        que_hacer = "Tu vivienda requiere evaluación. Nivel preliminar de prioridad: alto"
        barrera = "Vivienda no habitable"
    elif "parcial" in habitabilidad:
        que_hacer = "Tu vivienda requiere reparaciones antes de ser habitable por completo"
        barrera = "Habitabilidad parcial"
    else:
        que_hacer = "Recuperar los servicios y condiciones de tu vivienda"
        barrera = "Servicios o estructura afectados"

    ruta = [
        "Verificar las condiciones actuales de la vivienda",
        "Identificar los daños que impiden habitar con seguridad",
        "Solicitar evaluación técnica demostrativa",
        "Priorizar reparaciones para recuperar la habitabilidad",
    ]
    ayudas = buscar_ayudas_compatibles(contexto, datos, categoria)
    return _resultado(que_hacer, ruta, ayudas, "Recuperar vivienda", barrera)


def generar_ruta_ingresos(datos):
    contexto = _contexto_ingresos(datos)
    categoria = _determinar_categoria_principal(contexto, datos)

    if not datos.puede_operar and _contiene_termino(datos.danos, TERMINOS_EQUIPAMIENTO):
        que_hacer = "Recuperar el equipamiento indispensable para volver a operar"
        barrera = "Pérdida de equipamiento"
        ruta = [
            "Identificar el equipamiento indispensable",
            "Determinar qué puede repararse o reemplazarse",
            "Buscar apoyo para recuperar el equipamiento",
            "Preparar la reactivación de la actividad",
        ]
    elif not datos.puede_operar and _contiene_termino(datos.danos, TERMINOS_ESPACIO):
        que_hacer = "Recuperar las condiciones necesarias del espacio para volver a operar"
        barrera = "Espacio de trabajo afectado"
        ruta = [
            "Verificar las condiciones del espacio",
            "Identificar los daños que impiden operar",
            "Priorizar las reparaciones necesarias",
            "Preparar la reapertura",
        ]
    elif datos.puede_operar and _contiene_termino(datos.necesidades, TERMINOS_ECONOMICO):
        que_hacer = "Recuperar el flujo económico necesario para mantener la actividad"
        barrera = "Necesidad financiera"
        ruta = [
            "Identificar las necesidades económicas inmediatas",
            "Estimar los recursos necesarios",
            "Buscar opciones de apoyo financiero",
            "Priorizar los gastos necesarios para continuar operando",
        ]
    else:
        que_hacer = "Identificar la necesidad principal para comenzar la recuperación"
        barrera = "Barrera por determinar"
        ruta = [
            "Revisar los daños y necesidades registrados",
            "Determinar qué limita más la actividad en este momento",
            "Priorizar la acción más urgente",
            "Definir los primeros pasos concretos de recuperación",
        ]

    ayudas = buscar_ayudas_compatibles(contexto, datos, categoria)
    return _resultado(que_hacer, ruta, ayudas, "Recuperar ingresos", barrera)


def generar_ruta(datos):
    tipo_ruta = getattr(datos, "tipo_ruta", "ingresos")
    if tipo_ruta == "ayuda_inmediata":
        return generar_ruta_ayuda_inmediata(datos)
    if tipo_ruta == "vivienda":
        return generar_ruta_vivienda(datos)
    return generar_ruta_ingresos(datos)


# Re-export para compatibilidad con imports existentes
__all__ = ["generar_ruta", "obtener_catalogo_publico", "CATALOGO_RECURSOS"]
