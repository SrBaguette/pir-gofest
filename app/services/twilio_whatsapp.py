"""
Integración Twilio WhatsApp: validación de firma, TwiML y envío de mensajes.
"""

import html
import os
from urllib.parse import urljoin

from fastapi import HTTPException, Request

from app.services.conversacion_whatsapp import procesar_mensaje

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")  # ej: whatsapp:+14155238886
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")  # ej: https://xxxx.ngrok.io


def _validar_credenciales() -> list[str]:
    """Advertencias sobre formato de credenciales (sin exponer valores)."""
    avisos = []
    if TWILIO_ACCOUNT_SID and not TWILIO_ACCOUNT_SID.startswith("AC"):
        avisos.append("TWILIO_ACCOUNT_SID debe comenzar con AC (Account SID).")
    if TWILIO_AUTH_TOKEN.startswith("SK"):
        avisos.append(
            "TWILIO_AUTH_TOKEN parece un API Key (SK...). "
            "Usa el Auth Token principal de Account Info en console.twilio.com (32 caracteres, sin prefijo SK)."
        )
    elif TWILIO_AUTH_TOKEN and len(TWILIO_AUTH_TOKEN) != 32:
        avisos.append("TWILIO_AUTH_TOKEN suele tener exactamente 32 caracteres.")
    if TWILIO_WHATSAPP_FROM and not TWILIO_WHATSAPP_FROM.startswith("whatsapp:+"):
        avisos.append("TWILIO_WHATSAPP_FROM debe tener formato whatsapp:+573001234567")
    if not PUBLIC_BASE_URL.strip():
        avisos.append("PUBLIC_BASE_URL vacío — ngrok no llegará al webhook.")
    return avisos


def twilio_configurado() -> bool:
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM)


def webhook_url() -> str:
    base = PUBLIC_BASE_URL.rstrip("/")
    return urljoin(base + "/", "webhook/whatsapp")


def _twiml_respuesta(texto: str) -> str:
    seguro = html.escape(texto)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{seguro}</Message></Response>"
    )


def _validar_firma_twilio(request: Request, params: dict) -> None:
    if not TWILIO_AUTH_TOKEN:
        return

    firma = request.headers.get("X-Twilio-Signature", "")
    if not firma:
        raise HTTPException(status_code=403, detail="Firma Twilio ausente")

    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        return

    url = str(request.url)
    if PUBLIC_BASE_URL:
        url = webhook_url()

    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    if not validator.validate(url, params, firma):
        raise HTTPException(status_code=403, detail="Firma Twilio inválida")


async def manejar_webhook(request: Request) -> str:
    form = await request.form()
    params = dict(form)
    _validar_firma_twilio(request, params)

    telefono = params.get("From", "")
    cuerpo = params.get("Body", "")

    if not telefono:
        raise HTTPException(status_code=400, detail="Mensaje sin remitente")

    respuesta = procesar_mensaje(telefono, cuerpo)
    return _twiml_respuesta(respuesta)


def enviar_mensaje_whatsapp(destino: str, texto: str) -> dict:
    """
    Envío proactivo (seguimiento: ¿pudiste acceder a la ayuda?).
    Requiere TWILIO_* configurado.
    """
    if not twilio_configurado():
        return {"ok": False, "error": "Twilio no configurado"}

    try:
        from twilio.rest import Client
    except ImportError:
        return {"ok": False, "error": "Paquete twilio no instalado (pip install twilio)"}

    cliente = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    to = destino if destino.startswith("whatsapp:") else f"whatsapp:{destino}"

    mensaje = cliente.messages.create(
        body=texto,
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
    )
    return {"ok": True, "sid": mensaje.sid}


def estado_integracion() -> dict:
    avisos = _validar_credenciales()
    credenciales_ok = None
    if twilio_configurado() and not any("SK" in a for a in avisos):
        try:
            from twilio.rest import Client
            Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).api.accounts(TWILIO_ACCOUNT_SID).fetch()
            credenciales_ok = True
        except Exception:
            credenciales_ok = False
            avisos.append("Twilio rechazó SID + Auth Token. Revisa credenciales en console.twilio.com.")

    return {
        "configurado": twilio_configurado(),
        "credenciales_validas": credenciales_ok,
        "webhook_url": webhook_url() if PUBLIC_BASE_URL else None,
        "whatsapp_from": TWILIO_WHATSAPP_FROM or None,
        "avisos": avisos,
        "variables_requeridas": [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_WHATSAPP_FROM",
            "PUBLIC_BASE_URL",
        ],
    }
