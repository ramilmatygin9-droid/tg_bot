import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных
user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {
            'bal': 1000, 
            'bet': 10, 
            'name': name, 
            'game_state': None,
            'is_playing': False # Анти-дюп флаг
        }
    return user_db[uid]

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu(uid):
    u = get_user(uid)
    text = (
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {u['bal']} m₽\n"
        f"💸 **Ставка:** {u['bet']} m₽\n\n"
        f"👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["🏀", "⚽", "🎯", "🎳", "🎲", "🎰"]],
        [
            InlineKeyboardButton(text="🚀 Быстрые (Кейсы)", callback_data="tab_cases"),
            InlineKeyboardButton(text="Мины 💣", callback_data="mines_setup")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url="https://google.com"))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- АНТИ-ДЮП ОБЕРТКА ---
async def check_antidup(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['is_playing']:
        await callback.answer("⏳ Подождите, действие обрабатывается!", show_alert=True)
        return True
    return False

# --- ЛОГИКА МИН ---
@dp.callback_query(F.data == "mines_setup")
async def m_setup(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n💣 **Мины · выбери количество!**"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"m_start_{i}") for i in range(1, 4)],
        [InlineKeyboardButton(text=str(i), callback_data=f"m_start_{i}") for i in range(4, 7)],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("m_start_"))
async def m_start(callback: types.CallbackQuery):
    if await check_antidup(callback): return
    uid = callback.from_user.id
    u = get_user(uid)
    count = int(callback.data.split("_")[2])
    
    if u['bal'] < u['bet']: return await callback.answer("Недостаточно m₽")
    
    u['is_playing'] = True
    u['bal'] -= u['bet']
    mines = random.sample(range(25), count)
    u['game_state'] = {'mines': mines, 'opened': [], 'count': count, 'mult': 1.0}
    await render_mines(callback.message, uid)
    u['is_playing'] = False

async def render_mines(message, uid, ended=False):
    u = user_db[uid]
    g = u['game_state']
    next_m = round(1.2 + (len(g['opened']) * 0.3), 2)
    
    text = f"👤 **{u['name']}**\n💣 **Мины · Игра идет!**\nМножитель: x{g['mult']}\nСлед.: x{next_m}"
    if ended: text = f"👤 **{u['name']}**\n💣 **Мины · Конец игры!**"

    btns = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i+5):
            char = "❓"
            if j in g['opened']: char = "💎"
            elif ended and j in g['mines']: char = "💣"
            row.append(InlineKeyboardButton(text=char, callback_data=f"m_hit_{j}" if not ended else "none"))
        btns.append(row)
    
    if not ended and g['opened']:
        btns.append([InlineKeyboardButton(text=f"✅ ЗАБРАТЬ {int(u['bet']*g['mult'])} m₽", callback_data="m_cash")])
    btns.append([InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")])
    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("m_hit_"))
async def m_hit(callback: types.CallbackQuery):
    if await check_antidup(callback): return
    uid = callback.from_user.id
    u = get_user(uid)
    cell = int(callback.data.split("_")[2])
    g = u['game_state']
    
    u['is_playing'] = True
    if cell in g['mines']:
        await render_mines(callback.message, uid, ended=True)
    else:
        g['opened'].append(cell)
        g['mult'] = round(1.2 + (len(g['opened']) * 0.3), 2)
        await render_mines(callback.message, uid)
    u['is_playing'] = False

@dp.callback_query(F.data == "m_cash")
async def m_cash(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    win = int(u['bet'] * u['game_state']['mult'])
    u['bal'] += win
    await callback.answer(f"Выигрыш: {win} m₽!", show_alert=True)
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- КЕЙСЫ ---
@dp.callback_query(F.data == "tab_cases")
async def cases(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Деревянный (50 m₽)", callback_data="buy_50")],
        [InlineKeyboardButton(text="💰 Золотой (500 m₽)", callback_data="buy_500")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("🚀 **ВЫБЕРИ КЕЙС:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_case(callback: types.CallbackQuery):
    if await check_antidup(callback): return
    cost = int(callback.data.split("_")[1])
    u = get_user(callback.from_user.id)
    if u['bal'] < cost: return await callback.answer("Мало денег!")
    
    u['is_playing'] = True
    u['bal'] -= cost
    win = random.randint(int(cost*0.5), cost*3)
    u['bal'] += win
    await callback.answer(f"Выпало: {win} m₽!", show_alert=True)
    u['is_playing'] = False
    await cases(callback)

# --- ИГРЫ (ФУТБОЛ И Т.Д.) ---
@dp.callback_query(F.data.startswith("sub_"))
async def sub_games(callback: types.CallbackQuery):
    e = callback.data.split("_")[1]
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n{e} **Игра: {e}**\n💸 Ставка: {u['bet']} m₽"
    # Тут можно добавить кнопки коэффициентов как в прошлых сообщениях
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Играть {e}", callback_data=f"go_{e}")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

# --- ОБЩЕЕ ---
@dp.callback_query(F.data == "to_main")
async def to_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

@dp.message(Command("start"))
@dp.message()
async def start(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
