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
        user_db[uid] = {'bal': 1000, 'bet': 10, 'name': name, 'game_state': None}
    return user_db[uid]

def get_main_menu(uid):
    u = get_user(uid)
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {u['bal']} m₽\n💸 **Ставка:** {u['bet']} m₽"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="mines_setup"), InlineKeyboardButton(text="💎 Алмазы", callback_data="none")],
        [InlineKeyboardButton(text="🏰 Башня", callback_data="none"), InlineKeyboardButton(text="⚜️ Золото", callback_data="none")],
        [InlineKeyboardButton(text="🕹 Другие игры", callback_data="to_main_old")] # Переход к старым играм
    ])
    return text, kb

# --- НАСТРОЙКА МИН ---
@dp.callback_query(F.data == "mines_setup")
async def mines_setup(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n💣 **Мины · выбери мины!**\n. . . . . . . . . . . . . . . . . .\n💸 **Ставка:** {u['bet']} m₽"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"mines_start_{i}") for i in range(1, 4)],
        [InlineKeyboardButton(text=str(i), callback_data=f"mines_start_{i}") for i in range(4, 7)],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- СТАРТ ИГРЫ ---
@dp.callback_query(F.data.startswith("mines_start_"))
async def mines_start(callback: types.CallbackQuery):
    uid = callback.from_user.id
    count = int(callback.data.split("_")[2])
    u = get_user(uid)
    
    # Генерация поля
    all_cells = list(range(25))
    mines = random.sample(all_cells, count)
    u['game_state'] = {
        'type': 'mines',
        'mines': mines,
        'opened': [],
        'count': count,
        'multiplier': 1.0
    }
    await render_mines(callback.message, uid)

async def render_mines(message, uid, ended=False, won=False):
    u = user_db[uid]
    state = u['game_state']
    
    # Расчет следующего множителя (упрощенно)
    next_mult = round(1.2 + (len(state['opened']) * 0.2), 2)
    
    if ended:
        status = "Победа! 🎉" if won else "Проигрыш! 💥"
        text = f"👤 **{u['name']}**\n💣 **Мины · {status}**\n. . . . . . . . . . . . . . . . . .\n💣 Мины: {state['count']}\n💸 Ставка: {u['bet']} m₽"
    else:
        text = f"👤 **{u['name']}**\n🍀 **Мины · начни игру!**\n. . . . . . . . . . . . . . . . . .\n💣 Мин: {state['count']}\n💸 Ставка: {u['bet']} m₽\n\n🔢 Множитель: x{next_mult}"

    kb_rows = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i + 5):
            if j in state['opened']:
                btn_text = "💎"
            elif ended and j in state['mines']:
                btn_text = "💣"
            else:
                btn_text = "❓"
            row.append(InlineKeyboardButton(text=btn_text, callback_data=f"mines_hit_{j}" if not ended else "none"))
        kb_rows.append(row)

    if not ended:
        if len(state['opened']) > 0:
            kb_rows.append([InlineKeyboardButton(text=f"Забрать выигрыш (x{state['multiplier']}) ✅", callback_data="mines_cashout")])
        kb_rows.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    else:
        kb_rows.append([InlineKeyboardButton(text="🔄 Повторить", callback_data=f"mines_start_{state['count']}")])
        kb_rows.append([InlineKeyboardButton(text="◀️ в меню", callback_data="to_main")])

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="Markdown")

# --- ХОД В ИГРЕ ---
@dp.callback_query(F.data.startswith("mines_hit_"))
async def mines_hit(callback: types.CallbackQuery):
    uid = callback.from_user.id
    cell = int(callback.data.split("_")[2])
    u = user_db[uid]
    state = u['game_state']
    
    if cell in state['mines']:
        u['bal'] -= u['bet']
        await render_mines(callback.message, uid, ended=True, won=False)
    else:
        state['opened'].append(cell)
        state['multiplier'] = round(1.2 + (len(state['opened']) * 0.2), 2)
        await render_mines(callback.message, uid)

@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = user_db[uid]
    win_amount = int(u['bet'] * u['game_state']['multiplier'])
    u['bal'] += win_amount
    await render_mines(callback.message, uid, ended=True, won=True)

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.message()
async def auto_start(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
