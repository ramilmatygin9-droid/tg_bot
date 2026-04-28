import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION

TOKEN = "8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временное хранилище (в идеале использовать базу данных)
# Формат: {chat_id: chat_title}
active_channels = {}

# 1. Отслеживаем добавление бота в новые каналы
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added_to_channel(event: types.ChatMemberUpdated):
    chat = event.chat
    if chat.type in ["channel", "supergroup"]:
        active_channels[chat.id] = chat.title
        print(f"Меня добавили в: {chat.title} (ID: {chat.id})")

# 2. Отслеживаем удаление бота из каналов
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def bot_removed_from_channel(event: types.ChatMemberUpdated):
    chat_id = event.chat.id
    if chat_id in active_channels:
        del active_channels[chat_id]

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Просмотр каналов", callback_data="list_channels")]
    ])
    await message.answer("Привет! Добавь меня в канал как админа, и я смогу туда постить.\nНажми кнопку ниже, чтобы управлять списком.", reply_markup=kb)

# 3. Список каналов с кнопками управления
@dp.callback_query(F.data == "list_channels")
async def show_channels(callback: types.CallbackQuery):
    if not active_channels:
        await callback.answer("Я еще не добавлен ни в один канал!", show_alert=True)
        return

    text = "📢 Список каналов, где я нахожусь:\n\n"
    buttons = []
    
    for c_id, c_title in active_channels.items():
        # Кнопка для удаления (выхода из канала)
        buttons.append([
            InlineKeyboardButton(text=f"❌ Покинуть {c_title}", callback_data=f"leave_{c_id}")
        ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)

# 4. Обработка нажатия на кнопку "Удалить/Покинуть"
@dp.callback_query(F.data.startswith("leave_"))
async def leave_channel_process(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    try:
        await bot.leave_chat(channel_id)
        if channel_id in active_channels:
            del active_channels[channel_id]
        await callback.answer("Бот успешно вышел из канала!")
        await show_channels(callback) # Обновляем список
    except Exception as e:
        await callback.answer(f"Ошибка: {e}")

# 5. Пересылка сообщений во ВСЕ подключенные каналы
@dp.message()
async def post_to_all(message: types.Message):
    if message.chat.type == 'private' and active_channels:
        sent_count = 0
        for c_id in active_channels.keys():
            try:
                await message.copy_to(chat_id=c_id)
                sent_count += 1
            except:
                continue
        await message.answer(f"✅ Отправлено в {sent_count} канал(ов).")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


