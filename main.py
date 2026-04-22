import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'name': name, 'game_state': None, 'lock': False}
    return user_db[uid]

# --- ГЛАВНОЕ МЕНЮ (КАК НА СКРИНШОТЕ 1) ---
def get_main_menu(uid):
    u = get_user(uid)
    text = (
        f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {u['bal']} m₽\n"
        f"💸 **Ставка:** {u['bet']} m₽\n\n"
        f"👆 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["🏀", "⚽", "🎯", "🎳", "🎲", "🎰"]],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="tab_cases"), 
         InlineKeyboardButton(text="Режимы 💣", callback_data="mines_setup")],
        [InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/your_bot_link")], # Замени на свою ссылку
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- МЕНЮ ВЫБОРА МИН (КАК НА СКРИНШОТЕ 8) ---
@dp.callback_query(F.data == "mines_setup")
async def m_setup(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n💣 **Мины · выбери мины!**"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="double_bet")],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [1, 2, 3]],
        [InlineKeyboardButton(text=str(i), callback_data=f"mstart_{i}") for i in [4, 5, 6]],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

# --- ИГРОВОЕ ПОЛЕ МИН (КАК НА СКРИНШОТЕ 9) ---
async def render_mines(message, uid, ended=False, lost=False):
    u = user_db[uid]
    g = u['game_state']
    kb = []
    
    # Сетка 5x5 (как на скриншоте)
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i+5):
            if j in g['opened']:
                txt = "💎"
            elif (ended or lost) and j in g['mines']:
                txt = "💣" if not (lost and j == g.get('last_hit')) else "💥"
            else:
                txt = "❓" # Красные квадраты с вопросом
            row.append(InlineKeyboardButton(text=txt, callback_data=f"mhit_{j}" if not (ended or lost) else "none"))
        kb.append(row)
    
    if lost:
        text = f"👤 **{u['name']}**\n💥 **Мины · Проигрыш!**\n\n💣 Мин: {g['count']}\n💸 Ставка: {u['bet']} m₽\n💎 Открыто: {len(g['opened'])} из {25-g['count']}"
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {u['bet']} m₽", callback_data=f"mstart_{g['count']}")])
    elif ended:
        win = int(u['bet'] * g['m'])
        text = f"👤 **{u['name']}**\n✅ **Мины · Выплата!**\n\n💰 Выигрыш: {win} m₽"
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    else:
        text = f"👤 **{u['name']}**\n💎 **Мины · начни игру!**\n\n💣 Мин: {g['count']}\n💸 Ставка: {u['bet']} m₽\n📈 Множитель: x{g['m']}"
        if g['opened']:
            kb.append([InlineKeyboardButton(text=f"✅ Забрать {int(u['bet']*g['m'])} m₽", callback_data="mcash")])
    
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main"), InlineKeyboardButton(text="Честность 🔑", callback_data="provable")])
    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ЛОГИКА НАЖАТИЯ НА КЛЕТКУ ---
@dp.callback_query(F.data.startswith("mhit_"))
async def m_hit(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = get_user(uid)
    idx = int(callback.data.split("_")[1])
    g = u['game_state']
    
    if idx in g['mines']:
        g['last_hit'] = idx
        await render_mines(callback.message, uid, lost=True)
        u['game_state'] = None
    else:
        if idx not in g['opened']:
            g['opened'].append(idx)
            # Расчет множителя как в оригинале
            g['m'] = round(g['m'] * 1.2, 2) 
            await render_mines(callback.message, uid)

# --- ФУНКЦИИ СТАВОК ---
@dp.callback_query(F.data == "double_bet")
async def double_bet(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    u['bet'] *= 2
    await callback.answer(f"Ставка удвоена: {u['bet']}")
    await m_setup(callback)

@dp.callback_query(F.data == "mcash")
async def m_cash(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    win = int(u['bet'] * u['game_state']['m'])
    u['bal'] += win
    await render_mines(callback.message, callback.from_user.id, ended=True)
    u['game_state'] = None

@dp.callback_query(F.data.startswith("mstart_"))
async def m_start(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = get_user(uid)
    count = int(callback.data.split("_")[1])
    if u['bal'] < u['bet']: return await callback.answer("Мало m₽!")
    u['bal'] -= u['bet']
    u['game_state'] = {'mines': random.sample(range(25), count), 'opened': [], 'count': count, 'm': 1.1}
    await render_mines(callback.message, uid)

# --- ОСТАЛЬНОЕ ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k)

@dp.message()
async def all_msg(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
