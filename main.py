import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных в памяти (для теста)
user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {'bal': 1000, 'bet': 10, 'game': None}
    return user_data[uid]

def get_main_menu(uid):
    user = get_user(uid)
    text = (
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {user['bal']} m₽\n"
        f"💸 **Ставка:** {user['bet']} m₽\n\n"
        "👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"dice_{e}") for e in ["🏀", "⚽", "🎯", "🎳", "🎲", "🎰"]],
        [
            InlineKeyboardButton(text="🚀 Кейсы", callback_data="tab_cases"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="mines_settings")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- РАЗДЕЛ: МИНЫ (НАСТРОЙКИ И ИГРА) ---

@dp.callback_query(F.data == "mines_settings")
async def mines_sets(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2 Мины (Поле 3x3)", callback_data="st_mines_2")],
        [InlineKeyboardButton(text="10 Мин (Поле 5x5)", callback_data="st_mines_10")],
        [InlineKeyboardButton(text="20 Мин (Поле 7x7)", callback_data="st_mines_20")],
        [InlineKeyboardButton(text="« Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("💣 **ВЫБЕРИ СЛОЖНОСТЬ:**\nЧем больше мин, тем выше множитель!", reply_markup=kb)

def get_mines_kb(uid):
    game = user_data[uid]['game']
    size = game['size']
    btns = []
    for i in range(0, size*size, size):
        row = [InlineKeyboardButton(text="💎" if j in game['open'] else "❓", callback_data=f"m_{j}") for j in range(i, i+size)]
        btns.append(row)
    btns.append([InlineKeyboardButton(text=f"✅ ЗАБРАТЬ {game['cur_win']} m₽", callback_data="m_cash")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

@dp.callback_query(F.data.startswith("st_mines_"))
async def start_m(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user = get_user(uid)
    m_count = int(callback.data.split("_")[2])
    
    if user['bal'] < user['bet']: return await callback.answer("Мало денег!")
    
    size = 3 if m_count == 2 else (7 if m_count == 20 else 5)
    user['bal'] -= user['bet']
    user['game'] = {
        'mines': random.sample(range(size*size), m_count),
        'open': [],
        'size': size,
        'm_count': m_count,
        'cur_win': user['bet'],
        'step': 0
    }
    await callback.message.edit_text(f"💣 Поле {size}x{size}, мин: {m_count}", reply_markup=get_mines_kb(uid))

@dp.callback_query(F.data.startswith("m_"))
async def play_m(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user = get_user(uid)
    if not user['game'] or callback.data == "mines_settings": return

    if callback.data == "m_cash":
        win = user['game']['cur_win']
        user['bal'] += win
        user['game'] = None
        await callback.answer(f"Выигрыш: {win} m₽!")
        t, k = get_main_menu(uid)
        return await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

    idx = int(callback.data.split("_")[1])
    game = user['game']
    
    if idx in game['mines']:
        user['game'] = None
        await callback.message.edit_text("💥 БАБАХ! Ты проиграл.")
        await asyncio.sleep(2)
        t, k = get_main_menu(uid)
        await callback.message.answer(t, reply_markup=k, parse_mode="Markdown")
    else:
        if idx not in game['open']:
            game['open'].append(idx)
            game['step'] += 1
            mult = 1.2 + (game['m_count'] / 10)
            game['cur_win'] = int(user['bet'] * (mult ** game['step']))
            await callback.message.edit_reply_markup(reply_markup=get_mines_kb(uid))

# --- РАЗДЕЛ: КЕЙСЫ (СТАРЫЙ) ---

@dp.callback_query(F.data == "tab_cases")
async def show_cases(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ДЕРЕВЯННЫЙ (50 m₽)", callback_data="buy_c_50_300")],
        [InlineKeyboardButton(text="💰 ЗОЛОТОЙ (500 m₽)", callback_data="buy_c_500_2500")],
        [InlineKeyboardButton(text="« Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("📦 **МАГАЗИН КЕЙСОВ:**\nИспытай свою удачу!", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_c_"))
async def open_c(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user = get_user(uid)
    _, _, cost, max_w = callback.data.split("_")
    cost, max_w = int(cost), int(max_w)
    
    if user['bal'] < cost: return await callback.answer("Мало m₽!")
    
    user['bal'] -= cost
    win = random.randint(int(cost*0.2), max_w)
    user['bal'] += win
    await callback.answer(f"Вам выпало: {win} m₽!", show_alert=True)
    await show_cases(callback)

# --- ОБЩЕЕ ---

@dp.callback_query(F.data == "to_main")
async def back(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("dice_"))
async def d_game(callback: types.CallbackQuery):
    e = callback.data.split("_")[1]
    msg = await callback.message.answer_dice(emoji=e)
    # Логика выигрыша для дайсов тут (опционально)
    
@dp.message(Command("start"))
async def st(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
