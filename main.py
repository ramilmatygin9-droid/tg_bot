import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION

# --- НАСТРОЙКИ ---
TOKEN = "8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90"
ADMIN_ID = 8462392581 # Вставь свой ID
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище каналов (в памяти)
active_channels = {}

# Состояния для выбора канала
class PostState(StatesGroup):
    choosing_destination = State()

# 1. Ловим добавление в канал
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(event: types.ChatMemberUpdated):
    chat = event.chat
    active_channels[chat.id] = chat.title
    await bot.send_message(ADMIN_ID, f"✅ Добавлен в: {chat.title}\nТеперь я могу туда постить!")

# 2. Обработка входящего сообщения для рассылки
@dp.message(F.chat.type == 'private', F.from_user.id == ADMIN_ID)
async def handle_new_post(message: types.Message, state: FSMContext):
    if not active_channels:
        await message.answer("Сначала добавь меня в каналы и сделай админом.")
        return

    # Если канал всего один — шлем сразу
    if len(active_channels) == 1:
        c_id = list(active_channels.keys())[0]
        await message.copy_to(chat_id=c_id)
        await message.answer(f"✅ Отправлено в единственный канал: {active_channels[c_id]}")
        return

    # Если больше одного — предлагаем выбор
    # Сохраняем ID сообщения, которое нужно будет переслать
    await state.update_data(msg_to_copy=message.message_id)
    await state.set_state(PostState.choosing_destination)

    buttons = []
    for c_id, c_title in active_channels.items():
        buttons.append([InlineKeyboardButton(text=f"📤 {c_title}", callback_data=f"send_{c_id}")])
    
    buttons.append([InlineKeyboardButton(text="🌟 Во все каналы сразу", callback_data="send_all")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_post")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Куда отправить это сообщение?", reply_markup=kb)

# 3. Обработка выбора канала через кнопки
@dp.callback_query(PostState.choosing_destination, F.data.startswith("send_"))
async def process_callback_send(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_to_copy")
    target = callback.data.replace("send_", "")

    if target == "all":
        count = 0
        for c_id in active_channels.keys():
            try:
                await bot.copy_message(chat_id=c_id, from_chat_id=callback.message.chat.id, message_id=msg_id)
                count += 1
            except: pass
        await callback.message.edit_text(f"✅ Разослано в {count} канала(ов).")
    else:
        try:
            c_id = int(target)
            await bot.copy_message(chat_id=c_id, from_chat_id=callback.message.chat.id, message_id=msg_id)
            await callback.message.edit_text(f"✅ Отправлено в {active_channels[c_id]}")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")

    await state.clear()

# Отмена
@dp.callback_query(F.data == "cancel_post")
async def cancel_post(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


