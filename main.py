import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 

bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# Имитация БД
user_data = {"balance": 1000, "bet": 10, "mines_count": 3}
game_sessions = {} 
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
            InlineKeyboardButton(text="🎳", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰", callback_data="prep_slots")
        ],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_mines")
        ],
        [
            InlineKeyboardButton(text="⬇️ 5 💰", callback_data="bet_down"),
            InlineKeyboardButton(text="10 💰", callback_data="bet_reset"),
            InlineKeyboardButton(text="⬆️ 20 💰", callback_data="bet_up")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Повторить игру 🔄", callback_data="to_main")]
    ])

def mines_amount_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double_bet")],
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

def get_mines_game_kb(user_id):
    session = game_sessions.get(user_id)
    if not session: return None
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            if idx in session['opened']:
                text = "💎" if session['board'][idx] == 0 else "💥"
                row.append(InlineKeyboardButton(text=text, callback_data="mines_ignore"))
            else:
                row.append(InlineKeyboardButton(text="❓", callback_data=f"mines_open_{idx}"))
        kb.append(row)
    if not session['game_over']:
        if len(session['opened']) > 0:
            current_mult = session['multipliers'][len(session['opened']) - 1]
            win_cash = int(session['bet'] * current_mult)
            kb.append([InlineKeyboardButton(text=f"Забрать выигрыш ✅ ({win_cash} m¢)", callback_data="mines_cashout")])
        kb.append([InlineKeyboardButton(text="Честность 🔑", callback_data="mines_provably")])
    else:
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {session['bet']} m¢", callback_data="start_mines")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_mines"), InlineKeyboardButton(text="Честность 🔑", callback_data="mines_provably")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ЛОГИКА МИН ---
def calculate_mines_multipliers(mines_count):
    mults = []
    current_mult = 1.0
    for i in range(25 - mines_count):
        current_mult *= (25 - i) / (25 - i - mines_count)
        mults.append(round(current_mult * 0.95, 2)) # 0.95 - небольшая комиссия
    return mults

def generate_mines_text(user_id, status_icon="💣", status_text="начни игру!"):
    session = game_sessions.get(user_id)
    bet = session['bet'] if session else user_data['bet']
    mines = session['mines_count'] if session else user_data['mines_count']
    text = f"Рамиль\n{status_icon} *Мины · {status_text}*\n{DOTS}\n💣 *Мин: {mines}*\n💸 *Ставка: {bet} m¢*"
    if session:
        opened_count = len(session['opened'])
        if not session['game_over']:
            if opened_count > 0:
                text += f"\n📈 *Выигрыш: x{session['multipliers'][opened_count-1]} / {int(bet*session['multipliers'][opened_count-1])} m¢*"
            next_mults = session['multipliers'][opened_count : opened_count + 5]
            text += f"\n\n🧮 *Следующий множитель:*\n┕ {' ➡️ '.join([f'x{m}' for m in next_mults])} ❞"
        else:
            if session['won']:
                text += f"\n✅ *Выигрыш забран! x{session['multipliers'][opened_count-1]}*"
            else:
                text += f"\n💥 *Проигрыш! Открыто: {opened_count}*"
    return text

@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    await call.message.edit_text(f"Рамиль\n💣 *Мины · выбери мины!*\n{DOTS}\n💸 *Ставка: {user_data['bet']} m¢*", reply_markup=mines_amount_kb())

@dp.callback_query(F.data.startswith("setmines_"))
async def set_mines_start(call: types.CallbackQuery):
    user_data['mines_count'] = int(call.data.split("_")[1])
    await start_mines_game(call)

@dp.callback_query(F.data == "start_mines")
async def repeat_mines(call: types.CallbackQuery):
    await start_mines_game(call)

async def start_mines_game(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_data["balance"] < user_data['bet']:
        await call.answer("❌ Недостаточно m¢!", show_alert=True); return
    user_data["balance"] -= user_data['bet']
    board = [0]*25
    for idx in random.sample(range(25), user_data['mines_count']): board[idx] = 1
    game_sessions[user_id] = {'board': board, 'bet': user_data['bet'], 'mines_count': user_data['mines_count'], 'opened': [], 'multipliers': calculate_mines_multipliers(user_data['mines_count']), 'game_over': False, 'won': False}
    await call.message.edit_text(generate_mines_text(user_id), reply_markup=get_mines_game_kb(user_id))

@dp.callback_query(F.data.startswith("mines_open_"))
async def mines_step(call: types.CallbackQuery):
    user_id = call.from_user.id
    session = game_sessions.get(user_id)
    if not session or session['game_over']: return
    idx = int(call.data.split("_")[2])
    session['opened'].append(idx)
    if session['board'][idx] == 1:
        session['game_over'] = True
    elif len(session['opened']) == (25 - session['mines_count']):
        session['game_over'] = session['won'] = True
        user_data['balance'] += int(session['bet'] * session['multipliers'][-1])
    await call.message.edit_text(generate_mines_text(user_id, "💥" if session['game_over'] and not session['won'] else "💎", "игра идёт."), reply_markup=get_mines_game_kb(user_id))

@dp.callback_query(F.data == "mines_cashout")
async def mines_win(call: types.CallbackQuery):
    session = game_sessions.get(call.from_user.id)
    if not session or session['game_over']: return
    session['game_over'] = session['won'] = True
    user_data['balance'] += int(session['bet'] * session['multipliers'][len(session['opened'])-1])
    await call.message.edit_text(generate_mines_text(call.from_user.id, "💰", "Победа!"), reply_markup=get_mines_game_kb(call.from_user.id))

# --- КНОПКИ СТАВОК И ПРОФИЛЬ ---
@dp.callback_query(F.data.startswith("bet_"))
async def change_bet(call: types.CallbackQuery):
    a = call.data.split("_")[1]
    if a == "up": user_data["bet"] += 10
    elif a == "down" and user_data["bet"] > 5: user_data["bet"] -= 5
    elif a == "reset": user_data["bet"] = 10
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢\n🔥 Ставка: {user_data['bet']}", reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def view_profile(call: types.CallbackQuery):
    await call.answer(f"👤 Профиль\n💰 Баланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
