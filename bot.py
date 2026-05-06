import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Твой токен (лучше использовать переменные окружения на Railway)
TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
# Твой Premium ID из скриншота
MONEY_EMOJI_ID = "5206599371868631162"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных
players = {}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в Шахту!**\n\n"
        "Команды:\n"
        "⛏ /mine — начать копать (5-12 сек)\n"
        "💰 /balance — проверить деньги",
        parse_mode="Markdown"
    )

@dp.message(Command("mine"))
async def mine_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in players:
        players[user_id] = 0

    wait_time = random.randint(5, 12)
    
    # Отправляем сообщение о начале работы
    status_msg = await message.answer(f"🚧 Копаем... Подожди {wait_time} сек.")
    
    # Имитация работы
    await bot.send_chat_action(message.chat.id, "typing")
    await asyncio.sleep(wait_time)
    
    # Генерируем награду
    reward = random.randint(100, 500)
    players[user_id] += reward
    
    # Удаляем старое сообщение и пишем результат с Премиум Эмодзи
    await status_msg.delete()
    
    # Используем HTML для отображения кастомного эмодзи
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_EMOJI_ID}">💵</tg-emoji> <b>Добыча завершена!</b>\n'
        f'━━━━━━━━━━━━━━\n'
        f'💵 Ты заработал: <b>{reward}</b> монет\n'
        f'📈 Твой баланс: <b>{players[user_id]}</b> монет',
        parse_mode="HTML"
    )

@dp.message(Command("balance"))
async def bal_cmd(message: types.Message):
    balance = players.get(message.from_user.id, 0)
    await message.answer(f"💰 Твой баланс: <b>{balance}</b> монет", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
