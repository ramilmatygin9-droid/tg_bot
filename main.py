import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот работает! Используй /test")

@dp.message(Command("test"))
async def test(message: types.Message):
    await message.answer("🔍 Проверка...")
    
    # Проверка 1: бот запущен
    await message.answer("✅ Бот работает")
    
    # Проверка 2: пробуем отправить в канал
    try:
        # ВСТАВЬ СВОЙ ID КАНАЛА СЮДА:
        TEST_CHANNEL = -1008462392581  # ЗАМЕНИ НА СВОЙ!
        
        await bot.send_message(TEST_CHANNEL, "Тест от бота!")
        await message.answer("✅ Сообщение отправлено в канал!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\n\nПроверь:\n1. Бот админ канала?\n2. ID канала правильный?")

async def main():
    print("Бот запущен. Напиши /start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
