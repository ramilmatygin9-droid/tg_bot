import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'
CHANNEL_ID = -1008462392581 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработка команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Бот готов к работе!")

# Обработка команды /play
@dp.message(Command("play"))
async def cmd_play(message: types.Message):
    await message.answer("Запускаю игру... (или любое другое действие)")
    # Здесь можно добавить логику твоей игры

# Пересылка всех остальных сообщений в канал
@dp.message()
async def forward_handler(message: types.Message):
    # Проверяем, что это не команда (чтобы не пересылать /play в канал)
    if message.text and message.text.startswith('/'):
        return 

    try:
        await bot.forward_message(
            chat_id=CHANNEL_ID, 
            from_chat_id=message.chat.id, 
            message_id=message.message_id
        )
        await message.reply("Сообщение переслано в канал!")
    except Exception as e:
        await message.reply(f"Ошибка при пересылке: {e}")

async def main():
    print("Бот запущен и ждет команд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
