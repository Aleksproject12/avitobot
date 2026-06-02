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
WEBHOOK_URL = "https://avitobot-production.up.railway.app/webhook"

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
              "system": "Ты эксперт по продающим объявлениям на Авито для услуг. Стиль живой, без канцелярита. ЗАГОЛОВКИ строго до 50 символов. Цель заставить кликнуть из ленты. Примеры хитов: Жена сказала ещё одна скважина развод, Коммунальщики молятся чтоб я бросил бурить, Пробурю скважину пока вы жирите шашлык. ФОРМАТ только JSON без markdown: {headlines:[{text:заголовок,style:тема}],ad_text:текст}",
                "messages": messages,
            },
        )
        return JSONResponse(response.json())

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("messag
