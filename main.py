import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from typing import Dict, List

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище для каналов (в реальном проекте используйте БД)
user_channels: Dict[int, List[dict]] = {}  # {user_id: [{"id": channel_id, "title": title, "type": "channel/group"}]}
current_channel: Dict[int, int] = {}  # {user_id: current_channel_id}

# Клавиатуры
def get_channels_keyboard(user_id: int):
    """Создает клавиатуру со списком каналов пользователя"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    channels = user_channels.get(user_id, [])
    if not channels:
        return None
    
    buttons = []
    for ch in channels:
        emoji = "📢" if ch["type"] == "channel" else "👥"
        buttons.append([KeyboardButton(text=f"{emoji} {ch['title']}")])
    
    buttons.append([KeyboardButton(text="🔄 Обновить список")])
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 **Бот для управления каналами и группами**\n\n"
        "**Доступные команды:**\n"
        "/add_channel [ссылка или ID] - добавить канал/группу\n"
        "/my_channels - показать все мои каналы\n"
        "/select_channel - выбрать канал для отправки\n"
        "/channels_info - подробная информация о каналах\n"
        "/send [текст] - отправить в выбранный канал\n"
        "/leave [ID] - покинуть канал\n"
        "/get_chat_id - узнать ID текущего чата\n\n"
        "💡 **Как добавить бота в канал:**\n"
        "1. Сделайте бота администратором канала\n"
        "2. Используйте /add_channel с ID канала\n"
        "3. Или просто перешлите любое сообщение из канала боту",
        parse_mode="Markdown"
    )

@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    """Узнать ID любого чата"""
    chat_id = message.chat.id
    chat_type = message.chat.type
    chat_title = message.chat.title or "Личный чат"
    
    await message.answer(
        f"📊 **Информация о чате:**\n"
        f"Название: {chat_title}\n"
        f"ID: `{chat_id}`\n"
        f"Тип: {chat_type}\n\n"
        f"💡 Используйте этот ID: `/add_channel {chat_id}`",
        parse_mode="Markdown"
    )

@dp.message(Command("add_channel"))
async def add_channel(message: types.Message):
    """Добавить канал или группу"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ **Укажите ссылку или ID канала**\n\n"
            "Примеры:\n"
            "/add_channel -1001234567890\n"
            "/add_channel @username\n"
            "/add_channel https://t.me/username",
            parse_mode="Markdown"
        )
        return
    
    channel_input = args[1].strip()
    user_id = message.from_user.id
    
    try:
        # Пытаемся получить информацию о чате
        chat = None
        
        # Если передан ID (начинается с -100 для каналов или просто число)
        if channel_input.lstrip('-').isdigit():
            chat_id = int(channel_input)
            chat = await bot.get_chat(chat_id)
        else:
            # Пробуем как юзернейм или ссылку
            if channel_input.startswith('https://t.me/'):
                username = channel_input.split('/')[-1]
            elif channel_input.startswith('@'):
                username = channel_input[1:]
            else:
                username = channel_input
            
            chat = await bot.get_chat(f"@{username}")
        
        # Сохраняем информацию о канале
        if user_id not in user_channels:
            user_channels[user_id] = []
        
        # Проверяем, не добавлен ли уже
        ch_data = {
            "id": chat.id,
            "title": chat.title or "Без названия",
            "type": "channel" if chat.type == "channel" else "group",
            "username": chat.username
        }
        
        # Проверяем дубликаты
        if not any(ch["id"] == chat.id for ch in user_channels[user_id]):
            user_channels[user_id].append(ch_data)
            
            # Автоматически делаем этот канал текущим
            current_channel[user_id] = chat.id
            
            await message.answer(
                f"✅ **Канал добавлен!**\n\n"
                f"📌 Название: {chat.title}\n"
                f"🆔 ID: `{chat.id}`\n"
                f"📢 Тип: {chat.type}\n\n"
                f"🎯 Теперь это текущий канал для отправки\n"
                f"Используйте /send [текст] для отправки сообщения",
                parse_mode="Markdown"
            )
            
            # Тестовое сообщение в канал
            try:
                await bot.send_message(chat.id, f"🤖 Бот подключен к каналу {chat.title}!")
                await message.answer("✅ Тестовое сообщение отправлено в канал!")
            except Exception as e:
                await message.answer(f"⚠️ Не удалось отправить тестовое сообщение. Убедитесь, что бот администратор канала.\nОшибка: {e}")
        else:
            await message.answer("ℹ️ Этот канал уже добавлен")
            
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка:** {str(e)}\n\n"
            f"Возможные причины:\n"
            f"• Бот не добавлен в этот канал/группу\n"
            f"• Неверный ID или ссылка\n"
            f"• Бот не является администратором\n\n"
            f"💡 **Решение:** Добавьте бота в канал как администратора,\n"
            f"затем используйте /get_chat_id в том канале",
            parse_mode="Markdown"
        )

@dp.message(Command("my_channels"))
async def list_channels(message: types.Message):
    """Показать все каналы пользователя"""
    user_id = message.from_user.id
    channels = user_channels.get(user_id, [])
    
    if not channels:
        await message.answer(
            "📭 **У вас нет добавленных каналов**\n\n"
            "Используйте /add_channel [ID или ссылка] для добавления",
            parse_mode="Markdown"
        )
        return
    
    text = "📋 **Ваши каналы и группы:**\n\n"
    for i, ch in enumerate(channels, 1):
        emoji = "📢" if ch["type"] == "channel" else "👥"
        username_info = f" (@{ch['username']})" if ch.get("username") else ""
        current_mark = " ✅ **ТЕКУЩИЙ**" if current_channel.get(user_id) == ch["id"] else ""
        
        text += f"{emoji} **{i}. {ch['title']}**{current_mark}\n"
        text += f"   🆔 ID: `{ch['id']}`{username_info}\n\n"
    
    text += "💡 Используйте /select_channel для смены текущего канала"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("select_channel"))
async def select_channel(message: types.Message):
    """Выбрать канал для отправки"""
    user_id = message.from_user.id
    channels = user_channels.get(user_id, [])
    
    if not channels:
        await message.answer("❌ У вас нет добавленных каналов. Используйте /add_channel")
        return
    
    keyboard = get_channels_keyboard(user_id)
    if keyboard:
        await message.answer(
            "🎯 **Выберите канал для отправки сообщений:**\n\n"
            "Нажмите на кнопку с названием канала",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

@dp.message(Command("channels_info"))
async def channels_info(message: types.Message):
    """Подробная информация о каналах"""
    user_id = message.from_user.id
    channels = user_channels.get(user_id, [])
    
    if not channels:
        await message.answer("📭 Нет добавленных каналов")
        return
    
    text = "🔍 **Детальная информация:**\n\n"
    for ch in channels:
        try:
            # Получаем актуальную информацию
            chat = await bot.get_chat(ch["id"])
            admins = await bot.get_chat_administrators(ch["id"])
            bot_is_admin = any(admin.user.id == bot.id for admin in admins)
            
            text += f"📌 **{ch['title']}**\n"
            text += f"   ID: `{ch['id']}`\n"
            text += f"   Тип: {chat.type}\n"
            text += f"   Участников: {chat.get_members_count() if hasattr(chat, 'get_members_count') else '?'}\n"
            text += f"   Бот админ: {'✅ Да' if bot_is_admin else '❌ Нет'}\n\n"
        except:
            text += f"⚠️ **{ch['title']}** - нет доступа\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("send"))
async def send_to_channel(message: types.Message):
    """Отправить сообщение в выбранный канал"""
    user_id = message.from_user.id
    
    # Проверяем, выбран ли канал
    channel_id = current_channel.get(user_id)
    if not channel_id:
        await message.answer(
            "❌ **Не выбран канал для отправки**\n\n"
            "Используйте /add_channel [ID] или /select_channel",
            parse_mode="Markdown"
        )
        return
    
    # Получаем текст сообщения
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "✏️ **Укажите текст для отправки**\n\n"
            f"Пример: `/send Привет, канал!`\n\n"
            f"Текущий канал: {await get_channel_name(user_id)}",
            parse_mode="Markdown"
        )
        return
    
    text = args[1]
    
    try:
        await bot.send_message(channel_id, text)
        await message.answer(f"✅ **Сообщение отправлено!**\n\n📨 Текст: {text[:100]}...")
    except Exception as e:
        await message.answer(f"❌ **Ошибка отправки:** {e}\n\nПроверьте права бота в канале")

@dp.message(Command("leave"))
async def leave_channel(message: types.Message):
    """Покинуть канал"""
    args = message.text.split()
    user_id = message.from_user.id
    
    if len(args) < 2:
        await message.answer("❌ Укажите ID канала: /leave -1001234567890")
        return
    
    try:
        channel_id = int(args[1])
        
        # Удаляем из списка
        if user_id in user_channels:
            user_channels[user_id] = [ch for ch in user_channels[user_id] if ch["id"] != channel_id]
        
        # Если это был текущий канал, сбрасываем
        if current_channel.get(user_id) == channel_id:
            del current_channel[user_id]
        
        # Пытаемся выйти из канала
        await bot.leave_chat(channel_id)
        
        await message.answer(f"✅ Покинул канал {channel_id}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def get_channel_name(user_id: int) -> str:
    """Получить название текущего канала"""
    channel_id = current_channel.get(user_id)
    if not channel_id:
        return "не выбран"
    
    channels = user_channels.get(user_id, [])
    for ch in channels:
        if ch["id"] == channel_id:
            return ch["title"]
    return str(channel_id)

# Обработка кнопок выбора канала
@dp.message()
async def handle_channel_selection(message: types.Message):
    """Обработка выбора канала из меню"""
    user_id = message.from_user.id
    
    # Проверяем, есть ли каналы
    channels = user_channels.get(user_id, [])
    if not channels:
        return
    
    text = message.text
    
    if text == "🔄 Обновить список":
        await select_channel(message)
        return
    
    if text == "❌ Отмена":
        await message.answer("❌ Отменено", reply_markup=types.ReplyKeyboardRemove())
        return
    
    # Ищем выбранный канал по названию (убираем эмодзи)
    for ch in channels:
        button_text = f"{'📢' if ch['type']=='channel' else '👥'} {ch['title']}"
        if text == button_text:
            current_channel[user_id] = ch["id"]
            await message.answer(
                f"✅ **Текущий канал изменен на:** {ch['title']}\n\n"
                f"Теперь используйте /send [текст] для отправки сообщений",
                parse_mode="Markdown",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return

# Обработка пересланных сообщений (автоматическое добавление канала)
@dp.message()
async def auto_add_from_forward(message: types.Message):
    """Автоматическое добавление канала при пересылке из него"""
    if message.forward_from_chat:
        user_id = message.from_user.id
        chat = message.forward_from_chat
        
        if user_id not in user_channels:
            user_channels[user_id] = []
        
        ch_data = {
            "id": chat.id,
            "title": chat.title or "Без названия",
            "type": "channel" if chat.type == "channel" else "group",
            "username": chat.username
        }
        
        if not any(ch["id"] == chat.id for ch in user_channels[user_id]):
            user_channels[user_id].append(ch_data)
            if user_id not in current_channel:
                current_channel[user_id] = chat.id
            
            await message.answer(
                f"✅ **Автоматически добавлен канал:** {chat.title}\n"
                f"ID: `{chat.id}`\n\n"
                f"Теперь это текущий канал. Используйте /send для отправки",
                parse_mode="Markdown"
            )

async def main():
    print("🤖 Бот запущен!")
    print("📌 Функции:")
    print("  • Добавление каналов по ID/ссылке")
    print("  • Просмотр всех каналов")
    print("  • Выбор канала для отправки")
    print("  • Отправка сообщений в выбранный канал")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
