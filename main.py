import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Твои данные
API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'
CHANNEL_ID = -1008462392581  # Добавил -100, так как это стандарт для каналов

# Логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Бот запущен. Отправь сообщение, и я перешлю его в канал.")

@dp.message()
async def forward_to_channel(message: types.Message):
    try:
        # Метод forward сохраняет информацию об авторе
        await message.forward(chat_id=CHANNEL_ID)
        await message.reply("✅ Отправлено в канал")
    except Exception as e:
        # Если возникнет ошибка (например, бот не админ в канале)
        await message.reply(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
