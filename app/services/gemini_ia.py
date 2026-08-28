"""
Integración Gemini (tier gratuito) — NLU, confianza narrativa y recomendaciones.

Usa REST API directa (requests). Modelo por defecto: gemini-3.5-flash-lite.
Si falla, intenta modelos alternativos del tier gratuito.
"""

import json
import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
MODELOS_FALLBACK = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemma-4-26b-a4b-it",
]

_SYSTEM = (
    "Eres un asistente institucional del Pasaporte Inteligente de Recuperación "
    "post-emergencia en Colombia. Respuestas concisas, empáticas, en español. "
    "Nunca rechaces ayuda automáticamente; solo señala si hace falta validación."
)


def gemini_disponible() -> bool:
    return bool(GEMINI_API_KEY)


def estado_gemini(probar_conexion: bool = False) -> dict:
    ok = None
    avisos: list[str] = []
    if not gemini_disponible():
        avisos.append("GEMINI_API_KEY no configurada en .env (formato: GEMINI_API_KEY=...)")
    elif probar_conexion:
        texto = _generar("Responde solo: OK", max_tokens=16)
        ok = texto is not None
        if not ok:
            avisos.append("Gemini no respondió — revisa cuota o API key en AI Studio")
    else:
        ok = True

    return {
        "configurado": gemini_disponible(),
        "activo": ok,
        "modelo": GEMINI_MODEL if gemini_disponible() else None,
        "usos": [
            "Clasificar mensajes WhatsApp / demo (NLU)",
            "Explicar confianza del reporte (ML4 narrativo)",
            "Priorizar ayudas con justificación (ML3)",
            "Resumir alertas ML1 para dashboard",
        ],
        "avisos": avisos,
    }


def _generar(prompt: str, system: str = "", max_tokens: int = 1024) -> str | None:
    if not gemini_disponible():
        return None

    modelos = [GEMINI_MODEL] + [m for m in MODELOS_FALLBACK if m != GEMINI_MODEL]
    body_base: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.2},
    }
    instruccion = system or _SYSTEM
    body_base["systemInstruction"] = {"parts": [{"text": instruccion}]}

    for modelo in modelos:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{modelo}:generateContent?key={GEMINI_API_KEY}"
        )
        try:
            resp = requests.post(url, json=body_base, timeout=45)
            if resp.status_code == 503:
                continue
            if not resp.ok:
                logger.warning("Gemini %s: %s", modelo, resp.text[:120])
                continue
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            texto = "".join(p.get("text", "") for p in parts).strip()
            if texto:
                return texto
        except Exception as exc:
            logger.warning("Gemini error (%s): %s", modelo, exc)
    return None


def _extraer_json(texto: str) -> dict | None:
    if not texto:
        return None
    limpio = texto.strip()
    bloque = re.search(r"```(?:json)?\s*([\s\S]*?)```", limpio)
    if bloque:
        limpio = bloque.group(1).strip()
    try:
        return json.loads(limpio)
    except json.JSONDecodeError:
        inicio = limpio.find("{")
        fin = limpio.rfind("}")
        if inicio >= 0 and fin > inicio:
            try:
                return json.loads(limpio[inicio : fin + 1])
            except json.JSONDecodeError:
                return None
    return None


def interpretar_mensaje(mensaje: str, contexto: dict | None = None) -> dict | None:
    ctx = json.dumps(contexto or {}, ensure_ascii=False)
    prompt = f"""Analiza este mensaje de una persona afectada post-emergencia en Colombia.

Mensaje: "{mensaje}"
Contexto de sesión: {ctx}

Responde SOLO un JSON válido (sin markdown):
{{
  "ruta_sugerida": "ayuda_inmediata" | "vivienda" | "ingresos" | null,
  "menu_opcion": "1" | "2" | "3" | null,
  "municipio": string | null,
  "necesidad_principal": string | null,
  "urgencia": "baja" | "media" | "alta" | null,
  "resumen_corto": "máximo 2 frases institucionales",
  "siguiente_pregunta": "qué preguntar a continuación",
  "confianza_extraccion": "alta" | "media" | "baja"
}}"""
    return _extraer_json(_generar(prompt, max_tokens=512) or "")


def evaluar_confianza_narrativa(datos: dict, señales: dict) -> dict | None:
    prompt = f"""Evalúa la calidad/confianza de este reporte de recuperación post-emergencia.

Datos: {json.dumps(datos, ensure_ascii=False)}
Señales del sistema: {json.dumps(señales, ensure_ascii=False)}

Responde SOLO JSON:
{{
  "nivel": "alta" | "requiere_validacion" | "anomalia_suave",
  "etiqueta": "texto corto",
  "motivos": ["motivo 1", "motivo 2"],
  "accion_sugerida": "acción para funcionario (sin rechazar ayuda)",
  "disclaimer": "La IA no decide rechazos automáticos"
}}"""
    return _extraer_json(_generar(prompt, max_tokens=512) or "")


def recomendar_ayudas(perfil: dict, ayudas: list[dict]) -> dict | None:
    if not ayudas:
        return None
    prompt = f"""Perfil: {json.dumps(perfil, ensure_ascii=False)}
Ayudas: {json.dumps(ayudas[:8], ensure_ascii=False)}

Responde SOLO JSON:
{{
  "orden_ids": ["nombre ayuda 1", "nombre ayuda 2"],
  "explicacion": "2 frases justificando el orden",
  "ruta_recuperacion": "siguiente paso concreto en lenguaje simple"
}}"""
    return _extraer_json(_generar(prompt, max_tokens=512) or "")


def resumir_alertas_ml1(alertas: list[dict], resumen: dict) -> dict | None:
    if not alertas and not resumen.get("total_afectados"):
        return None

    por_municipio = resumen.get("por_municipio", {})
    top_municipios = sorted(por_municipio.items(), key=lambda x: x[1], reverse=True)[:5]
    brechas_top = [
        b for b in (resumen.get("brechas") or []) if b.get("brecha", 0) > 0
    ][:4]
    prioridades = (resumen.get("prioridades_entidad") or {}).get("prioridades", [])[:3]
    perfil = resumen.get("perfil_demo") or "—"

    contexto = {
        "perfil_escenario": perfil,
        "total_afectados": resumen.get("total_afectados", 0),
        "municipios_top": dict(top_municipios),
        "municipio_foco_brechas": resumen.get("municipio_foco_brechas"),
        "alertas_ml1": alertas[:5],
        "brechas_con_deficit": brechas_top,
        "prioridades_entidad": prioridades,
        "zonas_mapa": resumen.get("mapa_inteligente", {}).get("zonas_resumen", []),
    }

    prompt = f"""Resumen ejecutivo para alcalde (máx. 120 palabras).
IMPORTANTE: menciona al menos 2 municipios concretos de los datos (nombres exactos).
Explica qué está pasando EN CADA ZONA o municipio principal según el escenario cargado.

Contexto territorial (JSON):
{json.dumps(contexto, ensure_ascii=False)}

Responde SOLO JSON:
{{
  "titulo": "headline corto con municipio principal",
  "resumen_ejecutivo": "párrafo accionable citando municipios y necesidades",
  "accion_recomendada": "acción concreta para hoy nombrando municipio",
  "nivel_alerta": "info" | "media" | "alta",
  "municipios_destacados": ["Municipio1", "Municipio2", "Municipio3"],
  "perfil_interpretado": "a|b|manual"
}}"""

    resultado = _extraer_json(_generar(prompt, max_tokens=700) or "")
    if resultado:
        return resultado

    # Fallback sin Gemini: resumen legible con municipios reales
    if not top_municipios:
        return None
    nombres = [m for m, _ in top_municipios[:3]]
    return {
        "titulo": f"Concentración en {nombres[0]}",
        "resumen_ejecutivo": (
            f"Escenario {perfil.upper()}: {resumen.get('total_afectados', 0)} casos registrados. "
            f"Municipios con más solicitudes: {', '.join(nombres)}. "
            f"Revisar brechas de cupos en {resumen.get('municipio_foco_brechas') or nombres[0]}."
        ),
        "accion_recomendada": (
            prioridades[0]["accion_sugerida"]
            if prioridades
            else f"Priorizar atención en {nombres[0]}."
        ),
        "nivel_alerta": "media",
        "municipios_destacados": nombres,
        "perfil_interpretado": perfil,
        "generado_por": "reglas_fallback",
    }


def enriquecer_diagnostico(datos: dict, resultado: dict, pasaporte: dict) -> dict:
    señales = {
        "prioridad": pasaporte.get("prioridad_etiqueta"),
        "confianza_reglas": pasaporte.get("confianza_etiqueta"),
        "tiene_evidencia": bool(datos.get("evidencia")),
        "municipio": datos.get("municipio"),
    }
    confianza = evaluar_confianza_narrativa(datos, señales)
    ayudas = recomendar_ayudas(
        {
            "tipo_ruta": pasaporte.get("tipo_ruta"),
            "municipio": pasaporte.get("municipio"),
            "necesidades": pasaporte.get("necesidades", []),
            "actividad": pasaporte.get("actividad_economica"),
        },
        resultado.get("ayudas") or pasaporte.get("ayudas") or [],
    )
    return {
        "modelo": GEMINI_MODEL if gemini_disponible() else None,
        "confianza_ia": confianza,
        "recomendacion_ia": ayudas,
        "activo": confianza is not None or ayudas is not None,
    }
