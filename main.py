import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Простое хранилище (для теста)
user_channel = {}  # {user_id: channel_id}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 Бот готов!\n\n"
        "📌 Команды:\n"
        "/set_channel [ID] - установить канал\n"
        "/send [текст] - отправить сообщение\n"
        "/get_id - узнать ID этого чата"
    )

@dp.message(Command("get_id"))
async def get_id(message: types.Message):
    await message.answer(f"ID этого чата: `{message.chat.id}`", parse_mode="Markdown")

@dp.message(Command("set_channel"))
async def set_channel(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Пример: /set_channel -1001234567890")
        return
    
    try:
        channel_id = int(args[1])
        user_channel[message.from_user.id] = channel_id
        
        # Проверяем доступ
        chat = await bot.get_chat(channel_id)
        await message.answer(
            f"✅ Канал установлен: {chat.title}\n"
            f"ID: `{channel_id}`\n\n"
            f"Теперь используй /send [текст]"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\n\nБот должен быть администратором канала!")

@dp.message(Command("send"))
async def send_message(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_channel:
        await message.answer("❌ Сначала установи канал: /set_channel [ID]")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Пример: /send Привет, канал!")
        return
    
    channel_id = user_channel[user_id]
    text = args[1]
    
    try:
        await bot.send_message(channel_id, text)
        await message.answer(f"✅ Отправлено в канал!\n\nТекст: {text}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message()
async def forward_all(message: types.Message):
    """Пересылает все сообщения в установленный канал"""
    user_id = message.from_user.id
    
    if user_id not in user_channel:
        return
    
    channel_id = user_channel[user_id]
    
    # Пропускаем команды
    if message.text and message.text.startswith('/'):
        return
    
    try:
        # Отправляем в канал
        sender = message.from_user.first_name
        
        if message.text:
            await bot.send_message(channel_id, f"📨 От {sender}:\n\n{message.text}")
        elif message.photo:
            await bot.send_photo(channel_id, message.photo[-1].file_id, caption=f"📸 От {sender}")
        elif message.video:
            await bot.send_video(channel_id, message.video.file_id, caption=f"🎥 От {sender}")
        else:
            await bot.forward_message(channel_id, message.chat.id, message.message_id)
        
        await message.reply("✅ Переслано в канал!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
