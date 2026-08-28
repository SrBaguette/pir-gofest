"""
Máquina de estados para conversación WhatsApp → diagnóstico → pasaporte.
Canal alternativo a la Web; usa la misma API de negocio (generar_ruta + crear_pasaporte).
"""

from app.schemas import (
    DiagnosticoAyudaInmediata,
    DiagnosticoIngresos,
    DiagnosticoVivienda,
)
from app.services.almacen import crear_pasaporte
from app.services.motor_ruta import generar_ruta

_sesiones: dict[str, dict] = {}

MENU_PRINCIPAL = (
    "Hola. Somos *Pasaporte Inteligente de Recuperación*.\n"
    "¿Qué necesitas recuperar primero?\n\n"
    "1 - Ayuda inmediata (alimentación, alojamiento, agua…)\n"
    "2 - Recuperar mi vivienda\n"
    "3 - Recuperar mis ingresos\n\n"
    "Responde con el número (1, 2 o 3)."
)

PASOS_AYUDA = [
    ("municipio", "¿En qué municipio te encuentras?"),
    ("personas_hogar", "¿Cuántas personas hay en tu hogar? (número)"),
    ("necesidad", "¿Cuál es tu necesidad principal?\n(alojamiento, alimentación, agua, medicamentos, servicios básicos)"),
    ("urgencia", "¿Qué tan urgente es?\n(baja, media, alta)"),
]

PASOS_VIVIENDA = [
    ("municipio", "¿En qué municipio está la vivienda afectada?"),
    ("tipo_afectacion", "¿Qué tipo de afectación tiene?\n(estructural, grietas, techo, servicios — separados por coma)"),
    ("habitabilidad", "¿Cuál es la habitabilidad?\n(habitable, parcialmente habitable, no habitable)"),
    ("servicios_afectados", "¿Qué servicios están afectados?\n(agua, luz, gas, drenaje, ninguno — separados por coma)"),
]

PASOS_INGRESOS = [
    ("municipio", "¿En qué municipio ocurre la afectación?"),
    ("actividad_economica", "¿Qué actividad económica realizas?\n(tienda, restaurante, taller, agricultura, otro)"),
    ("danos", "¿Qué resultó afectado?\n(equipos, local, maquinaria, mercancía — separados por coma)"),
    ("puede_operar", "¿Puedes continuar operando?\n(responde: sí o no)"),
    ("necesidades", "¿Qué necesitas para recuperarte?\n(equipamiento, dinero, reparación, insumos — separados por coma)"),
]

RUTAS = {
    "1": ("ayuda_inmediata", PASOS_AYUDA),
    "2": ("vivienda", PASOS_VIVIENDA),
    "3": ("ingresos", PASOS_INGRESOS),
}


def _nueva_sesion(telefono: str) -> None:
    _sesiones[telefono] = {"tipo_ruta": None, "paso": 0, "datos": {}}


def _parsear_lista(texto: str) -> list[str]:
    return [p.strip() for p in texto.split(",") if p.strip()]


def _finalizar_sesion(telefono: str, datos: dict, tipo_ruta: str) -> str:
    try:
        if tipo_ruta == "ayuda_inmediata":
            modelo = DiagnosticoAyudaInmediata(
                municipio=datos["municipio"],
                personas_hogar=int(datos["personas_hogar"]),
                necesidad=datos["necesidad"],
                urgencia=datos["urgencia"],
                evidencia=datos.get("evidencia", ""),
            )
        elif tipo_ruta == "vivienda":
            modelo = DiagnosticoVivienda(
                municipio=datos["municipio"],
                tipo_afectacion=_parsear_lista(datos["tipo_afectacion"]),
                habitabilidad=datos["habitabilidad"],
                servicios_afectados=_parsear_lista(datos["servicios_afectados"]),
                evidencia=datos.get("evidencia", ""),
            )
        else:
            modelo = DiagnosticoIngresos(
                municipio=datos["municipio"],
                actividad_economica=datos["actividad_economica"],
                danos=_parsear_lista(datos["danos"]),
                puede_operar=datos["puede_operar"].lower() in ("sí", "si", "s", "yes"),
                necesidades=_parsear_lista(datos["necesidades"]),
            )

        resultado = generar_ruta(modelo)
        pasaporte = crear_pasaporte(modelo, resultado)
        del _sesiones[telefono]

        ayudas_txt = ""
        if resultado.get("ayudas"):
            nombres = [a["nombre"] for a in resultado["ayudas"][:2]]
            ayudas_txt = "\n\nAyudas compatibles:\n• " + "\n• ".join(nombres)

        barrera = resultado.get("barrera_principal", "")
        barrera_txt = f"\n\nBarrera principal: {barrera}" if barrera else ""

        return (
            f"✅ *Tu Pasaporte de Recuperación*\n"
            f"ID: *{pasaporte['id']}*\n\n"
            f"*{resultado['ruta_nombre']}*\n"
            f"{resultado['que_hacer_primero']}"
            f"{barrera_txt}"
            f"{ayudas_txt}\n\n"
            f"Guarda tu ID para consultar tu progreso.\n"
            f"Escribe *menu* para iniciar otro diagnóstico."
        )
    except (ValueError, KeyError) as exc:
        _nueva_sesion(telefono)
        return f"No pudimos procesar tus datos ({exc}). Escribe *menu* para reiniciar."


def procesar_mensaje(telefono: str, texto: str) -> str:
    cuerpo = (texto or "").strip()
    clave = cuerpo.lower()

    if clave in ("menu", "hola", "inicio", "empezar", "start"):
        _nueva_sesion(telefono)
        return MENU_PRINCIPAL

    if clave in ("ayuda", "help"):
        return (
            "Comandos disponibles:\n"
            "• *menu* — iniciar diagnóstico\n"
            "• *1*, *2* o *3* — elegir ruta\n"
            "Responde cada pregunta en un solo mensaje."
        )

    sesion = _sesiones.get(telefono)

    if sesion is None:
        _nueva_sesion(telefono)
        return MENU_PRINCIPAL

    if sesion["tipo_ruta"] is None:
        if clave not in RUTAS:
            return "Opción no válida. Responde *1*, *2* o *3*.\n\n" + MENU_PRINCIPAL
        tipo, pasos = RUTAS[clave]
        sesion["tipo_ruta"] = tipo
        sesion["pasos"] = pasos
        sesion["paso"] = 0
        return pasos[0][1]

    pasos = sesion["pasos"]
    paso_idx = sesion["paso"]
    campo, _ = pasos[paso_idx]
    sesion["datos"][campo] = cuerpo
    sesion["paso"] += 1

    if sesion["paso"] >= len(pasos):
        return _finalizar_sesion(telefono, sesion["datos"], sesion["tipo_ruta"])

    return pasos[sesion["paso"]][1]
