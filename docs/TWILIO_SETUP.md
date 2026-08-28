# Configuración Twilio + WhatsApp para PIR

## ¿Qué datos necesitas de Twilio?

| Dato | Dónde obtenerlo | Para qué sirve |
|------|-----------------|----------------|
| **Account SID** | [Twilio Console](https://console.twilio.com) → Account Info | Identificar tu cuenta |
| **Auth Token** | Misma pantalla (clic en "Show") | Validar webhooks y enviar mensajes |
| **WhatsApp From** | Messaging → Try WhatsApp → Sandbox | Número desde el que responde el bot |
| **PUBLIC_BASE_URL** | ngrok / deploy público | URL donde Twilio envía los mensajes |

### Variables de entorno

Copia `.env.example` a `.env` y completa:

```bash
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
PUBLIC_BASE_URL=https://xxxx.ngrok-free.app
```

Carga las variables antes de iniciar uvicorn (o usa un gestor como `python-dotenv`).

---

## Paso 1 — Cuenta Twilio

1. Crear cuenta en [twilio.com](https://www.twilio.com/try-twilio)
2. Verificar tu teléfono personal
3. Anotar **Account SID** y **Auth Token**

## Paso 2 — Sandbox de WhatsApp (desarrollo)

1. En consola: **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Activa el **WhatsApp Sandbox**
3. Desde tu WhatsApp personal, envía el código que te indica Twilio al número del sandbox (ej. `join <código>` a `+1 415 523 8886`)
4. El **From** del sandbox suele ser: `whatsapp:+14155238886`

## Paso 3 — Exponer el backend (local)

Twilio necesita una URL HTTPS pública:

```bash
# Terminal 1 — backend
uvicorn app.main:app --reload --port 8001

# Terminal 2 — túnel (ejemplo ngrok)
ngrok http 8001
```

Copia la URL HTTPS (ej. `https://abc123.ngrok-free.app`) en `PUBLIC_BASE_URL`.

## Paso 4 — Configurar webhook en Twilio

1. **Messaging** → **Try WhatsApp** → **Sandbox settings**
2. En **"When a message comes in"**:
   - URL: `https://TU-URL/webhook/whatsapp`
   - Método: **POST**
3. Guardar

## Paso 5 — Probar

Envía `hola` al sandbox de WhatsApp. Deberías recibir el menú de 3 rutas.

Verifica estado de la integración:

```bash
curl http://127.0.0.1:8001/integraciones/twilio
```

---

## Flujo implementado

```text
WhatsApp → Twilio → POST /webhook/whatsapp
                         ↓
              conversacion_whatsapp.py (estados)
                         ↓
              generar_ruta() + crear_pasaporte()
                         ↓
              Respuesta TwiML con ID del pasaporte
```

### Comandos del bot

| Mensaje | Acción |
|---------|--------|
| `hola`, `menu`, `inicio` | Menú de 3 rutas |
| `1`, `2`, `3` | Elegir ruta |
| Respuestas secuenciales | Preguntas del diagnóstico |
| Al finalizar | Pasaporte `PAS-XXXX` + ruta |

---

## Producción (post-hackathon)

Para salir del sandbox necesitas:

- **WhatsApp Business Account** vinculada a Twilio
- **Plantillas de mensaje** aprobadas por Meta (para mensajes proactivos)
- **Messaging Service SID** (opcional, recomendado)
- Dominio estable con HTTPS (Cloud Run, Railway, etc.)

### Paquete opcional

```bash
pip install twilio
```

Sin el paquete, el webhook sigue funcionando (TwiML manual). El envío proactivo (`enviar_mensaje_whatsapp`) requiere `twilio`.

---

## Seguridad

- En producción, `TWILIO_AUTH_TOKEN` valida la firma `X-Twilio-Signature` en cada webhook
- Nunca subas `.env` al repositorio
- El Auth Token es secreto — trátalo como contraseña
