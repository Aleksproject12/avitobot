from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEB_APP_URL = os.environ.get("WEB_APP_URL", "")

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/generate")
async def generate(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1500,
                "system": "Ты эксперт по продающим объявлениям на Авито для услуг. Стиль — живой, без канцелярита. ЗАГОЛОВКИ строго до 50 символов. Цель — заставить кликнуть из ленты. Примеры хитов: 'Жена сказала: ещё одна скважина — развод', 'Коммунальщики молятся чтоб я бросил бурить', 'Пробурю скважину пока вы жирите шашлык'. ФОРМАТ — только JSON без markdown: {\"headlines\":[{\"text\":\"заголовок\",\"style\":\"тема\"}],\"ad_text\":\"текст\"}",
                "messages": messages,
            },
        )
        return JSONResponse(response.json())

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    if not chat_id:
        return {"ok": True}
    if text in ["/start", "/open"]:
        payload = {
            "chat_id": chat_id,
            "text": "Генератор объявлений для Авито 🔥\nНажми кнопку чтобы открыть:",
            "reply_markup": {
                "inline_keyboard": [[{
                    "text": "Открыть генератор →",
                    "web_app": {"url": WEB_APP_URL}
                }]]
            }
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json=payload
            )
    return {"ok": True}

@app.get("/set_webhook")
async def set_webhook(request: Request):
    host = str(request.base_url).rstrip("/")
    webhook_url = f"{host}/webhook"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": webhook_url}
        )
        return r.json()
