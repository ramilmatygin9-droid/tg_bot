import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# ТВОЙ ТОКЕН
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(message: types.Message):
        await message.answer("✅ Бот работает! Я тебя вижу.")

    print("ПОПЫТКА ПОДКЛЮЧЕНИЯ К TELEGRAM...")
    try:
        user = await bot.get_me()
        print(f"УСПЕХ! Бот @{user.username} онлайн.")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")

if __name__ == "__main__":
    asyncio.run(main())
