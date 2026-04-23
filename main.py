import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# === КОНФИГУРАЦИЯ ===
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'name': name, 'game_state': None, 'lock': False}
    return user_db[uid]

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu(uid):
    u = get_user(uid)
    text = (
        f"👤 **{u['name']}**\n"
        f"💰 **Баланс:** {u['bal']} ₽\n"
        f"💸 **Ставка:** {u['bet']} ₽\n"
        f"—————————————————\n"
        f"👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["🏀", "⚽", "🎯", "🎳", "🎲", "🎰"]],
        [InlineKeyboardButton(text="🚀 Кейсы", callback_data="tab_cases"), 
         InlineKeyboardButton(text="Мины 💣", callback_data="mines_setup")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- АНТИ-СПАМ ПРОВЕРКА ---
async def is_locked(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['lock']:
        await callback.answer("⏳ Игра еще идет, подожди результат!", show_alert=False)
        return True
    return False

# --- ИЗМЕНЕНИЕ СТАВКИ ---
@dp.callback_query(F.data == "ch_bet")
async def ch_bet(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10", callback_data="setbet_10"), InlineKeyboardButton(text="50", callback_data="setbet_50")],
        [InlineKeyboardButton(text="100", callback_data="setbet_100"), InlineKeyboardButton(text="500", callback_data="setbet_500")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("💸 **ВЫБЕРИ РАЗМЕР СТАВКИ:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("setbet_"))
async def set_bet(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    u['bet'] = int(callback.data.split("_")[1])
    await callback.answer(f"Ставка: {u['bet']} ₽")
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- МЕНЮ ИГР (ОФОРМЛЕНИЕ ПО СКРИНШОТАМ) ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_sub(callback: types.CallbackQuery):
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id, callback.from_user.first_name)
    
    titles = {"⚽": "Футбол", "🏀": "Баскетбол", "🎯": "Дартс", "🎳": "Боулинг", "🎲": "Кубик"}
    title = titles.get(emoji, "Игра")
    
    text = f"👤 **{u['name']}**\n{emoji} **{title} · выбери исход!**\n—————————————————\n💸 **Ставка:** {u['bet']} ₽"
    kb = []

    if emoji == "⚽":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_⚽_win")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_⚽_lose")]]
    elif emoji == "🏀":
        kb = [[InlineKeyboardButton(text="🏀 Попал - x2.4", callback_data="play_🏀_win")],
              [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_🏀_lose")]]
    elif emoji == "🎯":
        kb = [[InlineKeyboardButton(text="🔴 Красное x1.94", callback_data="play_🎯_red"), InlineKeyboardButton(text="⚪️ Белое x2.9", callback_data="play_🎯_white")],
              [InlineKeyboardButton(text="🎯 Центр x5.8", callback_data="play_🎯_center"), InlineKeyboardButton(text="😯 Мимо x5.8", callback_data="play_🎯_miss")]]
    elif emoji == "🎳":
        kb = [[InlineKeyboardButton(text="🎳 Страйк x5.8", callback_data="play_🎳_strike")],
              [InlineKeyboardButton(text="😟 Мимо x5.8", callback_data="play_🎳_miss")]]
    elif emoji == "🎲":
        kb = [[InlineKeyboardButton(text="⚖️ Чёт x1.94", callback_data="play_🎲_even"), InlineKeyboardButton(text="🔰 Нечёт x1.94", callback_data="play_🎲_odd")],
              [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_🎲_high")],
              [InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_🎲_low")]]

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЧЕСТНАЯ СИСТЕМА ПРОВЕРКИ (DICE LOGIC) ---
@dp.callback_query(F.data.startswith("play_"))
async def execute_play(callback: types.CallbackQuery):
    if await is_locked(callback): return
    u = get_user(callback.from_user.id)
    _, emoji, choice = callback.data.split("_")
    
    if u['bal'] < u['bet']: return await callback.answer("Недостаточно ₽!")

    u['lock'] = True
    u['bal'] -= u['bet']
    
    msg = await callback.message.answer_dice(emoji=emoji if emoji != "🎳" else "🎳")
    val = msg.dice.value
    await asyncio.sleep(4.0)

    win, coef = False, 1.0

    if emoji == "⚽":
        # 1,2 - мимо; 3,4,5 - гол
        if choice == "win" and val in [3, 4, 5]: win, coef = True, 1.6
        if choice == "lose" and val in [1, 2]: win, coef = True, 2.4
    elif emoji == "🏀":
        # 1,2,3 - мимо; 4,5 - попал
        if choice == "win" and val in [4, 5]: win, coef = True, 2.4
        if choice == "lose" and val in [1, 2, 3]: win, coef = True, 1.6
    elif emoji == "🎯":
        if choice == "center" and val == 6: win, coef = True, 5.8
        if choice == "red" and val in [4, 5]: win, coef = True, 1.94
        if choice == "white" and val in [2, 3]: win, coef = True, 2.9
        if choice == "miss" and val == 1: win, coef = True, 5.8
    elif emoji == "🎳":
        if choice == "strike" and val == 6: win, coef = True, 5.8
        if choice == "miss" and val == 1: win, coef = True, 5.8
    elif emoji == "🎲":
        if choice == "even" and val % 2 == 0: win, coef = True, 1.94
        if choice == "odd" and val % 2 != 0: win, coef = True, 1.94
        if choice == "high" and val > 3: win, coef = True, 1.94
        if choice == "low" and val < 3: win, coef = True, 2.9

    if win:
        prize = int(u['bet'] * coef)
        u['bal'] += prize
        await callback.message.answer(f"✅ ВЫИГРЫШ! +{prize} ₽")
    else:
        await callback.message.answer(f"❌ ПРОИГРЫШ!")

    u['lock'] = False
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.answer(t, reply_markup=k)

# --- МИНЫ (БЕЗ 4, ВАЛЮТА ₽) ---
@dp.callback_query(F.data == "mines_setup")
async def m_setup(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="double_bet")],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [1, 2, 3]],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [5, 6, 7]],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(f"👤 **{u['name']}**\n💣 **Мины · выбери мины!**", reply_markup=kb)

@dp.callback_query(F.data == "double_bet")
async def double_bet(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    u['bet'] *= 2
    await m_setup(callback)

@dp.callback_query(F.data.startswith("mstart_"))
async def m_start(callback: types.CallbackQuery):
    if await is_locked(callback): return
    uid = callback.from_user.id
    u = get_user(uid)
    u['bal'] -= u['bet']
    count = int(callback.data.split("_")[1])
    u['game_state'] = {'mines': random.sample(range(25), count), 'opened': [], 'count': count, 'm': 1.1}
    await render_mines(callback.message, uid)

async def render_mines(message, uid, ended=False, lost=False):
    u = user_db[uid]
    g = u['game_state']
    kb = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i+5):
            txt = "❓"
            if j in g['opened']: txt = "💎"
            elif ended or lost: txt = "💣"
            row.append(InlineKeyboardButton(text=txt, callback_data=f"mhit_{j}" if not (ended or lost) else "none"))
        kb.append(row)
    
    if not (ended or lost) and g['opened']:
        kb.append([InlineKeyboardButton(text=f"✅ Забрать {int(u['bet']*g['m'])} ₽", callback_data="mcash")])
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    
    status = f"👤 **{u['name']}**\n💎 **Мины · Игра!**\n\n💣 Мин: {g['count']} | 💸 Ставка: {u['bet']} ₽\n📈 Коэф: x{g['m']}"
    if lost: status = f"👤 **{u['name']}**\n💥 **Мины · Проигрыш!**"
    await message.edit_text(status, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("mhit_"))
async def m_hit(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = get_user(uid)
    idx = int(callback.data.split("_")[1])
    g = u['game_state']
    if idx in g['mines']:
        await render_mines(callback.message, uid, lost=True)
        u['game_state'] = None
    else:
        g['opened'].append(idx)
        g['m'] = round(g['m'] * 1.3, 2)
        await render_mines(callback.message, uid)

@dp.callback_query(F.data == "mcash")
async def m_cash(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    win = int(u['bet'] * u['game_state']['m'])
    u['bal'] += win
    u['game_state'] = None
    await callback.answer(f"💰 +{win} ₽!")
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- КЕЙСЫ ---
@dp.callback_query(F.data == "tab_cases")
async def show_cases(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Деревянный (50 ₽)", callback_data="buy_50")],
        [InlineKeyboardButton(text="💰 Золотой (500 ₽)", callback_data="buy_500")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("🚀 **КЕЙСЫ:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_case(callback: types.CallbackQuery):
    if await is_locked(callback): return
    cost = int(callback.data.split("_")[1])
    u = get_user(callback.from_user.id)
    if u['bal'] < cost: return await callback.answer("Мало ₽!")
    u['lock'] = True
    u['bal'] -= cost
    win = random.randint(int(cost*0.4), cost*3)
    u['bal'] += win
    u['lock'] = False
    await callback.answer(f"🎁 Выпало: {win} ₽!", show_alert=True)
    await show_cases(callback)

# --- ОБЩЕЕ ---
@dp.callback_query(F.data == "to_main")
async def back_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

@dp.message()
async def start(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
