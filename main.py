import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ ШАБЛОНОВ ---

def get_header(user):
    return (f"👤 {user.first_name}\n"
            f"💰 Баланс: 1000 m¢\n"
            f"────────────────")

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

# --- МЕНЮ ВЫБОРА (КАК НА СКРИНШОТЕ) ---

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    header = f"👤 {call.from_user.first_name}\n"
    
    if game == "football":
        kb = [
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")],
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"{header}⚽ Футбол · выбери исход!\n. . . . . . . . . . . . . . . . . . .\n💸 Ставка: 10 m¢"
        
    elif game == "basketball":
        kb = [
            [InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")],
            [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"{header}🏀 Баскет · выбери исход!\n. . . . . . . . . . . . . . . . . . .\n💸 Ставка: 10 m¢"

    elif game == "darts":
        kb = [
            [InlineKeyboardButton(text="🎯 Центр - x5.0", callback_data="bet_darts_6")],
            [InlineKeyboardButton(text="🔴 Красное - x2.0", callback_data="bet_darts_red")],
            [InlineKeyboardButton(text="⚪ Белое - x2.0", callback_data="bet_darts_white")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"{header}🎯 Дартс · выбери сектор!\n. . . . . . . . . . . . . . . . . . .\n💸 Ставка: 10 m¢"

    elif game == "bowling":
        kb = [
            [InlineKeyboardButton(text="🎳 Страйк - x5.0", callback_data="bet_bowling_6")],
            [InlineKeyboardButton(text="🎳 Сбил - x1.4", callback_data="bet_bowling_any")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"{header}🎳 Боулинг · выбери исход!\n. . . . . . . . . . . . . . . . . . .\n💸 Ставка: 10 m¢"

    elif game == "dice":
        kb = [
            [InlineKeyboardButton(text="🔢 Четное x1.9", callback_data="bet_dice_even"), 
             InlineKeyboardButton(text="🔢 Нечетное x1.9", callback_data="bet_dice_odd")],
            [InlineKeyboardButton(text="📉 Больше 3 x2.0", callback_data="bet_dice_big"), 
             InlineKeyboardButton(text="📈 Меньше 4 x2.0", callback_data="bet_dice_small")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"{header}🎲 Кубик · выбери исход!\n. . . . . . . . . . . . . . . . . . .\n💸 Ставка: 10 m¢"

    elif game == "slots":
        kb = [
            [InlineKeyboardButton(text="🎰 Крутить - 10 m¢", callback_data="bet_slots_any")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ]
        text = f"{header}🎰 Слоты · удачи!\n. . . . . . . . . . . . . . . . . . .\n💸 Ставка: 10 m¢"

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА ИГРЫ ---

@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]
    choice = data[2]
    
    emoji_map = {"football": "⚽", "basketball": "🏀", "darts": "🎯", "bowling": "🎳", "dice": "🎲", "slots": "🎰"}
    msg = await call.message.answer_dice(emoji=emoji_map[game_type])
    
    await asyncio.sleep(4)
    val = msg.dice.value
    win = False
    coef = 1.0

    # Проверка условий
    if game_type == "football":
        is_goal = val >= 3
        win = (choice == "goal" and is_goal) or (choice == "miss" and not is_goal)
        coef = 1.6 if choice == "goal" else 2.4
    elif game_type == "basketball":
        is_goal = val >= 4
        win = (choice == "goal" and is_goal) or (choice == "miss" and not is_goal)
        coef = 1.6 if choice == "goal" else 2.4
    elif game_type == "darts":
        if choice == "6": win = (val == 6); coef = 5.0
        elif choice == "red": win = (val in [4, 5]); coef = 2.0
        elif choice == "white": win = (val in [2, 3]); coef = 2.0
    elif game_type == "bowling":
        if choice == "6": win = (val == 6); coef = 5.0
        else: win = (val > 1); coef = 1.4
    elif game_type == "dice":
        if choice == "even": win = (val % 2 == 0); coef = 1.9
        elif choice == "odd": win = (val % 2 != 0); coef = 1.9
        elif choice == "big": win = (val > 3); coef = 2.0
        elif choice == "small": win = (val < 4); coef = 2.0
    elif game_type == "slots":
        win = (val in [1, 22, 43, 64]); coef = 10.0

    res_emoji = "✅" if win else "❌"
    profit = int(10 * coef) if win else 0
    
    final_text = (
        f"👤 {call.from_user.first_name}\n"
        f"{'🥳 Победа!' if win else '😟 Проигрыш'}\n"
        f"────────────────\n"
        f"💰 Выигрыш: {profit} m¢ {res_emoji}\n"
        f"🎲 Результат: {val}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Играть снова", callback_data=f"prep_{game_type}")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")]
    ])

    await call.message.answer(final_text, reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(get_header(message.from_user), reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(get_header(call.from_user), reply_markup=main_kb())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
