import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация
TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"

# Твои ID премиум эмодзи из скриншотов
PICKAXE_ID = "5197371802136892976"  # Кирка
MONEY_BAG_ID = "5206223871467878339" # Мешок денег
CASH_ID = "5206599371868631162"      # Пачка денег

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных игроков (в памяти)
players = {}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Добро пожаловать на золотую жилу!</b>\n\n'
        f'Используй /mine, чтобы начать копать.',
        parse_mode="HTML"
    )

@dp.message(Command("mine"))
async def mine_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in players:
        players[user_id] = 0

    # Случайное время копания от 5 до 12 секунд
    wait_time = random.randint(5, 12)
    
    # Отправляем сообщение с таймером и киркой
    status_msg = await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n'
        f'⏳ Осталось: <b>{wait_time}</b> сек.', 
        parse_mode="HTML"
    )
    
    # Живой отсчет времени
    for seconds_left in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(
                f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n'
                f'⏳ Осталось: <b>{seconds_left}</b> сек.',
                parse_mode="HTML"
            )
        except Exception:
            pass # На случай, если сообщение удалят во время отсчета
    
    # Награда
    reward = random.randint(300, 900)
    players[user_id] += reward
    
    # Удаляем таймер и выводим результат
    await status_msg.delete()
    
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Богатый улов!</b>\n'
        f'━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji> Вы нашли: <b>{reward}</b> монет\n'
        f'🏦 Ваш баланс: <b>{players[user_id]}</b>',
        parse_mode="HTML"
    )

@dp.message(Command("balance"))
async def bal_cmd(message: types.Message):
    balance = players.get(message.from_user.id, 0)
    await message.answer(
        f'💰 Баланс: <b>{balance}</b> <tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji>',
        parse_mode="HTML"
    )

async def main():
    print("Бот с премиум-эмодзи и таймером запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
