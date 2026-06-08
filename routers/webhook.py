import asyncio
from fastapi import APIRouter, Request
from services import session as sess
from services.whatsapp import send_text, send_document
from services.sat.constancia import descargar_constancia
from services.sat.opinion import descargar_opinion
from config import AUTHORIZED_NUMBERS

router = APIRouter()

MENU = (
    "Hola! ¿Qué documento necesitas?\n\n"
    "1️⃣  Constancia de Situación Fiscal\n"
    "2️⃣  Opinión de Cumplimiento\n"
    "3️⃣  Facturar ticket _(próximamente)_"
)


def _extract(payload: dict) -> tuple[str, str] | None:
    """Extrae (número, texto) del payload de Evolution API."""
    try:
        data = payload.get("data", {})
        key = data.get("key", {})
        if key.get("fromMe"):
            return None
        jid: str = key.get("remoteJid", "")
        phone = jid.split("@")[0]
        msg = data.get("message", {})
        text = (
            msg.get("conversation")
            or msg.get("extendedTextMessage", {}).get("text")
            or ""
        ).strip()
        return phone, text
    except Exception:
        return None


@router.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()

    if payload.get("event") != "messages.upsert":
        return {"ok": True}

    result = _extract(payload)
    if not result:
        return {"ok": True}

    phone, text = result

    # Solo responder a números autorizados
    if AUTHORIZED_NUMBERS and phone not in AUTHORIZED_NUMBERS:
        return {"ok": True}

    state = sess.get_state(phone)

    if state == sess.State.IDLE:
        await send_text(phone, MENU)
        sess.set_state(phone, sess.State.WAITING_OPTION)
        return {"ok": True}

    if state == sess.State.WAITING_OPTION:
        if text == "1":
            sess.reset(phone)
            await send_text(phone, "Descargando tu Constancia de Situación Fiscal... ⏳")
            asyncio.create_task(_run_constancia(phone))

        elif text == "2":
            sess.reset(phone)
            await send_text(phone, "Descargando tu Opinión de Cumplimiento... ⏳")
            asyncio.create_task(_run_opinion(phone))

        elif text == "3":
            sess.reset(phone)
            await send_text(phone, "La opción de facturación estará disponible próximamente. 🚧")

        else:
            await send_text(phone, "Por favor responde 1, 2 o 3.\n\n" + MENU)

    return {"ok": True}


async def _run_constancia(phone: str):
    try:
        path = await descargar_constancia()
        await send_document(phone, path, "✅ Constancia de Situación Fiscal")
    except Exception as e:
        await send_text(phone, f"❌ Error al descargar la constancia: {e}")


async def _run_opinion(phone: str):
    try:
        path = await descargar_opinion()
        await send_document(phone, path, "✅ Opinión de Cumplimiento")
    except Exception as e:
        await send_text(phone, f"❌ Error al descargar la opinión: {e}")
