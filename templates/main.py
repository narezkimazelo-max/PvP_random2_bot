import os
import asyncio
import random
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from threading import Thread

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8710698401:AAEC4skVHrHjG0AmngdWJZzkNv0VoM7jLaM'
app = FastAPI()
templates = Jinja2Templates(directory="templates")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ (В памяти) ---
db = {
    "users": {}, # {id: {bal: 100, name: "nick"}}
    "game": {
        "players": {}, # {id: bet}
        "timer": 40,
        "is_active": False,
        "result": None
    }
}

# --- ЛОГИКА ИГРЫ ---
async def run_game_cycle():
    db["game"]["is_active"] = True
    db["game"]["timer"] = 40
    
    while db["game"]["timer"] > 0:
        await asyncio.sleep(1)
        db["game"]["timer"] -= 1
    
    await asyncio.sleep(2) # Пауза для визуала
    
    players = db["game"]["players"]
    if players:
        uids = list(players.keys())
        weights = list(players.values())
        winner_id = random.choices(uids, weights=weights, k=1)[0]
        
        total_bank = sum(players.values())
        winner_bet = players[winner_id]
        others_bet = total_bank - winner_bet
        
        # Комиссия 8% с проигрышей
        prize = winner_bet + (others_bet * 0.92)
        db["users"][winner_id]["bal"] += prize
        
        db["game"]["result"] = {
            "username": db["users"][winner_id]["name"],
            "prize": round(prize, 2),
            "cell": random.randint(0, 99)
        }
    
    await asyncio.sleep(7) # Показ шторки
    db["game"]["players"] = {}
    db["game"]["is_active"] = False
    db["game"]["result"] = None

# --- API ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/get_state")
async def get_state(uid: str, username: str):
    if uid not in db["users"]:
        db["users"][uid] = {"bal": 0.0, "name": username}
    return {"user": db["users"][uid], "game": db["game"]}

@app.post("/api/add_ton")
async def add_ton(data: dict):
    uid = str(data['uid'])
    if uid in db["users"]:
        db["users"][uid]["bal"] += 10.0
        return db["users"][uid]
    return {"error": "user not found"}

@app.post("/api/place_bet")
async def place_bet(data: dict):
    uid, amount = str(data['uid']), float(data['amount'])
    if db["users"].get(uid) and db["users"][uid]["bal"] >= amount:
        db["users"][uid]["bal"] -= amount
        db["game"]["players"][uid] = db["game"]["players"].get(uid, 0) + amount
        
        if len(db["game"]["players"]) >= 2 and not db["game"]["is_active"]:
            asyncio.create_task(run_game_cycle())
        return {"status": "ok"}
    return {"status": "error"}

# --- БОТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Прямая ссылка на твой Replit для надежности
    url = "https://pvp-random2-bot.narezkimazelo-max.repl.co"
    
    kb = [[types.InlineKeyboardButton(text="⚔️ ИГРАТЬ PvP", web_app=WebAppInfo(url=url))]]
    await message.answer(
        f"Привет, {message.from_user.first_name}!\nЖми кнопку ниже, чтобы войти в игру.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )

def start_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    # Запуск сервера на порту 8080 (важно для Replit)
    Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8080)).start()
    start_bot()
