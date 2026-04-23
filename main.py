import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ТОЧНЫЙ ДИЗАЙН ИЗ ФОТО ---
DOTS = ". . . . . . . . . . . . . . . . . . ."

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

# --- МЕНЮ ПОДГОТОВКИ ---

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    name = call.from_user.first_name
    
    # Стилизация под скриншоты
    if game == "football":
        kb = [
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")],
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"**{name}**\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**"

    elif game == "basketball":
        kb = [
            [InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")],
            [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"**{name}**\n🏀 **Баскет · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**"

    elif game == "darts":
        kb = [
            [InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"),
             InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
            [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center"),
             InlineKeyboardButton(text="😯 Мимо", callback_data="bet_darts_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = (f"**{name}**\n🎯 **Дартс · выбери исход!**\n{DOTS}\n"
                f"💸 **Ставка: 10 m¢**\n\n"
                f"🔰 **Коэффициенты:**\n"
                f"┕ 🔴 Красное (x1.94)\n"
                f"┕ ⚪ Белое (x2.9)\n"
                f"┕ 🎯 Центр (x5.8)\n"
                f"┕ 😯 Мимо (x5.8)")

    elif game == "bowling":
        kb = [
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"),
             InlineKeyboardButton(text="🎳 Сбить кегли", callback_data="bet_bowling_any")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = (f"**{name}**\n🎳 **Боулинг · выбери исход!**\n{DOTS}\n"
                f"💸 **Ставка: 10 m¢**\n\n"
                f"🔰 **Коэффициенты:**\n"
                f"┕ 🎳 Страйк (x4.8)\n"
                f"┕ 🎳 Сбить кегли (x1.4)")

    elif game == "dice":
        kb = [
            [InlineKeyboardButton(text="🔢 Четное", callback_data="bet_dice_even"), 
             InlineKeyboardButton(text="🔢 Нечетное", callback_data="bet_dice_odd")],
            [InlineKeyboardButton(text="📈 Больше 3", callback_data="bet_dice_big"), 
             InlineKeyboardButton(text="📉 Меньше 4", callback_data="bet_dice_small")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = (f"**{name}**\n🎲 **Кубик · выбери исход!**\n{DOTS}\n"
                f"💸 **Ставка: 10 m¢**\n\n"
                f"🔰 **Коэффициенты:**\n"
                f"┕ 🔢 Чет / Нечет (x1.9)\n"
                f"┕ 📈 Бол / Мен (x2.0)")

    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")], [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]
        text = f"**{name}**\n🎰 **Слоты · удачи!**\n{DOTS}\n💸 **Ставка: 10 m¢**"

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА ИГРЫ ---

@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]
    choice = data[2]
    
    emoji = {"football":"⚽","darts":"🎯","bowling":"🎳","basketball":"🏀","dice":"🎲","slots":"🎰"}[game_type]
    msg = await call.message.answer_dice(emoji=emoji)
    
    await asyncio.sleep(4)
    val = msg.dice.value
    win = False

    # Условия побед (базовые)
    if game_type == "football": win = (choice == "goal" and val >= 3) or (choice == "miss" and val < 3)
    elif game_type == "basketball": win = (choice == "goal" and val >= 4) or (choice == "miss" and val < 4)
    elif game_type == "bowling": win = (choice == "strike" and val == 6) or (choice == "any" and val > 1)
    elif game_type == "dice": 
        if choice == "even": win = (val % 2 == 0)
        elif choice == "odd": win = (val % 2 != 0)
        elif choice == "big": win = (val > 3)
        elif choice == "small": win = (val < 4)
    elif game_type == "darts":
        if choice == "center": win = (val == 6)
        elif choice == "red": win = (val in [4, 5])
        elif choice == "white": win = (val in [2, 3])
        elif choice == "miss": win = (val == 1)
    elif game_type == "slots": win = (val in [1, 22, 43, 64])

    res_title = "🥳 **Победа!**" if win else "❌ **Проигрыш**"
    
    final_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 играть снова", callback_data=f"prep_{game_type}")],
        [InlineKeyboardButton(text="◀️ в меню", callback_data="to_main")]
    ])

    await call.message.answer(f"**{call.from_user.first_name}**\n{res_title}\n────────────────\nРезультат: {val}", 
                               reply_markup=final_kb, parse_mode="Markdown")

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
