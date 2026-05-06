import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Твой токен (ОПАСНО: лучше использовать переменные окружения на Railway)
TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Простая база данных игроков
players = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in players:
        players[user_id] = {"name": message.from_user.first_name, "balance": 100}
    
    await message.answer(
        f"🎮 Привет, {message.from_user.first_name}!\n\n"
        "Ты в игре. Твой начальный баланс: 100 монет.\n"
        "Команды:\n"
        "💰 /work — заработать монеты\n"
        "🏆 /top — список богачей"
    )

@dp.message(Command("work"))
async def work_handler(message: types.Message):
    user_id = message.from_user.id
    import random
    
    if user_id not in players:
        players[user_id] = {"name": message.from_user.first_name, "balance": 0}
    
    earn = random.randint(10, 50)
    players[user_id]["balance"] += earn
    
    await message.reply(f"⛏ Ты поработал и получил {earn} монет!\nБаланс: {players[user_id]['balance']}")

@dp.message(Command("top"))
async def top_handler(message: types.Message):
    if not players:
        return await message.answer("Игроков пока нет!")
    
    # Сортируем по балансу
    sorted_players = sorted(players.values(), key=lambda x: x['balance'], reverse=True)[:10]
    
    text = "🏆 **Топ богачей чата:**\n\n"
    for i, p in enumerate(sorted_players, 1):
        text += f"{i}. {p['name']} — {p['balance']} 💰\n"
    
    await message.answer(text, parse_mode="Markdown")

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
