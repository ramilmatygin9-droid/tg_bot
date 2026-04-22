import asyncio
import random
import math
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных игр
user_games = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def calculate_multiplier(mines, opened):
    # Упрощенная формула множителя для имитации
    # В реальных минах: С(всего-мины, открыто) / С(всего, открыто)
    total_cells = 25
    safe_cells = total_cells - mines
    if opened == 0: return 1.0
    
    mult = 1.0
    for i in range(opened):
        mult *= (total_cells - i) / (safe_cells - i)
    return round(mult, 2)

def get_next_mults(mines, opened):
    res = []
    for i in range(1, 6):
        res.append(f"x{calculate_multiplier(mines, opened + i)}")
    return " ➡ ".join(res)

# --- КЛАВИАТУРЫ ---

def main_menu_kb(balance=182, bet=10):
    text = (
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {balance} m₽\n"
        f"💸 **Ставка:** {bet} m₽\n\n"
        "👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="setup_mines"), 
         InlineKeyboardButton(text="Алмазы 💎", callback_data="dev")],
        [InlineKeyboardButton(text="🏰 Башня", callback_data="dev"), 
         InlineKeyboardButton(text="Золото ⚜", callback_data="dev")],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="dev")]
    ])
    return text, kb

def mines_setup_kb():
    # Клавиатура выбора количества мин (как на скрине 1)
    btns = []
    row = []
    for i in range(1, 7):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"start_with_{i}"))
        if i % 3 == 0:
            btns.append(row)
            row = []
    btns.append([InlineKeyboardButton(text="⬅ назад", callback_data="to_main")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def get_game_kb(user_id):
    game = user_games[user_id]
    kb = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i + 5):
            if j in game['opened']:
                row.append(InlineKeyboardButton(text="💎", callback_data="none"))
            elif not game['active'] and j in game['mines']:
                row.append(InlineKeyboardButton(text="💣", callback_data="none"))
            else:
                row.append(InlineKeyboardButton(text="❓", callback_data=f"hit_{j}"))
        kb.append(row)
    
    if game['active']:
        kb.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="cashout")])
    else:
        kb.append([InlineKeyboardButton(text="🔄 Повторить", callback_data="setup_mines"),
                   InlineKeyboardButton(text="⬅ назад", callback_data="to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    text, kb = main_menu_kb()
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "setup_mines")
async def setup_mines(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💣 **Мины · выбери мины!**\n"
        "........................\n"
        "💸 **Ставка:** 10 m₽",
        reply_markup=mines_setup_kb(), parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("start_with_"))
async def start_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mines_count = int(callback.data.split("_")[-1])
    
    user_games[user_id] = {
        'mines_count': mines_count,
        'mines': random.sample(range(25), mines_count),
        'opened': [],
        'bet': 10,
        'active': True
    }
    
    game = user_games[user_id]
    mult = calculate_multiplier(mines_count, 0)
    next_m = get_next_mults(mines_count, 0)
    
    text = (
        "🍀 **Мины · начни игру!**\n"
        "........................\n"
        f"💣 **Мин:** {mines_count}\n"
        f"💸 **Ставка:** 10 m₽\n\n"
        f"🧮 **Следующий множитель:**\n"
        f" `{next_m}`"
    )
    await callback.message.edit_text(text, reply_markup=get_game_kb(user_id), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("hit_"))
async def hit_cell(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cell = int(callback.data.split("_")[1])
    game = user_games[user_id]
    
    if cell in game['mines']:
        # ПРОИГРЫШ (Скрин 3)
        game['active'] = False
        m_val = calculate_multiplier(game['mines_count'], len(game['opened']))
        text = (
            "💥 **Мины · Проигрыш!**\n"
            "........................\n"
            f"💣 **Мин:** {game['mines_count']}\n"
            f"💸 **Ставка:** 10 m₽\n"
            f"💎 **Открыто:** {len(game['opened'])} из {25 - game['mines_count']}\n\n"
            f"💜 **Мог забрать:** x{m_val} / {int(10 * m_val)} m₽"
        )
        await callback.message.edit_text(text, reply_markup=get_game_kb(user_id), parse_mode="Markdown")
    else:
        # ИГРА ИДЕТ (Скрин 4)
        game['opened'].append(cell)
        m_val = calculate_multiplier(game['mines_count'], len(game['opened']))
        next_m = get_next_mults(game['mines_count'], len(game['opened']))
        
        text = (
            "💎 **Мины · игра идёт.**\n"
            "........................\n"
            f"💣 **Мин:** {game['mines_count']}\n"
            f"💸 **Ставка:** 10 m₽\n"
            f"📊 **Выигрыш:** x{m_val} / {int(10 * m_val)} m₽\n\n"
            f"🧮 **Следующий множитель:**\n"
            f" `{next_m}`"
        )
        await callback.message.edit_text(text, reply_markup=get_game_kb(user_id), parse_mode="Markdown")

@dp.callback_query(F.data == "cashout")
async def cashout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    game = user_games[user_id]
    m_val = calculate_multiplier(game['mines_count'], len(game['opened']))
    win = int(10 * m_val)
    
    await callback.answer(f"✅ Забрал {win} m₽!", show_alert=True)
    text, kb = main_menu_kb(balance=182 + win)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    text, kb = main_menu_kb()
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "dev")
async def dev(callback: types.CallbackQuery):
    await callback.answer("⚒ В разработке...")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
