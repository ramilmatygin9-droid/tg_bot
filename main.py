import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# === КОНФИГУРАЦИЯ (ВСТАВЬ СВОЙ ТОКЕН) ===
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база игроков
user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'name': name, 'lock': False, 'game_state': None}
    return user_db[uid]

# --- ГЛАВНОЕ МЕНЮ (КАК НА СКРИНШОТАХ) ---
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
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")],
        [InlineKeyboardButton(text="🔄 СТАРТ", callback_data="to_main")]
    ])
    return text, kb

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k)

# --- ВЫБОР СУБ-ИГРЫ (ОРИГИНАЛЬНОЕ ОФОРМЛЕНИЕ) ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_sub(callback: types.CallbackQuery):
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id)
    
    titles = {"⚽": "Футбол", "🏀": "Баскетбол", "🎯": "Дартс", "🎳": "Боулинг", "🎲": "Кубик"}
    title = titles.get(emoji.strip(), "Игра")
    
    text = f"👤 **{u['name']}**\n{emoji} **{title} · выбери исход!**\n—————————————————\n💸 **Ставка:** {u['bet']} ₽"
    kb = []

    if emoji == "🎯":
        text += "\n\n🔰 **Коэффициенты:**\n🔴 Красное (x1.94)\n⚪️ Белое (x2.9)\n🎯 Центр (x5.8)\n😯 Мимо (x5.8)"
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_🎯_red"), InlineKeyboardButton(text="⚪️ Белое", callback_data="play_🎯_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="play_🎯_center"), InlineKeyboardButton(text="😯 Мимо", callback_data="play_🎯_miss")]]
    elif emoji == "⚽":
        kb = [[InlineKeyboardButton(text="⚽ Гол (x1.6)", callback_data="play_⚽_win")], [InlineKeyboardButton(text="🥅 Мимо (x2.4)", callback_data="play_⚽_lose")]]
    elif emoji == "🏀":
        kb = [[InlineKeyboardButton(text="🏀 Попал (x2.4)", callback_data="play_🏀_win")], [InlineKeyboardButton(text="🙈 Мимо (x1.6)", callback_data="play_🏀_lose")]]
    elif emoji == "🎳":
        kb = [[InlineKeyboardButton(text="🎳 Страйк (x5.8)", callback_data="play_🎳_strike")], [InlineKeyboardButton(text="😟 Мимо (x5.8)", callback_data="play_🎳_miss")]]
    elif emoji == "🎲":
        kb = [[InlineKeyboardButton(text="⚖️ Чёт (x1.94)", callback_data="play_🎲_even"), InlineKeyboardButton(text="🔰 Нечёт (x1.94)", callback_data="play_🎲_odd")]]
    
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ОПРЕДЕЛЕНИЯ ВЫИГРЫША (ПО АНИМАЦИИ) ---
@dp.callback_query(F.data.startswith("play_"))
async def execute_play(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['lock']: return await callback.answer("⏳ Подождите...")
    
    _, emoji, choice = callback.data.split("_")
    if u['bal'] < u['bet']: return await callback.answer("❌ Недостаточно ₽!")

    u['lock'] = True
    u['bal'] -= u['bet']
    
    # Отправляем кубик/дротик/мяч
    msg = await callback.message.answer_dice(emoji=emoji if emoji != "🎳" else "🎳")
    val = msg.dice.value
    await asyncio.sleep(4.0) # Ждем, пока анимация доиграет

    win, coef = False, 0
    # ПРОВЕРКА ПО РЕЗУЛЬТАТУ АНИМАЦИИ TELEGRAM
    if emoji == "🎯":
        if choice == "red" and val in [4, 5]: win, coef = True, 1.94
        elif choice == "white" and val in [2, 3]: win, coef = True, 2.9
        elif choice == "center" and val == 6: win, coef = True, 5.8
        elif choice == "miss" and val == 1: win, coef = True, 5.8
    elif emoji == "⚽":
        if (choice == "win" and val in [3,4,5]) or (choice == "lose" and val in [1,2]): win, coef = True, (1.6 if choice == "win" else 2.4)
    elif emoji == "🏀":
        if (choice == "win" and val in [4,5]) or (choice == "lose" and val in [1,2,3]): win, coef = True, (2.4 if choice == "win" else 1.6)
    elif emoji == "🎳":
        if (choice == "strike" and val == 6) or (choice == "miss" and val == 1): win, coef = True, 5.8

    if win:
        prize = int(u['bet'] * coef)
        u['bal'] += prize
        await callback.message.answer(f"✅ ВЫИГРЫШ! +{prize} ₽")
    else:
        await callback.message.answer(f"❌ ПРОИГРЫШ!")

    u['lock'] = False
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.answer(t, reply_markup=k)

# --- МИНЫ (КАК В ОРИГИНАЛЕ) ---
@dp.callback_query(F.data == "mines_setup")
async def m_setup(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="double_bet")],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [1, 2, 3]],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [5, 6, 7]],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(f"👤 **{u['name']}**\n💣 **Мины · выбери кол-во!**", reply_markup=kb)

@dp.callback_query(F.data == "double_bet")
async def double_bet(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    u['bet'] *= 2
    await m_setup(callback)

@dp.callback_query(F.data.startswith("mstart_"))
async def m_start(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = get_user(uid)
    if u['bal'] < u['bet']: return await callback.answer("Мало ₽!")
    u['bal'] -= u['bet']
    count = int(callback.data.split("_")[1])
    # Генерируем мины (рандомно 25 ячеек)
    u['game_state'] = {'mines': random.sample(range(25), count), 'opened': [], 'count': count, 'm': 1.1}
    await render_mines(callback.message, uid)

async def render_mines(message, uid, lost=False):
    u = user_db[uid]
    g = u['game_state']
    kb = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i+5):
            txt = "❓"
            if j in g['opened']: txt = "💎"
            elif lost: txt = "💣"
            row.append(InlineKeyboardButton(text=txt, callback_data=f"mhit_{j}" if not lost else "none"))
        kb.append(row)
    
    if not lost and g['opened']:
        kb.append([InlineKeyboardButton(text=f"✅ Забрать {int(u['bet']*g['m'])} ₽", callback_data="mcash")])
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main"), InlineKeyboardButton(text="Честность 🔑", callback_data="check")])
    
    status = f"👤 **{u['name']}**\n📈 Коэф: x{g['m']} | Ставка: {u['bet']} ₽"
    if lost: status = f"👤 **{u['name']}**\n💥 **ВЫ ПРОИГРАЛИ!**"
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
    await callback.answer(f"💰 +{win} ₽!", show_alert=True)
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- ИЗМЕНЕНИЕ СТАВКИ ---
@dp.callback_query(F.data == "ch_bet")
async def ch_bet(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10 ₽", callback_data="setbet_10"), InlineKeyboardButton(text="50 ₽", callback_data="setbet_50")],
        [InlineKeyboardButton(text="100 ₽", callback_data="setbet_100"), InlineKeyboardButton(text="500 ₽", callback_data="setbet_500")],
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

@dp.callback_query(F.data == "to_main")
async def back_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
