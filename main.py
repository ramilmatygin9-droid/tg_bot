import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ТОЧНЫЙ ДИЗАЙН ---
DOTS = ". . . . . . . . . . . . . . . . . . ."
LINE = "────────────────"

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
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- МЕНЮ ВЫБОРА ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    name = call.from_user.first_name
    
    # Конфиги для меню каждой игры
    configs = {
        "football": {
            "text": f"**{name}**\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**",
            "kb": [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")],
                   [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")]]
        },
        "basketball": {
            "text": f"**{name}**\n🏀 **Баскет · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**",
            "kb": [[InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")],
                   [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")]]
        },
        "darts": {
            "text": f"**{name}**\n🎯 **Дартс · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**\n\n🔰 **Коэффициенты:**\n┕ 🔴 Красное (x1.94)\n┕ ⚪ Белое (x2.9)\n┕ 🎯 Центр (x5.8)\n┕ 😯 Мимо (x5.8)",
            "kb": [[InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
                   [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"), InlineKeyboardButton(text="😯 Мимо", callback_data="bet_darts_miss")]]
        },
        "bowling": {
            "text": f"**{name}**\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**\n\n🔰 **Коэффициенты:**\n┕ 🎳 Страйк (x4.8)\n┕ 🎳 Сбить кегли (x1.4)",
            "kb": [[InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="🎳 Сбить кегли", callback_data="bet_bowling_any")]]
        },
        "dice": {
            "text": f"**{name}**\n🎲 **Кубик · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**\n\n🔰 **Коэффициенты:**\n┕ 🔢 Чет / Нечет (x1.9)\n┕ 📈 Бол / Мен (x2.0)",
            "kb": [[InlineKeyboardButton(text="🔢 Четное", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔢 Нечетное", callback_data="bet_dice_odd")],
                   [InlineKeyboardButton(text="📈 Больше 3", callback_data="bet_dice_big"), InlineKeyboardButton(text="📉 Меньше 4", callback_data="bet_dice_small")]]
        },
        "slots": {
            "text": f"**{name}**\n🎰 **Слоты · удачи!**\n{DOTS}\n💸 **Ставка: 10 m¢**",
            "kb": [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]
        }
    }
    
    config = configs[game]
    config["kb"].append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(config["text"], reply_markup=InlineKeyboardMarkup(inline_keyboard=config["kb"]), parse_mode="Markdown")

# --- ЛОГИКА И ОФОРМЛЕНИЕ РЕЗУЛЬТАТА ---
@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type, choice = data[1], data[2]
    
    # Кидаем дайс
    emoji = {"football":"⚽","darts":"🎯","bowling":"🎳","basketball":"🏀","dice":"🎲","slots":"🎰"}[game_type]
    msg = await call.message.answer_dice(emoji=emoji)
    
    await asyncio.sleep(4)
    val = msg.dice.value
    win = False
    coef = 0

    # Проверка выигрыша и коэфы
    if game_type == "football":
        win = (choice == "goal" and val >= 3) or (choice == "miss" and val < 3)
        coef = 1.6 if choice == "goal" else 2.4
    elif game_type == "basketball":
        win = (choice == "goal" and val >= 4) or (choice == "miss" and val < 4)
        coef = 1.6 if choice == "goal" else 2.4
    elif game_type == "bowling":
        win = (choice == "strike" and val == 6) or (choice == "any" and val > 1)
        coef = 4.8 if choice == "strike" else 1.4
    elif game_type == "darts":
        if choice == "center": win = (val == 6); coef = 5.8
        elif choice == "red": win = (val in [4, 5]); coef = 1.94
        elif choice == "white": win = (val in [2, 3]); coef = 2.9
        elif choice == "miss": win = (val == 1); coef = 5.8
    elif game_type == "dice":
        if choice == "even": win = (val % 2 == 0); coef = 1.9
        elif choice == "odd": win = (val % 2 != 0); coef = 1.9
        elif choice == "big": win = (val > 3); coef = 2.0
        elif choice == "small": win = (val < 4); coef = 2.0
    elif game_type == "slots":
        win = (val in [1, 22, 43, 64]); coef = 10.0

    # ТЕКСТ РЕЗУЛЬТАТА КАК НА ВИДЕО
    status = "🥳 **Победа!**" if win else "❌ **Проигрыш**"
    profit = int(10 * coef) if win else 0
    res_emoji = "✅" if win else "❌"
    
    result_text = (
        f"**{call.from_user.first_name}**\n"
        f"{status}\n"
        f"{LINE}\n"
        f"💰 Выигрыш: {profit} m¢ {res_emoji}\n"
        f"🎲 Результат: {val}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 играть снова", callback_data=f"prep_{game_type}")],
        [InlineKeyboardButton(text="◀️ в меню", callback_data="to_main")]
    ])

    await call.message.answer(result_text, reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"**{message.from_user.first_name}**\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"**{call.from_user.first_name}**\nВыбирай игру:", reply_markup=main_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
