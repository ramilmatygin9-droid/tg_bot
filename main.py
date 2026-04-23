import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
# Токен бота (замени на свой)
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Данные для профиля (в памяти, сбрасываются при перезапуске)
user_data = {
    "balance": 1000,
    "level": 1
}

LINE = "────────────────"

# --- КЛАВИАТУРЫ ---
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
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="withdraw")]
    ])

# --- ПРОФИЛЬ ---
@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    name = call.from_user.first_name
    uid = call.from_user.id
    text = (
        f"👤 **{name}** | ID: `{uid}`\n"
        f"🎖 Ваш уровень: **{user_data['level']}**\n"
        f"💰 Баланс: **{user_data['balance']} руб.**\n"
        f"{LINE}\nУдачи в играх!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- ПОДГОТОВКА СТАВКИ (ИСПРАВЛЕННЫЕ МЕНЮ) ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    header = f"👤 **Рамиль**\n"
    footer = f"{LINE}\n💸 **Ставка: 10 m¢**"
    kb = []
    text = ""

    if game == "dice":
        text = f"{header}🍀 **Кубик · выбери режим!**\n{footer}"
        kb = [
            [InlineKeyboardButton(text="1", callback_data="bet_dice_1"), InlineKeyboardButton(text="2", callback_data="bet_dice_2"), InlineKeyboardButton(text="3", callback_data="bet_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="bet_dice_4"), InlineKeyboardButton(text="5", callback_data="bet_dice_5"), InlineKeyboardButton(text="6", callback_data="bet_dice_6")],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")],
            [InlineKeyboardButton(text="〓 Равно 3 x5.8", callback_data="bet_dice_v3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="bet_dice_big"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="bet_dice_small")]
        ]
    elif game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")]]
        text = f"{header}⚽ **Футбол · выбери исход!**\n{footer}"
    elif game == "basketball":
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")],
              [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")]]
        text = f"{header}🏀 **Баскетбол · выбери исход!**\n{footer}"
    elif game == "bowling":
        kb = [
            [InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="3 кегли", callback_data="bet_bowling_3")],
            [InlineKeyboardButton(text="4 кегли", callback_data="bet_bowling_4"), InlineKeyboardButton(text="5 кегель", callback_data="bet_bowling_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")]
        ]
        text = f"{header}🎳 **Боулинг · выбери исход!**\n{footer}"
    elif game == "darts":
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_darts_miss")]]
        text = f"{header}🎯 **Дартс · выбери исход!**\n{footer}"
    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]
        text = f"{header}🎰 **Слоты**\n{footer}"

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- СИСТЕМНОЕ ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
