import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных (в продакшене используй SQL)
user_data = {}

# --- УТИЛИТЫ ---
def get_header(user_id, name):
    if user_id not in user_data:
        user_data[user_id] = {"balance": 1000, "lvl": 1}
    data = user_data[user_id]
    return (f"👤 {name} | ID: `{user_id}`\n"
            f"🏆 Ваш уровень: {data['lvl']}\n"
            f"💰 Баланс: {data['balance']} m¢\n"
            f"────────────────")

def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="🏀", callback_data="game_basketball"),
         InlineKeyboardButton(text="⚽", callback_data="game_football"),
         InlineKeyboardButton(text="🎯", callback_data="game_darts"),
         InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
         InlineKeyboardButton(text="🎲", callback_data="game_dice"),
         InlineKeyboardButton(text="🎰", callback_data="game_slots")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="menu_fast"),
         InlineKeyboardButton(text="Режимы 💣", callback_data="menu_modes")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
         InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- МЕНЮ БЫСТРЫХ ИГР ---
@dp.callback_query(F.data == "menu_fast")
async def fast_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🚀 Краш", callback_data="game_crash"),
         InlineKeyboardButton(text="💣 Мины", callback_data="game_mines")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette"),
         InlineKeyboardButton(text="💰 Монетка", callback_data="game_coin")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user.id, call.from_user.first_name)}\n🚀 **Быстрые игры**", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ИГРА МИНЫ (MINES) ---
active_mines = {}

def get_mines_kb(user_id, exploded_cell=None):
    game = active_mines[user_id]
    grid = []
    for y in range(5):
        row = []
        for x in range(5):
            cell = f"{x}_{y}"
            if cell in game['opened']:
                text = "💥" if cell == exploded_cell else "💎"
            else:
                text = "🔹"
            row.append(InlineKeyboardButton(text=text, callback_data=f"mine_{cell}"))
        grid.append(row)
    grid.append([InlineKeyboardButton(text=f"📥 Забрать {game['current_win']} m¢", callback_data="mine_cashout")])
    return InlineKeyboardMarkup(inline_keyboard=grid)

@dp.callback_query(F.data == "game_mines")
async def start_mines(call: types.CallbackQuery):
    user_id = call.from_user.id
    # Генерируем 3 мины
    all_cells = [f"{x}_{y}" for x in range(5) for y in range(5)]
    mines = random.sample(all_cells, 3)
    active_mines[user_id] = {"mines": mines, "opened": [], "current_win": 10}
    
    await call.message.edit_text(f"{get_header(user_id, call.from_user.first_name)}\n💣 **Мины: Удачи!**", 
                                 reply_markup=get_mines_kb(user_id), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("mine_"))
async def play_mines(call: types.CallbackQuery):
    user_id = call.from_user.id
    if call.data == "mine_cashout":
        win = active_mines[user_id]['current_win']
        user_data[user_id]['balance'] += win
        await call.answer(f"Вы забрали {win} m¢!", show_alert=True)
        return await to_main(call)
    
    cell = call.data.replace("mine_", "")
    game = active_mines[user_id]
    
    if cell in game['mines']:
        game['opened'].append(cell)
        user_data[user_id]['balance'] -= 10
        await call.message.edit_text(f"{get_header(user_id, call.from_user.first_name)}\n💥 **БОМБА! Вы проиграли!**", 
                                     reply_markup=get_main_menu(), parse_mode="Markdown")
    else:
        game['opened'].append(cell)
        game['current_win'] = int(game['current_win'] * 1.4)
        await call.message.edit_reply_markup(reply_markup=get_mines_kb(user_id))

# --- ИГРА КРАШ (CRASH) ---
@dp.callback_query(F.data == "game_crash")
async def crash_bet(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="x1.2", callback_data="cr_1.2"), InlineKeyboardButton(text="x2.0", callback_data="cr_2.0")],
        [InlineKeyboardButton(text="x5.0", callback_data="cr_5.0"), InlineKeyboardButton(text="x10.0", callback_data="cr_10.0")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_fast")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user.id, call.from_user.first_name)}\n🚀 **Выбери множитель:**", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cr_"))
async def crash_run(call: types.CallbackQuery):
    target = float(call.data.split("_")[1])
    crash_at = round(random.uniform(1.0, 5.0), 2)
    
    msg = await call.message.answer("🚀 Ракета взлетает...")
    await asyncio.sleep(1.5)
    
    if crash_at >= target:
        user_data[call.from_user.id]['balance'] += int(10 * target)
        await msg.edit_text(f"🥳 **Победа!**\nРакета долетела до x{crash_at}\nВыигрыш: {int(10*target)} m¢")
    else:
        user_data[call.from_user.id]['balance'] -= 10
        await msg.edit_text(f"💥 **КРАШ!**\nРакета взорвалась на x{crash_at}")

# --- ОБЩИЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"{get_header(message.from_user.id, message.from_user.first_name)}\nВыбирай игру:", 
                         reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_home(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_header(call.from_user.id, call.from_user.first_name)}\nВыбирай игру:", 
                                 reply_markup=get_main_menu(), parse_mode="Markdown")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
