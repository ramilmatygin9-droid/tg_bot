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
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- ЛОГИКА И ОФОРМЛЕНИЕ ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_games(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    bet = user_data['bet']
    btn_back = InlineKeyboardButton(text="◀️ назад", callback_data="to_main")
    
    if game == "basketball":
        text = f"Рамиль\n🏀 *Баскетбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_bask_goal")],
              [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_bask_miss")], [btn_back]]
    elif game == "football":
        text = f"Рамиль\n⚽ *Футбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")], [btn_back]]
    elif game == "darts":
        text = (f"Рамиль\n🎯 *Дартс · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 🔴 Красное (x1.94) ❞\n┕ ⚪️ Белое (x2.9)\n┕ 🎯 Центр (x5.8)\n┕ 😟 Мимо (x5.8)")
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_dart_red"), InlineKeyboardButton(text="⚪️ Белое", callback_data="play_dart_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="play_dart_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_dart_miss")], [btn_back]]
    elif game == "bowling":
        text = (f"Рамиль\n🎳 *Боулинг · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 1️⃣ - 5️⃣ кегли (x5.8) ❞\n┕ 🎳 Страйк (x5.8)\n┕ 😟 Мимо (x5.8)")
        kb = [[InlineKeyboardButton(text="1 кегла", callback_data="play_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
              [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_0")], [btn_back]]
    elif game == "dice":
        text = f"Рамиль\n🍀 *Кубик · выбери режим!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
              [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
              [InlineKeyboardButton(text="＝ Равно 3 x5.8", callback_data="play_dice_equal3")],
              [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_dice_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_dice_low")],
              [btn_back]]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- ДВИЖОК ИГРЫ ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    data = call.data.split("_")
    game_code = data[1]
    selection = data[2]
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True); return

    user_data["balance"] -= user_data["bet"]
    emojis = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲"}
    dice_msg = await call.message.answer_dice(emoji=emojis.get(game_code, "🎲"))
    
    await asyncio.sleep(4)
    val = dice_msg.dice.value
    win, multiplier, outcome_text = False, 1.0, "неизвестно"
    
    if game_code == "bask":
        is_goal = val >= 4
        multiplier = 2.4 if selection == "goal" else 1.6
        win = (selection == "goal" and is_goal) or (selection == "miss" and not is_goal)
        outcome_text = "попадание" if is_goal else "мимо"
    elif game_code == "foot":
        is_goal = val >= 3
        multiplier = 1.6 if selection == "goal" else 2.4
        win = (selection == "goal" and is_goal) or (selection == "miss" and not is_goal)
        outcome_text = "гол" if is_goal else "мимо"
    elif game_code == "dice":
        if selection == "even": win = val % 2 == 0; multiplier = 1.94
        elif selection == "odd": win = val % 2 != 0; multiplier = 1.94
        elif selection == "high": win = val > 3; multiplier = 1.94
        elif selection == "low": win = val < 3; multiplier = 2.9
        elif selection.isdigit() and int(selection) == val: win = True; multiplier = 5.8
        outcome_text = f"выпало {val}"

    # --- ИСПРАВЛЕННОЕ ОФОРМЛЕНИЕ РЕЗУЛЬТАТА ---
    if win:
        header = f"🥳 {emojis[game_code]} Победа! ✅"
        win_amount = int(user_data['bet'] * multiplier)
        user_data["balance"] += win_amount
    else:
        # Убран 🥳 при проигрыше по твоей просьбе
        header = f"{emojis[game_code]} Проигрыш ❌"
        win_amount = 0
        multiplier = 0

    res_text = (f"{header}\n"
                f"{DOTS}\n💸 *Ставка:* {user_data['bet']} m¢\n"
                f"🎲 *Выбрано:* {selection.capitalize()}\n"
                f"💰 *Выигрыш:* x{multiplier} / {win_amount} m¢\n"
                f"{DOTS}\n⚡️ *Итог:* {outcome_text}")
    
    await call.message.answer(res_text, reply_markup=main_kb())

# --- МИНЫ ---
def mines_amount_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]])

def get_mines_game_kb(user_id):
    session = game_sessions.get(user_id)
    if not session: return None
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            text = ("💎" if session['board'][idx] == 0 else "💥") if idx in session['opened'] else "❓"
            row.append(InlineKeyboardButton(text=text, callback_data="mines_ignore" if idx in session['opened'] else f"mines_open_{idx}"))
        kb.append(row)
    if not session['game_over']:
        if len(session['opened']) > 0:
            kb.append([InlineKeyboardButton(text=f"Забрать ({int(session['bet'] * session['multipliers'][len(session['opened'])-1])} m¢)", callback_data="mines_cashout")])
    else:
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить", callback_data="start_mines")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_mines")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def calculate_mines_multipliers(mines_count):
    mults = []; current_mult = 1.0
    for i in range(25 - mines_count):
        current_mult *= (25 / (25 - i)) * (1.0 + (mines_count / 100.0))
        mults.append(round(current_mult, 2))
    return mults

@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    await call.message.edit_text(f"Рамиль\n💣 *Мины*\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢", reply_markup=mines_amount_kb())

@dp.callback_query(F.data.startswith("setmines_"))
async def set_mines_and_start(call: types.CallbackQuery):
    user_data['mines_count'] = int(call.data.split("_")[1])
    await start_mines_game(call)

async def start_mines_game(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_data["balance"] < user_data['bet']:
        await call.answer("❌ Недостаточно m¢!", show_alert=True); return
    user_data["balance"] -= user_data['bet']
    board = [0]*25
    for idx in random.sample(range(25), user_data['mines_count']): board[idx] = 1
    game_sessions[user_id] = {'board': board, 'bet': user_data['bet'], 'mines_count': user_data['mines_count'], 'opened': [], 'multipliers': calculate_mines_multipliers(user_data['mines_count']), 'game_over': False, 'won': False}
    await call.message.edit_text(f"Рамиль\n💣 *Мины*\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢", reply_markup=get_mines_game_kb(user_id))

@dp.callback_query(F.data.startswith("mines_open_"))
async def mines_open_cell(call: types.CallbackQuery):
    user_id = call.from_user.id
    session = game_sessions.get(user_id)
    if not session or session['game_over']: return
    idx = int(call.data.split("_")[2])
    session['opened'].append(idx)
    if session['board'][idx] == 1:
        session['game_over'] = True
        msg = "💥 Проигрыш!"
    else:
        msg = "💎 Игра идёт..."
    await call.message.edit_text(f"Рамиль\n💣 *Мины · {msg}*\n{DOTS}\n💸 Ставка: {session['bet']} m¢", reply_markup=get_mines_game_kb(user_id))

@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(call: types.CallbackQuery):
    user_id = call.from_user.id
    session = game_sessions.get(user_id)
    if not session or session['game_over']: return
    session['game_over'] = session['won'] = True
    user_data["balance"] += int(session['bet'] * session['multipliers'][len(session['opened'])-1])
    await call.message.edit_text("💰 Выигрыш забран!", reply_markup=get_mines_game_kb(user_id))

# --- ОБЩИЕ КОМАНДЫ ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    game_sessions.pop(call.from_user.id, None)
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data.startswith("bet_"))
async def change_bet(call: types.CallbackQuery):
    action = call.data.split("_")[1]
    if action == "up": user_data["bet"] += 10
    elif action == "down" and user_data["bet"] > 5: user_data["bet"] -= 5
    elif action == "reset": user_data["bet"] = 10
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢\n🔥 Ставка: {user_data['bet']}", reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    await call.answer(f"👤 Профиль\nБаланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data == "mines_ignore")
async def ignore(call: types.CallbackQuery): await call.answer()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
