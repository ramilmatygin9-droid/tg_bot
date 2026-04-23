import asyncio
import random
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования (поможет увидеть ошибки в консоли)
logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
# Игровой бот (новый чистый токен)
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 
# Админ-бот (вернул токен по твоей просьбе)
ADMIN_TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"
MY_ID = 846239258 

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

user_data = {"balance": 1000, "bet": 10}
user_support_state = {}
admin_reply_state = {}
change_bet_state = {}

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
            InlineKeyboardButton(text="🎳", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰", callback_data="prep_slots")
        ],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ]
    ])

# Команды /start и /play
@dp.message(Command("start", "play"))
async def cmd_start_play(message: types.Message):
    if message.bot.token == GAME_TOKEN:
        now = datetime.now().strftime("%H:%M:%S")
        text = (
            f"🎮 **БОТ ЗАПУЩЕН!**\n\n"
            f"💰 Баланс: **{user_data['balance']} руб.**\n"
            f"💸 Ставка: **{user_data['bet']} руб.**\n"
            f"🕒 Время: `{now}`\n\n"
            f"Выбери игру ниже 👇"
        )
        await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

@dp.message()
async def handle_messages(message: types.Message):
    uid = message.from_user.id
    
    # Логика для игрового бота
    if message.bot.token == GAME_TOKEN:
        if change_bet_state.get(uid):
            if message.text.isdigit():
                user_data["bet"] = int(message.text)
                change_bet_state[uid] = False
                await message.answer(f"✅ Ставка: {user_data['bet']} руб.", reply_markup=main_kb())
            return
        
        if user_support_state.get(uid):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{uid}")]])
            sms = f"🆘 **ВОПРОС**\n👤 От: {message.from_user.full_name}\n🆔 ID: `{uid}`\n✉️: {message.text}"
            try:
                await admin_bot.send_message(MY_ID, sms, reply_markup=kb, parse_mode="Markdown")
                await message.answer("✅ Отправлено поддержке!")
            except Exception as e:
                await message.answer(f"❌ Ошибка отправки админу. Проверьте, запущен ли админ-бот.")
                logging.error(f"Ошибка админ-бота: {e}")
            user_support_state[uid] = False

    # Логика для админ-бота
    elif message.bot.token == ADMIN_TOKEN and uid == MY_ID:
        if admin_reply_state.get(MY_ID):
            target = admin_reply_state[MY_ID]
            try:
                await bot.send_message(target, f"✉️ **Ответ техподдержки:**\n\n{message.text}")
                await message.answer(f"✅ Ответ доставлен пользователю {target}")
                del admin_reply_state[MY_ID]
            except Exception as e:
                await message.answer("❌ Не удалось отправить ответ.")
                logging.error(f"Ошибка ответа пользователю: {e}")

@dp.callback_query(F.data == "ask_help")
async def help_init(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 Напишите ваше сообщение поддержке:")
    await call.answer()

@dp.callback_query(F.data.startswith("adm_reply_"))
async def adm_reply_callback(call: types.CallbackQuery):
    admin_reply_state[MY_ID] = call.data.split("_")[2]
    await call.message.answer("⌨️ Введите ответ для игрока:")
    await call.answer()

@dp.callback_query(F.data == "change_bet")
async def bet_init(call: types.CallbackQuery):
    change_bet_state[call.from_user.id] = True
    await call.message.answer("✏️ Введите сумму ставки:")
    await call.answer()

@dp.callback_query(F.data == "profile")
async def profile_call(call: types.CallbackQuery):
    await call.answer(f"👤 {call.from_user.first_name}\n💰 Баланс: {user_data['balance']} руб.", show_alert=True)

async def main():
    # Очистка очереди обновлений
    await bot.delete_webhook(drop_pending_updates=True)
    await admin_bot.delete_webhook(drop_pending_updates=True)
    print(">>> БОТЫ ЗАПУЩЕНЫ <<<")
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
