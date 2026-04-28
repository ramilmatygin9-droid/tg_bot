import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище для ID канала (можно сохранять в файл/БД)
current_channel_id = None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 Бот готов к работе!\n\n"
        "Команды:\n"
        "/join [ссылка] - вступить в канал по ссылке\n"
        "/set_channel [ID] - установить ID канала вручную\n"
        "/get_chat_id - показать ID текущего чата\n"
        "/play - запустить игру\n"
        "/status - проверить статус подключения к каналу"
    )

@dp.message(Command("play"))
async def cmd_play(message: types.Message):
    await message.answer("🎮 Запускаю игру... (или любое другое действие)")

@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    await message.answer(f"📱 ID этого чата: {message.chat.id}")

@dp.message(Command("status"))
async def check_status(message: types.Message):
    global current_channel_id
    if current_channel_id:
        try:
            chat = await bot.get_chat(current_channel_id)
            await message.answer(f"✅ Бот подключен к каналу: {chat.title}\nID: {current_channel_id}")
        except:
            await message.answer(f"⚠️ Бот не имеет доступа к каналу {current_channel_id}")
    else:
        await message.answer("❌ Канал не установлен. Используйте /join [ссылка] или /set_channel [ID]")

@dp.message(Command("join"))
async def join_channel(message: types.Message):
    global current_channel_id
    
    # Получаем ссылку из команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /join https://t.me/название_канала")
        return
    
    invite_link = args[1]
    
    try:
        # Пытаемся вступить в канал по ссылке
        await message.answer("🔄 Пытаюсь вступить в канал...")
        
        # Для вступления нужен другой подход - через invite link
        # Получаем информацию о канале по ссылке
        chat_info = await bot.get_chat(invite_link)
        
        # Бот должен быть добавлен как администратор или участник
        # Если ссылка пригласительная, можно попробовать присоединиться
        await bot.leave_chat(chat_info.id)  # сначала выходим если был
        await bot.join_chat(invite_link)  # пытаемся войти
        
        current_channel_id = chat_info.id
        await message.answer(
            f"✅ Бот успешно вступил в канал!\n"
            f"📌 Название: {chat_info.title}\n"
            f"🆔 ID: {current_channel_id}\n\n"
            f"⚠️ ВАЖНО: Добавьте бота в администраторы канала с правом отправки сообщений!"
        )
        
        # Отправляем тестовое сообщение в канал
        await bot.send_message(current_channel_id, "🤖 Бот подключен и готов к работе!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\n\n"
                           f"Возможные причины:\n"
                           f"1. Бот не имеет прав на вступление по ссылке\n"
                           f"2. Ссылка недействительна\n"
                           f"3. Бот уже в канале, но не администратор\n\n"
                           f"💡 Альтернатива: добавьте бота в канал вручную как администратора,\n"
                           f"затем используйте /set_channel [ID]")

@dp.message(Command("set_channel"))
async def set_channel(message: types.Message):
    global current_channel_id
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /set_channel -1001234567890")
        return
    
    try:
        channel_id = int(args[1])
        
        # Проверяем доступ к каналу
        chat = await bot.get_chat(channel_id)
        current_channel_id = channel_id
        
        await message.answer(
            f"✅ Канал установлен!\n"
            f"📌 Название: {chat.title}\n"
            f"🆔 ID: {channel_id}\n\n"
            f"⚠️ Убедитесь, что бот является администратором канала!"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\nПроверьте ID канала и права бота")

@dp.message()
async def forward_handler(message: types.Message):
    global current_channel_id
    
    # Пропускаем команды
    if message.text and message.text.startswith('/'):
        return
    
    # Проверяем, что канал установлен
    if not current_channel_id:
        await message.reply("❌ Канал не настроен! Используйте /join [ссылка] или /set_channel [ID]")
        return
    
    # Пропускаем пустые сообщения
    if not message.text and not message.photo and not message.video and not message.document:
        return

    try:
        # Отправляем сообщение напрямую в канал (а не пересылаем)
        if message.text:
            # Текстовое сообщение
            await bot.send_message(
                chat_id=current_channel_id,
                text=f"📨 От {message.from_user.first_name}:\n\n{message.text}"
            )
        elif message.photo:
            # Фото
            await bot.send_photo(
                chat_id=current_channel_id,
                photo=message.photo[-1].file_id,
                caption=f"📸 Фото от {message.from_user.first_name}"
            )
        elif message.video:
            # Видео
            await bot.send_video(
                chat_id=current_channel_id,
                video=message.video.file_id,
                caption=f"🎥 Видео от {message.from_user.first_name}"
            )
        else:
            # Другие типы сообщений
            await bot.forward_message(
                chat_id=current_channel_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        
        await message.reply("✅ Сообщение отправлено в канал!")
        
    except Exception as e:
        error_msg = str(e)
        if "chat not found" in error_msg or "bot is not a member" in error_msg:
            await message.reply(f"❌ Бот не имеет доступа к каналу!\n"
                              f"Убедитесь, что бот добавлен в канал как администратор.\n"
                              f"Используйте /status для проверки")
        else:
            await message.reply(f"❌ Ошибка: {error_msg}")

async def main():
    print("🤖 Бот запущен!")
    print("📌 Команды:")
    print("  /join [ссылка] - вступить в канал по ссылке")
    print("  /set_channel [ID] - установить ID канала")
    print("  /status - проверить статус")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
