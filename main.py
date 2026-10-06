import os
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, HTMLResponse
import httpx

app = FastAPI(title="Secretária Lumi — Decorê")

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")

@app.get("/")
async def health():
   return {"status": "online", "service": "Secretária Lumi", "brand": "Decorê"}

@app.get("/privacy")
async def privacy():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Política de Privacidade — Secretária Lumi</title>
</head>
<body>
    <h1>Política de Privacidade — Secretária Lumi</h1>

    <p>A Secretária Lumi é um serviço da Decorê Personalizados de Luxo destinado ao atendimento e à automação de comunicações.</p>

    <h2>Informações tratadas</h2>
    <p>Podem ser tratados dados fornecidos durante o atendimento, como nome, número de telefone e conteúdo das mensagens.</p>

    <h2>Uso das informações</h2>
    <p>As informações são utilizadas para atendimento ao cliente, organização das conversas e funcionamento da integração com o WhatsApp Business.</p>

    <h2>Compartilhamento</h2>
    <p>As informações podem ser processadas por serviços tecnológicos necessários ao funcionamento da integração e do atendimento.</p>

    <h2>Segurança</h2>
    <p>São adotadas medidas técnicas e administrativas para proteger as informações contra acesso não autorizado.</p>

    <h2>Exclusão de dados</h2>
    <p>Solicitações de acesso, correção ou exclusão de dados podem ser feitas pelos canais de atendimento da Decorê.</p>

    <h2>Contato</h2>
    <p>Decorê Personalizados de Luxo</p>
</body>
</html>
""")

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

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                for message in value.get("messages", []):
                    if message.get("type") != "text":
                        continue

                    from_number = message.get("from")
                    text = message.get("text", {}).get("body", "").strip()

                    if from_number and text:
                        resposta = (
                            "Olá! 💜 Sou a Secretária Lumi da Decorê. "
                            "Recebi sua mensagem e já estou aqui para atender você! ✨"
                        )
                        await send_whatsapp_text(from_number, resposta)

    except Exception as e:
        print("Erro ao processar mensagem:", repr(e))

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

        if response.status_code >= 400:
            print("ERRO META:", response.status_code, response.text)
            raise RuntimeError(
                f"WhatsApp API error {response.status_code}: {response.text}"
            )

        return response.json()
