import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
ADMIN_TOKEN = "8610751877:AAG4eHS_knuJ-tFuVVfSIXkOC2AJxIdC990"
MY_ID = 846239258 

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}
change_bet_state = {}

LINE = "────────────────"

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="prep_basketball"), InlineKeyboardButton(text="⚽", callback_data="prep_football"), InlineKeyboardButton(text="🎯", callback_data="prep_darts"), InlineKeyboardButton(text=" bowling", callback_data="prep_bowling"), InlineKeyboardButton(text="🎲", callback_data="prep_dice"), InlineKeyboardButton(text="🎰", callback_data="prep_slots")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"), InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Если старт нажали в ИГРОВОМ боте
    if message.bot.token == GAME_TOKEN:
        await message.answer(f"🎮 **ИГРОВОЙ БОТ ЗАПУЩЕН**\n💰 Баланс: {user_data['balance']}", reply_markup=main_kb(), parse_mode="Markdown")
    
    # Если старт нажали в БОТЕ ПОМОЩИ (как на твоем скрине)
    elif message.bot.token == ADMIN_TOKEN:
        if message.from_user.id == MY_ID:
            await message.answer("🛠 **АДМИН-ПАНЕЛЬ АКТИВИРОВАНА**\nТеперь сюда будут приходить вопросы пользователей.")
        else:
            await message.answer("Это бот поддержки. Пишите в основной игровой бот.")

# --- ЛОГИКА СООБЩЕНИЙ ---
@dp.message()
async def handle_messages(message: types.Message):
    uid = message.from_user.id
    
    if message.bot.token == GAME_TOKEN:
        if change_bet_state.get(uid):
            if message.text.isdigit():
                user_data["bet"] = int(message.text)
                change_bet_state[uid] = False
                await message.answer(f"✅ Ставка: {user_data['bet']}", reply_markup=main_kb())
            return

        if user_support_state.get(uid):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{uid}")]])
            sms = f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n👤 От: {message.from_user.first_name}\n🆔 ID: `{uid}`\n✉️ Текст: {message.text}"
            
            try:
                await admin_bot.send_message(MY_ID, sms, reply_markup=kb, parse_mode="Markdown")
                await message.answer("✅ Сообщение отправлено в поддержку!")
            except Exception as e:
                await message.answer("❌ Ошибка отправки админу.")
            user_support_state[uid] = False

    elif message.bot.token == ADMIN_TOKEN and uid == MY_ID:
        if admin_reply_state.get(MY_ID):
            target = admin_reply_state[MY_ID]
            try:
                await bot.send_message(target, f"✉️ **Ответ техподдержки:**\n\n{message.text}")
                await message.answer(f"✅ Отправлено пользователю `{target}`")
                del admin_reply_state[MY_ID]
            except:
                await message.answer("❌ Ошибка отправки.")

# --- CALLBACKS ---
@dp.callback_query(F.data == "change_bet")
async def bet_init(call: types.CallbackQuery):
    change_bet_state[call.from_user.id] = True
    await call.message.answer("✏️ Введите сумму ставки:")
    await call.answer()

@dp.callback_query(F.data == "ask_help")
async def help_init(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 Напишите ваш вопрос:")
    await call.answer()

@dp.callback_query(F.data.startswith("adm_reply_"))
async def adm_reply_cb(call: types.CallbackQuery):
    admin_reply_state[MY_ID] = call.data.split("_")[2]
    await call.message.answer("⌨️ Пишите ответ:")
    await call.answer()

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
