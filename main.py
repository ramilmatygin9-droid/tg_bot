import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# === КОНФИГУРАЦИЯ ===
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных игроков
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
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["🏀", "⚽", "🎯", " bowling", "🎲", "🎰"]],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="tab_cases"), 
         InlineKeyboardButton(text="Режимы 💣", callback_data="mines_setup")],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url="https://google.com"))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- АНТИ-СПАМ ---
async def is_locked(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if u['lock']:
        await callback.answer("⏳ Обработка... Не нажимай часто!")
        return True
    return False

# --- ВЫБОР СТАВКИ ---
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
    await callback.answer(f"Ставка: {u['bet']} m₽")
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

# --- ИГРОВЫЕ МЕНЮ (КАК НА СКРИНШОТАХ) ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_sub(callback: types.CallbackQuery):
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id, callback.from_user.first_name)
    
    titles = {
        "⚽": "Футбол · выбери исход!",
        "🏀": "Баскетбол · выбери исход!",
        "🎯": "Дартс · выбери исход!",
        " bowling": "Боулинг · выбери исход!",
        "🎲": "Кубик · выбери режим!"
    }
    
    title = titles.get(emoji, "Выбери исход!")
    text = f"👤 **{u['name']}**\n{emoji} **{title}**\n—————————————————\n💸 **Ставка:** {u['bet']} m₽"
    kb = []

    if emoji == "⚽":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_⚽_win")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_⚽_lose")]]
    elif emoji == "🏀":
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_🏀_win")],
              [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_🏀_lose")]]
    elif emoji == "🎯":
        text += "\n\n🔰 **Коэффициенты:**\n🔴 Красное (x1.94)\n⚪️ Белое (x2.9)\n🎯 Центр (x5.8)\n😯 Мимо (x5.8)"
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_🎯_red"), InlineKeyboardButton(text="⚪️ Белое", callback_data="play_🎯_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="play_🎯_center"), InlineKeyboardButton(text="😯 Мимо", callback_data="play_🎯_miss")]]
    elif emoji == " bowling":
        text += "\n\n🔰 **Коэффициенты:**\n1-5 кегли (x5.8)\n🎳 Страйк (x5.8)\n😟 Мимо (x5.8)"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="play_🎳_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_🎳_3")],
              [InlineKeyboardButton(text="4 кегли", callback_data="play_🎳_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_🎳_5")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_🎳_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_🎳_miss")]]
    elif emoji == "🎲":
        kb = [[InlineKeyboardButton(text=str(i), callback_data=f"play_🎲_{i}") for i in range(1, 4)],
              [InlineKeyboardButton(text=str(i), callback_data=f"play_🎲_{i}") for i in range(4, 7)],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_🎲_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_🎲_odd")],
              [InlineKeyboardButton(text="— Равно 3 x5.8", callback_data="play_🎲_3")],
              [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_🎲_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_🎲_low")]]

    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА ИГР (ИСПРАВЛЕН БАГ С ВЫБОРОМ) ---
@dp.callback_query(F.data.startswith("play_"))
async def execute_play(callback: types.CallbackQuery):
    if await is_locked(callback): return
    u = get_user(callback.from_user.id)
    _, emoji, choice = callback.data.split("_")
    
    if u['bal'] < u['bet']: return await callback.answer("Недостаточно m₽!")
    u['lock'] = True
    u['bal'] -= u['bet']
    
    msg = await callback.message.answer_dice(emoji=emoji if emoji != " bowling" else "🎳")
    val = msg.dice.value
    await asyncio.sleep(4.0)

    win, coef = False, 2.0
    if emoji == "⚽":
        if (choice == "win" and val >= 3) or (choice == "lose" and val <= 2): win, coef = True, (1.6 if choice == "win" else 2.4)
    elif emoji == "🏀":
        if (choice == "win" and val >= 4) or (choice == "lose" and val <= 3): win, coef = True, (2.4 if choice == "win" else 1.6)
    elif emoji == "🎲":
        if (choice == "even" and val % 2 == 0) or (choice == "odd" and val % 2 != 0) or (choice.isdigit() and val == int(choice)):
            win, coef = True, (1.94 if not choice.isdigit() else 5.8)

    if win:
        prize = int(u['bet'] * coef)
        u['bal'] += prize
        await callback.message.answer(f"✅ ВЫИГРЫШ! +{prize} m₽")
    else:
        await callback.message.answer(f"❌ ПРОИГРЫШ!")

    u['lock'] = False
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.answer(t, reply_markup=k)

# --- МИНЫ (БЕЗ 4, С КНОПКОЙ УДВОИТЬ) ---
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
        kb.append([InlineKeyboardButton(text=f"✅ Забрать {int(u['bet']*g['m'])} m₽", callback_data="mcash")])
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main"), InlineKeyboardButton(text="Честность 🔑", callback_data="provable")])
    
    status = f"👤 **{u['name']}**\n💎 **Мины · начни игру!**\n\n💣 Мин: {g['count']}\n💸 Ставка: {u['bet']} m₽\n📈 Множитель: x{g['m']}"
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
        g['m'] = round(g['m'] * 1.25, 2)
        await render_mines(callback.message, uid)

@dp.callback_query(F.data == "mcash")
async def m_cash(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    win = int(u['bet'] * u['game_state']['m'])
    u['bal'] += win
    u['game_state'] = None
    await callback.answer(f"💰 +{win} m₽!")
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

@dp.callback_query(F.data == "to_main")
async def back_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

@dp.message()
async def start(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k)

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
