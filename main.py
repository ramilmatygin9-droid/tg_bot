import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище
user_channels = {}  # {user_id: [{"id": id, "name": name}]}
selected_channel = {}  # {user_id: channel_id}

# Главное меню
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Выбрать канал")],
            [KeyboardButton(text="➕ Добавить канал"), KeyboardButton(text="📋 Мои каналы")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Меню выбора канала
def channel_menu(user_id):
    channels = user_channels.get(user_id, [])
    if not channels:
        return None
    
    keyboard = []
    for ch in channels:
        keyboard.append([KeyboardButton(text=f"📢 {ch['name']}")])
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(Command("startchat"))
async def start_chat(message: types.Message):
    await message.answer(
        "🤖 **Добро пожаловать!**\n\n"
        "Я бот для отправки сообщений в Telegram каналы.\n\n"
        "📌 **Как пользоваться:**\n"
        "1️⃣ Добавьте канал через кнопку «➕ Добавить канал»\n"
        "2️⃣ Выберите канал через «📢 Выбрать канал»\n"
        "3️⃣ Просто напишите любой текст - он отправится в выбранный канал!\n\n"
        "👇 **Выберите действие:**",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.message(lambda message: message.text == "➕ Добавить канал")
async def add_channel_button(message: types.Message):
    await message.answer(
        "📝 **Как добавить канал:**\n\n"
        "1. Добавьте бота в канал как АДМИНИСТРАТОРА\n"
        "2. Перешлите ЛЮБОЕ сообщение из канала сюда\n"
        "3. Или отправьте ID канала: `/add -1001234567890`\n\n"
        "💡 **Узнать ID канала:**\n"
        "Напишите `/getid` в вашем канале",
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "📢 Выбрать канал")
async def select_channel_button(message: types.Message):
    user_id = message.from_user.id
    channels = user_channels.get(user_id, [])
    
    if not channels:
        await message.answer(
            "❌ **У вас нет добавленных каналов!**\n\n"
            "Нажмите «➕ Добавить канал» и следуйте инструкции",
            parse_mode="Markdown"
        )
        return
    
    menu = channel_menu(user_id)
    await message.answer(
        "🎯 **Выберите канал для отправки сообщений:**\n\n"
        "Просто нажмите на нужный канал",
        parse_mode="Markdown",
        reply_markup=menu
    )

@dp.message(lambda message: message.text == "📋 Мои каналы")
async def my_channels(message: types.Message):
    user_id = message.from_user.id
    channels = user_channels.get(user_id, [])
    
    if not channels:
        await message.answer("📭 У вас нет добавленных каналов")
        return
    
    text = "📋 **Ваши каналы:**\n\n"
    for i, ch in enumerate(channels, 1):
        current = " ✅ ТЕКУЩИЙ" if selected_channel.get(user_id) == ch['id'] else ""
        text += f"{i}. {ch['name']}{current}\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(lambda message: message.text == "🔙 Назад")
@dp.message(lambda message: message.text == "❌ Отмена")
async def back_button(message: types.Message):
    await message.answer("🔙 Возврат в главное меню", reply_markup=main_menu())

# Добавление канала через пересылку
@dp.message(lambda message: message.forward_from_chat is not None)
async def add_channel_from_forward(message: types.Message):
    user_id = message.from_user.id
    chat = message.forward_from_chat
    
    # Проверяем, что это канал
    if chat.type not in ["channel", "supergroup"]:
        await message.answer("❌ Это не канал, отправьте сообщение ИЗ канала")
        return
    
    # Сохраняем канал
    if user_id not in user_channels:
        user_channels[user_id] = []
    
    # Проверяем дубликаты
    if not any(c['id'] == chat.id for c in user_channels[user_id]):
        user_channels[user_id].append({
            'id': chat.id,
            'name': chat.title
        })
        
        # Если это первый канал, делаем его выбранным
        if user_id not in selected_channel:
            selected_channel[user_id] = chat.id
        
        await message.answer(
            f"✅ **Канал добавлен!**\n\n"
            f"📌 Название: {chat.title}\n"
            f"🆔 ID: `{chat.id}`\n\n"
            f"Теперь выберите его в меню «📢 Выбрать канал»\n"
            f"и напишите любой текст для отправки!",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        await message.answer(f"ℹ️ Канал {chat.title} уже добавлен")

# Добавление канала через команду
@dp.message(Command("add"))
async def add_channel_command(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Пример: /add -1001234567890")
        return
    
    try:
        channel_id = int(args[1])
        chat = await bot.get_chat(channel_id)
        
        user_id = message.from_user.id
        if user_id not in user_channels:
            user_channels[user_id] = []
        
        if not any(c['id'] == channel_id for c in user_channels[user_id]):
            user_channels[user_id].append({
                'id': channel_id,
                'name': chat.title
            })
            
            if user_id not in selected_channel:
                selected_channel[user_id] = channel_id
            
            await message.answer(
                f"✅ Канал {chat.title} добавлен!",
                reply_markup=main_menu()
            )
        else:
            await message.answer("ℹ️ Канал уже добавлен")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\n\nБот должен быть администратором канала!")

@dp.message(Command("getid"))
async def get_id(message: types.Message):
    await message.answer(f"🆔 ID этого чата: `{message.chat.id}`", parse_mode="Markdown")

# Обработка выбора канала из меню
@dp.message(lambda message: message.text and message.text.startswith("📢 "))
async def handle_channel_selection(message: types.Message):
    user_id = message.from_user.id
    channel_name = message.text.replace("📢 ", "")
    
    channels = user_channels.get(user_id, [])
    for ch in channels:
        if ch['name'] == channel_name:
            selected_channel[user_id] = ch['id']
            await message.answer(
                f"✅ **Выбран канал:** {ch['name']}\n\n"
                f"Теперь просто напишите любой текст, и он отправится в этот канал!\n\n"
                f"💡 Совет: нажмите «❌ Отмена» чтобы убрать меню",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
            return

# Обработка обычных текстовых сообщений (отправка в выбранный канал)
@dp.message()
async def send_to_selected_channel(message: types.Message):
    user_id = message.from_user.id
    
    # Пропускаем если текст - это команда или кнопка меню
    if message.text.startswith('/'):
        return
    
    # Проверяем, выбран ли канал
    if user_id not in selected_channel:
        await message.answer(
            "❌ **Сначала выберите канал!**\n\n"
            "Нажмите «📢 Выбрать канал» в меню",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return
    
    channel_id = selected_channel[user_id]
    text = message.text
    
    try:
        await bot.send_message(
            channel_id,
            f"📨 **Сообщение от {message.from_user.first_name}:**\n\n{text}"
        )
        await message.answer(
            f"✅ **Сообщение отправлено в канал!**\n\n"
            f"📝 Ваш текст: {text[:100]}...",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка отправки:** {e}\n\n"
            f"Убедитесь, что:\n"
            f"1. Бот администратор канала\n"
            f"2. Канал существует\n"
            f"3. Вы выбрали правильный канал",
            parse_mode="Markdown"
        )

async def main():
    print("🤖 Бот запущен!")
    print("Напишите /startchat")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
