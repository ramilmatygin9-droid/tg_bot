import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЭЛЕМЕНТЫ ДИЗАЙНА ---
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

# --- МЕНЮ ПОДГОТОВКИ ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    name = call.from_user.first_name
    
    if game == "bowling":
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
        
    elif game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")],
              [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]
        text = f"**{name}**\n⚽ **Футбол · выбери исход!**\n{DOTS}\n💸 **Ставка: 10 m¢**"

    # (Остальные игры оформляются так же)
    else:
        kb = [[InlineKeyboardButton(text="🎮 Начать", callback_data=f"bet_{game}_any")],
              [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]
        text = f"**{name}**\n🎮 **Игра началась!**\n{DOTS}\n💸 **Ставка: 10 m¢**"

    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- РЕЗУЛЬТАТ ---
@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type, choice = data[1], data[2]
    
    await call.message.delete()
    
    emoji = {"football":"⚽","darts":"🎯","bowling":"🎳","basketball":"🏀","dice":"🎲","slots":"🎰"}[game_type]
    msg = await call.bot.send_dice(call.message.chat.id, emoji=emoji)
    
    await asyncio.sleep(4)
    val = msg.dice.value
    win = False
    coef = 0.0

    if game_type == "bowling":
        is_strike = (val == 6)
        win = (choice == "strike" and is_strike) or (choice == "any" and val > 1 and not is_strike)
        coef = 4.8 if choice == "strike" else 1.4
    
    # ... логика для других игр (аналогично предыдущим) ...

    status = "🥳 **Победа!**" if win else "❌ **Проигрыш**"
    profit = int(10 * coef) if win else 0
    
    result_text = (
        f"**{call.from_user.first_name}**\n"
        f"{status}\n"
        f"{LINE}\n"
        f"💰 Выигрыш: {profit} m¢ {'✅' if win else '❌'}\n"
        f"🎲 Результат: {val}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 играть снова", callback_data=f"prep_{game_type}"),
         InlineKeyboardButton(text="◀️ в меню", callback_data="to_main")]
    ])

    await msg.reply(result_text, reply_markup=kb, parse_mode="Markdown")

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
