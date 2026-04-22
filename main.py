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

# Временная база данных в оперативной памяти
user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {
            'bal': 1000, 
            'bet': 10, 
            'name': name, 
            'game_state': None, 
            'lock': False  # Флаг анти-дюпа
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
            InlineKeyboardButton(text="🚀 Кейсы", callback_data="tab_cases"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="mines_setup")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- ПРОВЕРКА НА АНТИ-СПАМ ---
async def is_locked(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['lock']:
        await callback.answer("⏳ Подождите, действие обрабатывается...", show_alert=False)
        return True
    return False

# --- ПОДМЕНЮ ИГР (ФУТБОЛ, ДАРТС И Т.Д.) ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_submenu(callback: types.CallbackQuery):
    if await is_locked(callback): return
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id, callback.from_user.first_name)
    
    base_text = f"👤 **{u['name']}**\n{emoji} **Игра: {emoji}**\n. . . . . . . . . . . . . . . . . .\n💸 **Ставка:** {u['bet']} m₽"
    rows = []
    
    if emoji == "⚽":
        rows = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_⚽_win")],
                [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_⚽_lose")]]
    elif emoji == "🏀":
        rows = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_🏀_win")],
                [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_🏀_lose")]]
    elif emoji == "🎯":
        rows = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_🎯_r"), InlineKeyboardButton(text="⚪ Белое", callback_data="play_🎯_w")],
                [InlineKeyboardButton(text="🎯 Центр", callback_data="play_🎯_c"), InlineKeyboardButton(text="😯 Мимо", callback_data="play_🎯_m")]]
    elif emoji == "🎳":
        rows = [[InlineKeyboardButton(text="1-5 кеглей", callback_data="play_🎳_win")],
                [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_🎳_strike")]]
    elif emoji == "🎲":
        rows = [[InlineKeyboardButton(text=str(i), callback_data=f"play_🎲_{i}") for i in range(1, 4)],
                [InlineKeyboardButton(text=str(i), callback_data=f"play_🎲_{i}") for i in range(4, 7)],
                [InlineKeyboardButton(text="⚖️ Чёт", callback_data="play_🎲_even"), InlineKeyboardButton(text="🔰 Нечёт", callback_data="play_🎲_odd")]]
    else: # Слоты
        rows = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="play_🎰_go")]]

    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")])
    await callback.message.edit_text(base_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

# --- ЛОГИКА ЭМОДЗИ-ИГР ---
@dp.callback_query(F.data.startswith("play_"))
async def execute_play(callback: types.CallbackQuery):
    if await is_locked(callback): return
    u = get_user(callback.from_user.id)
    u['lock'] = True 
    
    _, emoji, choice = callback.data.split("_")
    if u['bal'] < u['bet']:
        u['lock'] = False
        return await callback.answer("Недостаточно m₽!")

    u['bal'] -= u['bet']
    dice_msg = await callback.message.answer_dice(emoji=emoji)
    await asyncio.sleep(4.0) 
    
    win = random.choice([True, False, False]) # Шанс выигрыша
    if win:
        prize = int(u['bet'] * 2)
        u['bal'] += prize
        await callback.message.answer(f"✅ Победа! +{prize} m₽")
    else:
        await callback.message.answer("❌ Проигрыш!")
    
    u['lock'] = False
    t, k = get_main_menu(u['name'])
    await callback.message.answer(t, reply_markup=k, parse_mode="Markdown")

# --- МИНЫ 5x5 (4 УДАЛЕНА) ---
@dp.callback_query(F.data == "mines_setup")
async def m_setup(callback: types.CallbackQuery):
    if await is_locked(callback): return
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n💣 **Мины · выбери количество!**"
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
    
    if u['bal'] < u['bet']: return await callback.answer("Мало m₽!")
    
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
        kb.append([InlineKeyboardButton(text=f"✅ ЗАБРАТЬ {int(u['bet']*g['m'])}", callback_data="mcash")])
    kb.append([InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")])
    await message.edit_text(f"💣 Мин: {g['count']} | Множитель: x{g['m']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

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
    else:
        if idx not in g['opened']:
            g['opened'].append(idx)
            g['m'] = round(g['m'] + (g['count'] * 0.4), 2)
            await render_mines(callback.message, uid)
    u['lock'] = False

@dp.callback_query(F.data == "mcash")
async def m_cash(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    win = int(u['bet'] * u['game_state']['m'])
    u['bal'] += win
    u['game_state'] = None
    await callback.answer(f"💰 Выигрыш: {win} m₽!", show_alert=True)
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- РАЗДЕЛ КЕЙСОВ ---
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
    await callback.answer(f"🎁 Выпало: {win} m₽!", show_alert=True)
    u['lock'] = False
    await show_cases(callback)

# --- ОБЩИЕ ФУНКЦИИ ---
@dp.callback_query(F.data == "to_main")
async def back_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.message()
async def start_handler(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
