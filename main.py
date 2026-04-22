import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# === КОНФИГУРАЦИЯ ===
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных
user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'name': name, 'game_state': None, 'lock': False}
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
            InlineKeyboardButton(text="🚀 Кейсы", callback_data="tab_cases"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="mines_setup")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- АНТИ-СПАМ (ЗАЩИТА ОТ ДЮПА) ---
async def is_locked(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['lock']:
        await callback.answer("⏳ Обработка... Не нажимай часто!", show_alert=False)
        return True
    return False

# --- МИНЫ (БЕЗ ЦИФРЫ 4) ---
@dp.callback_query(F.data == "mines_setup")
async def m_setup(callback: types.CallbackQuery):
    if await is_locked(callback): return
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n💣 **Мины · выбери количество!**"
    # Убрали 4 из списка
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [1, 2, 3]],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [5, 6]],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("mstart_"))
async def m_start(callback: types.CallbackQuery):
    if await is_locked(callback): return
    uid = callback.from_user.id
    u = get_user(uid)
    count = int(callback.data.split("_")[1])
    
    if u['bal'] < u['bet']: return await callback.answer("Недостаточно m₽!")
    
    u['lock'] = True
    u['bal'] -= u['bet']
    mines = random.sample(range(25), count)
    u['game_state'] = {'mines': mines, 'opened': [], 'count': count, 'm': 1.0}
    await render_mines(callback.message, uid)
    u['lock'] = False

async def render_mines(message, uid, ended=False):
    u = user_db[uid]
    g = u['game_state']
    kb = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i+5):
            txt = "❓"
            if j in g['opened']: txt = "💎"
            elif ended and j in g['mines']: txt = "💣"
            row.append(InlineKeyboardButton(text=txt, callback_data=f"mhit_{j}" if not ended else "none"))
        kb.append(row)
    
    if not ended and g['opened']:
        win_now = int(u['bet'] * g['m'])
        kb.append([InlineKeyboardButton(text=f"✅ ЗАБРАТЬ {win_now} m₽", callback_data="mcash")])
    kb.append([InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")])
    
    status = f"💣 Мин: {g['count']} | Множитель: x{g['m']}"
    if ended: status = "💥 ИГРА ОКОНЧЕНА"
    await message.edit_text(status, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("mhit_"))
async def m_hit(callback: types.CallbackQuery):
    if await is_locked(callback): return
    uid = callback.from_user.id
    u = get_user(uid)
    idx = int(callback.data.split("_")[1])
    g = u['game_state']
    
    u['lock'] = True
    if idx in g['mines']:
        await render_mines(callback.message, uid, ended=True)
        u['game_state'] = None
    else:
        if idx not in g['opened']:
            g['opened'].append(idx)
            # Коэффициент растет от количества мин
            g['m'] = round(g['m'] + (g['count'] * 0.35), 2)
            await render_mines(callback.message, uid)
    u['lock'] = False

@dp.callback_query(F.data == "mcash")
async def m_cash(callback: types.CallbackQuery):
    if await is_locked(callback): return
    u = get_user(callback.from_user.id)
    u['lock'] = True
    win = int(u['bet'] * u['game_state']['m'])
    u['bal'] += win
    u['game_state'] = None
    u['lock'] = False
    await callback.answer(f"💰 Зачислено: {win} m₽!", show_alert=True)
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- ОСТАЛЬНЫЕ ИГРЫ И КЕЙСЫ (БЕЗ ИЗМЕНЕНИЙ) ---
@dp.callback_query(F.data == "tab_cases")
async def show_cases(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Деревянный (50)", callback_data="buy_50")],
        [InlineKeyboardButton(text="💰 Золотой (500)", callback_data="buy_500")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("🚀 **КЕЙСЫ:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_case(callback: types.CallbackQuery):
    if await is_locked(callback): return
    cost = int(callback.data.split("_")[1])
    u = get_user(callback.from_user.id)
    if u['bal'] < cost: return await callback.answer("Мало m₽!")
    u['lock'] = True
    u['bal'] -= cost
    win = random.randint(int(cost*0.5), cost*3)
    u['bal'] += win
    u['lock'] = False
    await callback.answer(f"🎁 Выпало: {win} m₽!", show_alert=True)
    await show_cases(callback)

@dp.callback_query(F.data == "to_main")
async def back_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.message()
async def any_msg(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
