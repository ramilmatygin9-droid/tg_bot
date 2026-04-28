import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище
user_channel = {}  # {user_id: {"id": channel_id, "name": channel_name}}

# Главное меню
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Найти канал")],
        [KeyboardButton(text="📋 Текущий канал")],
        [KeyboardButton(text="❌ Сбросить")]
    ],
    resize_keyboard=True
)

@dp.message(Command("startchat"))
async def start_chat(message: types.Message):
    await message.answer(
        "🤖 **Бот для отправки сообщений в канал**\n\n"
        "🔍 **Как найти канал:**\n"
        "1. Нажми «📢 Найти канал»\n"
        "2. Введи название канала или @username\n"
        "3. Выбери нужный канал из результатов\n"
        "4. Пиши любой текст - он уйдет в канал!\n\n"
        "⚠️ **Важно:** Бот должен быть администратором канала!",
        parse_mode="Markdown",
        reply_markup=menu
    )

@dp.message(lambda m: m.text == "📢 Найти канал")
async def find_channel_prompt(message: types.Message):
    await message.answer(
        "🔍 **Введи название канала или ссылку:**\n\n"
        "Примеры:\n"
        "• `новости`\n"
        "• `@durov`\n"
        "• `https://t.me/durov`\n\n"
        "Бот найдет похожие каналы!",
        parse_mode="Markdown"
    )

@dp.message(lambda m: m.text == "📋 Текущий канал")
async def show_current_channel(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_channel:
        await message.answer("❌ Канал не выбран. Нажми «📢 Найти канал»")
        return
    
    try:
        chat = await bot.get_chat(user_channel[user_id]["id"])
        await message.answer(
            f"✅ **Текущий канал:** {chat.title}\n\n"
            f"Теперь просто пиши текст - он уйдет сюда!",
            parse_mode="Markdown"
        )
    except:
        await message.answer("❌ Ошибка: бот потерял доступ к каналу")

@dp.message(lambda m: m.text == "❌ Сбросить")
async def reset_channel(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_channel:
        del user_channel[user_id]
    await message.answer("✅ Канал сброшен. Нажми «📢 Найти канал» для выбора нового")

# Поиск канала по тексту
@dp.message()
async def search_and_send(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    
    # Если это просто текст (не команда и не кнопка)
    if text.startswith('/'):
        return
    
    if text in ["📢 Найти канал", "📋 Текущий канал", "❌ Сбросить"]:
        return
    
    # Если канал уже выбран - отправляем сообщение
    if user_id in user_channel:
        try:
            await bot.send_message(
                user_channel[user_id]["id"],
                f"📝 **{message.from_user.first_name}:**\n\n{text}"
            )
            await message.answer("✅ Сообщение отправлено в канал!")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}\n\nВозможно, бот не админ канала")
        return
    
    # Если канал не выбран - ищем канал по тексту
    await message.answer("🔍 Ищу каналы...")
    
    try:
        # Пробуем найти по юзернейму
        search_text = text.strip()
        if search_text.startswith('@'):
            search_text = search_text[1:]
        if search_text.startswith('https://t.me/'):
            search_text = search_text.split('/')[-1]
        
        # Пытаемся получить канал по юзернейму
        try:
            chat = await bot.get_chat(f"@{search_text}")
            if chat.type in ["channel", "supergroup"]:
                # Создаем кнопки для выбора
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Выбрать этот канал", callback_data=f"select_{chat.id}")],
                        [InlineKeyboardButton(text="🔍 Искать другой", callback_data="search_again")]
                    ]
                )
                
                await message.answer(
                    f"📢 **Найден канал:**\n\n"
                    f"📌 Название: {chat.title}\n"
                    f"👥 Участников: {chat.get_members_count() if hasattr(chat, 'get_members_count') else '?'}\n"
                    f"🔗 Ссылка: @{chat.username if chat.username else 'нет'}\n\n"
                    f"Выбрать этот канал?",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                return
        except:
            pass
        
        # Если не нашли по точному совпадению, показываем инструкцию
        await message.answer(
            "❌ **Канал не найден!**\n\n"
            "Проверь правильность названия или используй:\n"
            "• Полную ссылку: https://t.me/название\n"
            "• Юзернейм: @название\n\n"
            "💡 **Важно:** Бот должен быть добавлен в канал как администратор!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")

# Обработка выбора канала
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    if data.startswith("select_"):
        channel_id = int(data.split("_")[1])
        
        try:
            chat = await bot.get_chat(channel_id)
            
            # Сохраняем канал
            user_channel[user_id] = {
                "id": channel_id,
                "name": chat.title
            }
            
            await callback.message.edit_text(
                f"✅ **Канал выбран:** {chat.title}\n\n"
                f"Теперь просто пиши любой текст - он автоматически отправится в этот канал!\n\n"
                f"Текущий канал можно посмотреть кнопкой «📋 Текущий канал»",
                parse_mode="Markdown"
            )
            await callback.answer(f"Выбран канал: {chat.title}")
            
        except Exception as e:
            await callback.answer(f"Ошибка: {e}", show_alert=True)
    
    elif data == "search_again":
        await callback.message.edit_text(
            "🔍 **Введи название канала или ссылку для поиска:**\n\n"
            "Примеры:\n"
            "• `новости`\n"
            "• `@durov`\n"
            "• `https://t.me/durov`"
        )
        await callback.answer()

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "📖 **Инструкция:**\n\n"
        "1. Нажми «📢 Найти канал»\n"
        "2. Введи название или ссылку на канал\n"
        "3. Выбери канал из результатов\n"
        "4. Пиши любой текст - он отправится в канал!\n\n"
        "⚠️ **Важно:** Бот должен быть администратором канала!",
        parse_mode="Markdown"
    )

async def main():
    print("🤖 Бот запущен!")
    print("Напиши /startchat")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
