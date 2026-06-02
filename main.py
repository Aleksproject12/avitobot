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

SYSTEM = (
    "Ты эксперт по созданию продающих объявлений на Авито для сферы услуг. "
    "Твоя задача — изучить объявления конкурентов и создать лучшее объявление на основе анализа. "
    "\n\n"
    "ПРИНЦИПЫ РАБОТЫ:\n"
    "1. Сначала анализируй что работает у конкурентов — формулы заголовков, структуру, триггеры, боли клиентов\n"
    "2. Создавай объявление которое использует лучшие приёмы но написано по-другому\n"
    "3. Стиль — живой, человеческий, как уверенный мастер говорит по делу\n"
    "\n"
    "ЗАГОЛОВКИ (строго до 50 символов):\n"
    "Цель — заставить кликнуть из ленты, не описать услугу.\n"
    "Используй разрыв шаблона, провокацию, юмор, абсурд, противоречие.\n"
    "Примеры хитов: "
    "Жена сказала ещё одна скважина развод, "
    "Коммунальщики молятся чтоб я бросил бурить, "
    "Пробурю скважину пока вы жирите шашлык, "
    "4000 скважин жена говорит это диагноз, "
    "Скважина готова сосед ещё шашлык не дожарил.\n"
    "Никогда не пиши скучные заголовки типа Услуга в городе недорого.\n"
    "\n"
    "СТРУКТУРА ТЕКСТА:\n"
    "1. Имя + стаж + главная гарантия (нет результата — не платишь)\n"
    "2. Конкретная цифра работ за N лет — социальное доказательство\n"
    "3. Боли клиента его словами — что он слышал у других\n"
    "4. Пошаговый план работы — 4-5 шагов кратко\n"
    "5. Конкретные гарантии с цифрами\n"
    "6. CTA — бесплатный первый шаг + дефицит или срочность\n"
    "7. Подпись: имя + всегда на связи\n"
    "Запрещено: качественно, недорого, опытные мастера, звоните договоримся без конкретики.\n"
    "Длина текста: 250-320 слов.\n"
    "\n"
    "ФОРМАТ ОТВЕТА — строго JSON без markdown:\n"
    '{"analysis":"анализ конкурентов 3-5 пунктов что работает в этой нише",'
    '"headlines":[{"text":"заголовок до 50 символов","style":"тема"}],'
    '"ad_text":"текст объявления"}'
)


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
                "model": "claude-sonnet-4-5",
                "max_tokens": 2000,
                "system": SYSTEM,
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
            "text": "Генератор объявлений для Авито\nНажми кнопку чтобы открыть:",
            "reply_markup": {
                "inline_keyboard": [[{
                    "text": "Открыть генератор",
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
async def set_webhook():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": WEBHOOK_URL}
        )
        return r.json()
