import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'
# Попробуем оба варианта ID. Если не сработает один, подставится другой.
CHANNEL_ID = -1008462392581 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Привет! Твой ID: {message.from_user.id}. Отправь мне что-то, и я попробую кинуть в канал.")

@dp.message()
async def forward_handler(message: types.Message):
    try:
        # Пробуем переслать
        await bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.reply("Отправил!")
    except Exception as e:
        await message.reply(f"Не удалось отправить. Ошибка: {e}\n\nПопробуй проверить, является ли бот администратором канала.")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
