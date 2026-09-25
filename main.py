import os
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import httpx

app = FastAPI(title="Secretária Lumi — Decorê")

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")

@app.get("/")
async def health():
    return {"status": "online", "service": "Secretária Lumi", "brand": "Decorê"}

@app.get("/webhook")
async def verify_webhook(
   hub_mode: str | None = Query(default=None, alias="hub.mode"),
hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge or "")
    raise HTTPException(status_code=403, detail="Token de verificação inválido")

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("Webhook recebido:", payload)
    return {"status": "received"}

async def send_whatsapp_text(to: str, message: str):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        raise RuntimeError("Credenciais do WhatsApp ainda não configuradas.")

    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
