import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION

# --- НАСТРОЙКИ ---
TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ"
ADMIN_ID = 8462392581 
CHANNELS_FILE = "channels.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class PostState(StatesGroup):
    choosing_destination = State()

# Функции для сохранения каналов в файл
def save_channels(data):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

active_channels = load_channels()

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(event: types.ChatMemberUpdated):
    chat = event.chat
    active_channels[str(chat.id)] = chat.title
    save_channels(active_channels)
    await bot.send_message(ADMIN_ID, f"✅ Добавлен в: {chat.title}")

@dp.message(F.chat.type == 'private', F.from_user.id == ADMIN_ID)
async def handle_new_post(message: types.Message, state: FSMContext):
    if not active_channels:
        await message.answer("Сначала добавь меня в каналы.")
        return

    # Сохраняем ID сообщения для копирования (вместе с премиум эмодзи)
    await state.update_data(msg_id=message.message_id)
    
    if len(active_channels) == 1:
        c_id = list(active_channels.keys())[0]
        await message.send_copy(chat_id=c_id)
        await message.answer("✅ Отправлено!")
        return

    await state.set_state(PostState.choosing_destination)
    buttons = []
    for c_id, c_title in active_channels.items():
        buttons.append([InlineKeyboardButton(text=f"📤 {c_title}", callback_data=f"send_{c_id}")])
    
    buttons.append([InlineKeyboardButton(text="🌟 Во все сразу", callback_data="send_all")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])

    await message.answer("Куда шлем? (Премиум эмодзи поддерживаются)", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(PostState.choosing_destination, F.data.startswith("send_"))
async def process_send(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_id")
    target = callback.data.replace("send_", "")

    if target == "all":
        for c_id in active_channels.keys():
            try:
                await bot.copy_message(chat_id=c_id, from_chat_id=callback.message.chat.id, message_id=msg_id)
            except: pass
        await callback.message.edit_text("✅ Разослано везде!")
    else:
        try:
            await bot.copy_message(chat_id=target, from_chat_id=callback.message.chat.id, message_id=msg_id)
            await callback.message.edit_text(f"✅ Отправлено в канал!")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")

    await state.clear()

@dp.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

