import base64
import httpx
import aiofiles
from config import EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE

HEADERS = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
BASE = f"{EVOLUTION_API_URL}/message"


async def send_text(number: str, text: str):
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"{BASE}/sendText/{EVOLUTION_INSTANCE}",
            headers=HEADERS,
            json={"number": number, "text": text},
        )


async def send_document(number: str, file_path: str, caption: str):
    async with aiofiles.open(file_path, "rb") as f:
        data = await f.read()
    encoded = base64.b64encode(data).decode()
    filename = file_path.split("/")[-1]
    async with httpx.AsyncClient(timeout=60) as client:
        await client.post(
            f"{BASE}/sendMedia/{EVOLUTION_INSTANCE}",
            headers=HEADERS,
            json={
                "number": number,
                "mediatype": "document",
                "media": encoded,
                "fileName": filename,
                "caption": caption,
            },
        )
