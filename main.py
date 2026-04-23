import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
ADMIN_TOKEN = "8610751877:AAG4eHS_knuJ-tFuVVfSIXkOC2AJxIdC990"
MY_ID = 8462392581  # Твой ID

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

# Данные пользователя
user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}

# --- ГЛАВНОЕ МЕНЮ (КАК НА СКРИНШОТЕ 16:19) ---
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
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="withdraw")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 Баланс: **{user_data['balance']} руб.**\n"
        f"💸 Ставка: **{user_data['bet']} руб.**\n\n"
        f"👇 *Выбери игру и начинай!*"
    )
    await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- ПРОФИЛЬ ---
@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = (
        f"👤 **{call.from_user.first_name}** | ID: `{call.from_user.id}`\n"
        f"🎖 Ваш уровень: **{user_data['level']}**\n"
        f"💰 Баланс: **{user_data['balance']} руб.**\n"
        f"────────────────\n"
        f"Удачи в играх!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- КУБИК (КАК НА СКРИНШОТЕ 15:16) ---
@dp.callback_query(F.data == "prep_dice")
async def prep_dice(call: types.CallbackQuery):
    text = (
        f"🍀 **Кубик · выбери режим!**\n"
        f".................................\n"
        f"💸 Ставка: **{user_data['bet']} руб.**"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
        [InlineKeyboardButton(text="4", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6", callback_data="bet_dice_v6")],
        [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")],
        [InlineKeyboardButton(text="〓 Равно 3 x5.8", callback_data="bet_dice_eq3")],
        [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="bet_dice_big"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="bet_dice_small")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- БОУЛИНГ (КАК НА СКРИНШОТЕ 14:57) ---
@dp.callback_query(F.data == "prep_bowling")
async def prep_bowling(call: types.CallbackQuery):
    text = (
        f"🎳 **Боулинг · выбери исход!**\n"
        f".................................\n"
        f"💸 Ставка: **{user_data['bet']} руб.**\n\n"
        f"📈 **Коэффициенты:**\n"
        f"┕ 1 - 5 кегли (x5.8)\n"
        f"┕ 🎳 Страйк (x5.8)\n"
        f"┕ 😟 Мимо (x5.8)"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="3 кегли", callback_data="bet_bowling_3")],
        [InlineKeyboardButton(text="4 кегли", callback_data="bet_bowling_4"), InlineKeyboardButton(text="5 кегель", callback_data="bet_bowling_5")],
        [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- ЛОГИКА ОБРАБОТКИ (БЕЗ ИЗМЕНЕНИЙ) ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = (
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 Баланс: **{user_data['balance']} руб.**\n"
        f"💸 Ставка: **{user_data['bet']} руб.**\n\n"
        f"👇 *Выбери игру и начинай!*"
    )
    await call.message.edit_text(text, reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "withdraw")
async def withdraw_handler(call: types.CallbackQuery):
    await call.answer("💳 Раздел в разработке!", show_alert=True)

@dp.callback_query(F.data == "ask_help")
async def ask_help(call: types.CallbackQuery):
    user_support_state[call.from_user.id] = True
    await call.message.answer("📝 Опишите вашу проблему:")
    await call.answer()

@dp.message()
async def handle_messages(message: types.Message):
    if user_support_state.get(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{message.from_user.id}")]])
        await admin_bot.send_message(MY_ID, f"🆘 Тикет от {message.from_user.first_name}:\n{message.text}", reply_markup=kb)
        await message.answer("✅ Отправлено администратору.")
        del user_support_state[message.from_user.id]

async def main():
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
