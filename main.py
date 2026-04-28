import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'
# ⚠️ ЗАМЕНИТЕ НА ПРАВИЛЬНЫЙ ID КАНАЛА (получите через /get_chat_id)
CHANNEL_ID = -1008462392581  # ❌ Скорее всего неправильный

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Бот готов к работе!")

@dp.message(Command("play"))
async def cmd_play(message: types.Message):
    await message.answer("Запускаю игру... (или любое другое действие)")

# Добавьте эту команду для получения ID чата
@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    await message.answer(f"ID этого чата: {message.chat.id}")

@dp.message()
async def forward_handler(message: types.Message):
    # Пропускаем команды
    if message.text and message.text.startswith('/'):
        return
    
    # Пропускаем служебные сообщения
    if not message.text and not message.photo and not message.video:
        return

    try:
        await bot.forward_message(
            chat_id=CHANNEL_ID, 
            from_chat_id=message.chat.id, 
            message_id=message.message_id
        )
        await message.reply("✅ Сообщение переслано в канал!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}\nПроверьте, что бот администратор канала и ID правильный")

async def main():
    print("Бот запущен. Напишите /get_chat_id в чате/канале, куда добавили бота")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
