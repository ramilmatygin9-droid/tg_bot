import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ОФОРМЛЕНИЕ) ---

def get_user_header(user):
    # Как на видео: Имя, ID и уровень
    return f"👤 {user.first_name} (ID: `{user.id}`)\n🏆 Ваш уровень: 1\n💰 Баланс: 250 m¢\n"

def get_main_menu():
    kb = [
        [
            InlineKeyboardButton(text="🏀", callback_data="game_basketball"), 
            InlineKeyboardButton(text="⚽", callback_data="game_football"),
            InlineKeyboardButton(text="🎯", callback_data="game_darts"),
            InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="game_dice"),
            InlineKeyboardButton(text="🎰", callback_data="game_slots")
        ],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast_menu"), 
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- МИНЫ (MINES) 5x5 ---
def get_mines_field(opened_cells=None, exploded=False):
    if opened_cells is None: opened_cells = []
    kb = []
    for y in range(5):
        row = []
        for x in range(5):
            cell_id = f"{x}_{y}"
            if cell_id in opened_cells:
                text = "💥" if exploded and cell_id == opened_cells[-1] else "💎"
            else:
                text = "🔹"
            row.append(InlineKeyboardButton(text=text, callback_data=f"mine_click_{cell_id}"))
        kb.append(row)
    kb.append([InlineKeyboardButton(text="📥 Забрать выигрыш", callback_data="mine_stop")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="fast_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"{get_user_header(message.from_user)}\nВыбирай игру:", reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_user_header(call.from_user)}\nВыбирай игру:", reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "fast_menu")
async def fast_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🚀 Краш", callback_data="game_crash"), InlineKeyboardButton(text="💣 Мины", callback_data="game_mines")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette"), InlineKeyboardButton(text="💰 Монетка", callback_data="game_coin")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await call.message.edit_text(f"{get_user_header(call.from_user)}\n🚀 **Быстрые игры**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ИГРА МИНЫ (MINES) ---
user_mines = {} # В идеале хранить в БД, тут для примера

@dp.callback_query(F.data == "game_mines")
async def start_mines(call: types.CallbackQuery):
    # Генерируем 3 случайные мины
    mines = []
    while len(mines) < 3:
        m = f"{random.randint(0,4)}_{random.randint(0,4)}"
        if m not in mines: mines.append(m)
    
    user_mines[call.from_user.id] = {"mines": mines, "opened": [], "steps": 0}
    
    await call.message.edit_text(
        f"{get_user_header(call.from_user)}\n💣 **Мины: игра идет...**\nНайди алмазы и не взорвись!",
        reply_markup=get_mines_field(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("mine_click_"))
async def click_mine(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_mines: return
    
    cell = call.data.replace("mine_click_", "")
    game = user_mines[user_id]
    
    if cell in game["opened"]: return

    if cell in game["mines"]:
        game["opened"].append(cell)
        await call.message.edit_text(f"{get_user_header(call.from_user)}\n💥 **БУМ! Вы взорвались!**", 
                                     reply_markup=get_mines_field(game["opened"], True), parse_mode="Markdown")
        del user_mines[user_id]
    else:
        game["opened"].append(cell)
        game["steps"] += 1
        coef = round(1.2 + (game["steps"] * 0.3), 2)
        await call.message.edit_text(f"{get_user_header(call.from_user)}\n💎 **Алмаз найден!**\n📈 Текущий коэф: x{coef}", 
                                     reply_markup=get_mines_field(game["opened"]), parse_mode="Markdown")

@dp.callback_query(F.data == "mine_stop")
async def stop_mine(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_mines or user_mines[user_id]["steps"] == 0: return
    
    steps = user_mines[user_id]["steps"]
    win = int(10 * (1.2 + (steps * 0.3)))
    await call.message.answer(f"💰 **Выигрыш: {win} m¢!**\nВы успешно забрали деньги.", reply_markup=get_main_menu(), parse_mode="Markdown")
    del user_mines[user_id]

# --- ИГРА КРАШ (CRASH) ---
@dp.callback_query(F.data == "game_crash")
async def crash_start(call: types.CallbackQuery):
    kb = []
    for row in [["x1.2", "x2.0", "x5.0"], ["x10.0", "x50.0", "x100.0"]]:
        kb.append([InlineKeyboardButton(text=m, callback_data=f"cr_bet_{m[1:]}") for m in row])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="fast_menu")])
    
    await call.message.edit_text(f"{get_user_header(call.from_user)}\n🚀 **Краш — выбери цель!**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cr_bet_"))
async def play_crash(call: types.CallbackQuery):
    target = float(call.data.split("_")[2])
    crash_point = round(random.uniform(1.0, 10.0), 2)
    
    msg = await call.message.answer("🚀 Ракета на старте...")
    await asyncio.sleep(1)
    
    if crash_point >= target:
        await msg.edit_text(f"🥳 **Победа! ✅**\n🚀 Долетела до x{crash_point}\n💰 Выигрыш: {int(10*target)} m¢", parse_mode="Markdown")
    else:
        await msg.edit_text(f"💥 **КРАШ!**\n📉 Взрыв на x{crash_point}\n🎯 Цель была x{target}", parse_mode="Markdown")

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
