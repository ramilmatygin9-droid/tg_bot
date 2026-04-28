import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION

# --- НАСТРОЙКИ ---
TOKEN = "8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90" # Твой токен
ADMIN_ID = 8462392581  # Твой ID
CHANNELS_FILE = "channels.json"

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

class PostState(StatesGroup):
    choosing_destination = State()

# --- РАБОТА С КАНАЛАМИ ---
def save_channels(data):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    # Если файла нет, создаем список с твоим основным каналом
    return {"-1003756091662": "Основной канал"}

active_channels = load_channels()

# --- ПРОВЕРКА ДОСТУПА ---
@dp.message(F.chat.type == 'private', F.from_user.id != ADMIN_ID)
async def access_denied(message: types.Message):
    await message.answer("⛔ Доступ только для владельца.")

# --- ДОБАВЛЕНИЕ В НОВЫЙ КАНАЛ ---
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(event: types.ChatMemberUpdated):
    chat = event.chat
    active_channels[str(chat.id)] = chat.title
    save_channels(active_channels)
    await bot.send_message(ADMIN_ID, f"🔔 Добавлен в: {chat.title}\nID: `{chat.id}`")

# --- СТАРТ ---
@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def start_cmd(message: types.Message):
    await message.answer("👋 Бот готов! Присылай текст или котиков (Premium-эмодзи), и я опубликую их.")

# --- ОБРАБОТКА ПОСТА ---
@dp.message(F.chat.type == 'private', F.from_user.id == ADMIN_ID)
async def handle_new_post(message: types.Message, state: FSMContext):
    if not active_channels:
        await message.answer("❌ Нет каналов в списке.")
        return

    await state.update_data(saved_msg=message)
    
    if len(active_channels) == 1:
        c_id = list(active_channels.keys())[0]
        try:
            await message.send_copy(chat_id=c_id)
            await message.answer("✅ Опубликовано!")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        return

    await state.set_state(PostState.choosing_destination)
    buttons = []
    for c_id, c_title in active_channels.items():
        buttons.append([InlineKeyboardButton(text=f"📤 {c_title}", callback_data=f"send_{c_id}")])
    
    buttons.append([InlineKeyboardButton(text="🌟 Во все сразу", callback_data="send_all")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])

    await message.answer("Куда отправить?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# --- ОТПРАВКА ---
@dp.callback_query(PostState.choosing_destination, F.from_user.id == ADMIN_ID)
async def process_send(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    saved_msg: types.Message = data.get("saved_msg")
    target = callback.data.replace("send_", "")

    if target == "all":
        for c_id in active_channels.keys():
            try: await saved_msg.send_copy(chat_id=c_id)
            except: pass
        await callback.message.edit_text("✅ Разослано везде!")
    elif target == "cancel":
        await callback.message.edit_text("Отменено.")
    else:
        try:
            await saved_msg.send_copy(chat_id=target)
            await callback.message.edit_text(f"✅ Готово!")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")

    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
