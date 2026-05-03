import asyncio
import logging
import random
import time
import aiosqlite
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"
ADMIN_ID = 0  # Замени на свой ID (можно узнать через @userinfobot)
DB_NAME = "casino.db"
START_BALANCE = 1000
DAILY_BONUS = 200

# --- ЛОГИКА БАЗЫ ДАННЫХ ---
class Database:
    def __init__(self):
        self.name = DB_NAME

    async def setup(self):
        async with aiosqlite.connect(self.name) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 1000,
                last_bonus INTEGER DEFAULT 0,
                last_wheel INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0
            )''')
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def register_user(self, user_id, username):
        async with aiosqlite.connect(self.name) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
            await db.commit()

    async def update_balance(self, user_id, amount):
        async with aiosqlite.connect(self.name) as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    async def set_time(self, user_id, column, timestamp):
        async with aiosqlite.connect(self.name) as db:
            await db.execute(f"UPDATE users SET {column} = ? WHERE user_id = ?", (timestamp, user_id))
            await db.commit()

    async def get_top(self):
        async with aiosqlite.connect(self.name) as db:
            async with db.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10") as cursor:
                return await cursor.fetchall()

db = Database()
router = Router()
cooldowns = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def check_user(message: types.Message, bet: int = 0):
    user_id = message.from_user.id
    now = time.time()
    
    # Анти-спам 3 сек
    if user_id in cooldowns and now - cooldowns[user_id] < 3:
        await message.answer("⏱ **Подождите!** Не частите со ставками.")
        return None
    
    user = await db.get_user(user_id)
    if not user:
        await db.register_user(user_id, message.from_user.username or "Игрок")
        user = await db.get_user(user_id)
    
    if user['balance'] < bet:
        await message.answer(f"❌ Недостаточно 🪙. Ваш баланс: `{user['balance']}`")
        return None
        
    cooldowns[user_id] = now
    return user

# --- ОБРАБОТЧИКИ КОМАНД ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await db.register_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "🎰 **Добро пожаловать в Главное Казино!**\n\n"
        "💰 Вам начислено 1000 🪙 Coins.\n"
        "🕹 **Команды:**\n"
        "• `/slots [ставка]` — Игровые автоматы\n"
        "• `/dice [ставка] [больше/меньше]` — Кости\n"
        "• `/wheel` — Колесо удачи (раз в 2 часа)\n"
        "• `/profile` — Баланс и стата\n"
        "• `/top` — Список богачей",
        parse_mode="Markdown"
    )

@router.message(Command("slots"))
async def cmd_slots(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await message.answer("Введите: `/slots [ставка]`")
    
    bet = int(args[1])
    user = await check_user(message, bet)
    if not user: return

    symbols = ['🍒', '🍋', '🍊', '💎', '7️⃣']
    reel = [random.choice(symbols) for _ in range(3)]
    
    mult = 0
    if reel[0] == reel[1] == reel[2]:
        if reel[0] == '7️⃣': mult = 50
        elif reel[0] == '💎': mult = 15
        else: mult = 5
    
    win = bet * mult
    change = win - bet
    await db.update_balance(message.from_user.id, change)
    
    res = "🏆 ВЫИГРЫШ!" if mult > 0 else "📉 ПРОИГРЫШ"
    await message.answer(
        f"🎰 | {' | '.join(reel)} |\n\n"
        f"**{res}**\n"
        f"{'💰 +' if mult > 0 else '➖ '}{win if mult > 0 else bet} 🪙",
        parse_mode="Markdown"
    )

@router.message(Command("wheel"))
async def cmd_wheel(message: types.Message):
    user = await check_user(message)
    if not user: return
    
    now = int(time.time())
    if now - user['last_wheel'] < 7200:
        rem = (7200 - (now - user['last_wheel'])) // 60
        return await message.answer(f"⏳ Колесо доступно через **{rem} мин.**")
    
    prizes = [50, 100, 250, 500, 1000, 5000]
    weights = [40, 30, 15, 10, 4, 1]
    prize = random.choices(prizes, weights=weights)[0]
    
    await db.update_balance(user['user_id'], prize)
    await db.set_time(user['user_id'], "last_wheel", now)
    
    await message.answer(f"🎡 Колесо остановилось на: **{prize} 🪙**!")

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user: return
    await message.answer(
        f"👤 **Профиль:** {user['username']}\n"
        f"💰 **Баланс:** `{user['balance']}` 🪙\n"
        f"📊 **Побед:** {user['wins']}",
        parse_mode="Markdown"
    )

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    users = await db.get_top()
    text = "🏆 **ТОП 10 МАЖОРОВ:**\n\n"
    for i, u in enumerate(users, 1):
        text += f"{i}. {u[0]} — `{u[1]}` 🪙\n"
    await message.answer(text, parse_mode="Markdown")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await db.setup()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("Бот казино успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
