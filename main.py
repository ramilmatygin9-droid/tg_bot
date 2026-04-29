import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 

bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# Имитация БД
user_data = {"balance": 1000, "bet": 10, "mines_count": 3}
game_sessions = {} 
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---

# Главное меню (Обновленный интерфейс)
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
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_modes")
        ],
        [
            InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url="https://google.com"))
        ],
        [
            InlineKeyboardButton(text="📝 Изменить ставку", callback_data="change_bet"),
            InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance")
        ]
    ])

# Меню режимов
def modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"), InlineKeyboardButton(text="Алмазы 💠", callback_data="under_dev")],
        [InlineKeyboardButton(text="🧱 Башня", callback_data="under_dev"), InlineKeyboardButton(text="Золото ⚜️", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="HiLo ⬇️", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21(Очко)", callback_data="under_dev"), InlineKeyboardButton(text="Пирамида 🏜", callback_data="under_dev")],
        [InlineKeyboardButton(text="🥊 Арена", callback_data="under_dev")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- НОВАЯ ИГРА: КРУТИЛКА (МОЁ ДОБАВЛЕНИЕ) ---
def wheel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="wheel_red")],
        [InlineKeyboardButton(text="⚫ Черное (x2)", callback_data="wheel_black")],
        [InlineKeyboardButton(text="🟢 Зеленое (x14)", callback_data="wheel_green")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- НОВАЯ ИГРА: КАМЕНЬ-НОЖНИЦЫ-БУМАГА (МОЁ ДОБАВЛЕНИЕ) ---
def rps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪨 Камень (x2)", callback_data="rps_rock")],
        [InlineKeyboardButton(text="✂️ Ножницы (x2)", callback_data="rps_scissors")],
        [InlineKeyboardButton(text="📄 Бумага (x2)", callback_data="rps_paper")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- ЛОГИКА ИГР ---

@dp.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    await call.answer(f"💰 Баланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data == "menu_modes")
async def show_modes(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=modes_kb())

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
    elif game == "slots":
        text = f"Рамиль\n🎰 *Слоты · крути барабаны!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="🎰 КРУТИТЬ", callback_data="play_slots_spin")], [btn_back]]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    # Проверка баланса
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    
    data = call.data.split("_")
    game_code = data[1]
    selection = data[2] if len(data) > 2 else "spin"
    
    # Списываем ставку
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    # СЛОТЫ (НОВАЯ ИГРА)
    if game_code == "slots":
        symbols = ["🍒", "🍊", "🍋", "🍉", "🔔", "💎", "7️⃣"]
        reel1 = random.choice(symbols)
        reel2 = random.choice(symbols)
        reel3 = random.choice(symbols)
        
        win = False
        multiplier = 0
        
        if reel1 == reel2 == reel3:
            if reel1 == "7️⃣":
                multiplier = 10
            elif reel1 == "💎":
                multiplier = 8
            elif reel1 == "🔔":
                multiplier = 5
            else:
                multiplier = 3
            win = True
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            multiplier = 2
            win = True
        
        if win:
            win_amount = int(bet * multiplier)
            user_data["balance"] += win_amount
            result_text = f"✅ ПОБЕДА! x{multiplier} = {win_amount} m¢"
        else:
            result_text = f"❌ ПРОИГРЫШ! -{bet} m¢"
        
        text = (f"🎰 **СЛОТЫ**\n{DOTS}\n"
                f"[ {reel1} ] [ {reel2} ] [ {reel3} ]\n{DOTS}\n"
                f"{result_text}\n"
                f"💰 Баланс: {user_data['balance']} m¢")
        
        await call.message.answer(text, reply_markup=main_kb())
        await call.message.delete()
        return
    
    # Обычные игры с кубиком
    emojis = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲"}
    dice_msg = await call.message.answer_dice(emoji=emojis.get(game_code, "🎲"))
    await asyncio.sleep(3)
    val = dice_msg.dice.value
    
    win = False
    multiplier = 0
    outcome_text = ""
    
    # ЛОГИКА БАСКЕТБОЛ
    if game_code == "bask":
        if selection == "goal":
            win = val >= 5
            multiplier = 2.4 if win else 0
        else:
            win = val <= 2
            multiplier = 1.6 if win else 0
    
    # ЛОГИКА ФУТБОЛ
    elif game_code == "foot":
        if selection == "goal":
            win = val >= 5
            multiplier = 1.6 if win else 0
        else:
            win = val <= 2
            multiplier = 2.4 if win else 0
    
    # ЛОГИКА ДАРТС
    elif game_code == "dart":
        if selection == "red":
            win = val in [1, 2]
            multiplier = 1.94 if win else 0
        elif selection == "white":
            win = val in [3, 4]
            multiplier = 2.9 if win else 0
        elif selection == "center":
            win = val == 5
            multiplier = 5.8 if win else 0
        elif selection == "miss":
            win = val == 6
            multiplier = 5.8 if win else 0
    
    # ЛОГИКА БОУЛИНГ
    elif game_code == "bowl":
        if selection == "6":
            win = val == 6
            multiplier = 5.8 if win else 0
        elif selection == "0":
            win = val == 1
            multiplier = 5.8 if win else 0
        else:
            k = int(selection)
            win = 1 <= val <= 5
            multiplier = 5.8 if win else 0
    
    # ЛОГИКА КУБИК
    elif game_code == "dice":
        if selection.isdigit():
            win = val == int(selection)
            multiplier = 5.8 if win else 0
        elif selection == "even":
            win = val % 2 == 0
            multiplier = 1.94 if win else 0
        elif selection == "odd":
            win = val % 2 == 1
            multiplier = 1.94 if win else 0
        elif selection == "equal3":
            win = val == 3
            multiplier = 5.8 if win else 0
        elif selection == "high":
            win = val > 3
            multiplier = 1.94 if win else 0
        elif selection == "low":
            win = val < 3
            multiplier = 2.9 if win else 0
    
    # Начисляем выигрыш
    if win:
        win_amount = int(bet * multiplier)
        user_data["balance"] += win_amount
        header = f"🥳 ПОБЕДА! ✅"
        outcome_text = f"💰 Выигрыш: x{multiplier} = {win_amount} m¢"
    else:
        header = f"😭 ПРОИГРЫШ ❌"
        outcome_text = f"💸 Потеряно: {bet} m¢"
    
    res_text = (f"{header}\n{DOTS}\n"
                f"💸 *Ставка:* {bet} m¢\n"
                f"🎲 *Выбрано:* {selection}\n"
                f"🎯 *Выпало:* {val}\n"
                f"{DOTS}\n"
                f"{outcome_text}\n"
                f"💰 *Баланс:* {user_data['balance']} m¢")
    
    await call.message.answer(res_text, reply_markup=main_kb())
    await call.message.delete()

# --- НОВЫЕ ИГРЫ (МОЁ ДОБАВЛЕНИЕ) ---

# КРУТИЛКА (РУЛЕТКА)
@dp.callback_query(F.data.startswith("wheel_"))
async def wheel_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    
    color = call.data.split("_")[1]
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    # Эмуляция кручения
    msg = await call.message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)
    
    # Цвета: 0-красное, 1-черное, 2-зеленое
    colors = ["🔴", "⚫", "🟢"]
    results = ["Красное", "Черное", "Зеленое"]
    result_idx = random.randint(0, 12)
    
    if result_idx == 0:
        result = 2  # зеленое (шанс 1/13)
    elif result_idx <= 6:
        result = 0  # красное
    else:
        result = 1  # черное
    
    win = False
    multiplier = 0
    
    if color == "red" and result == 0:
        win = True
        multiplier = 2
    elif color == "black" and result == 1:
        win = True
        multiplier = 2
    elif color == "green" and result == 2:
        win = True
        multiplier = 14
    
    if win:
        win_amount = int(bet * multiplier)
        user_data["balance"] += win_amount
        text = (f"🎡 **РУЛЕТКА**\n{DOTS}\n"
                f"🎯 Выпало: {colors[result]} {results[result]}\n"
                f"✅ ПОБЕДА! x{multiplier} = {win_amount} m¢\n"
                f"💰 Баланс: {user_data['balance']} m¢")
    else:
        text = (f"🎡 **РУЛЕТКА**\n{DOTS}\n"
                f"🎯 Выпало: {colors[result]} {results[result]}\n"
                f"❌ ПРОИГРЫШ! -{bet} m¢\n"
                f"💰 Баланс: {user_data['balance']} m¢")
    
    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()

# КАМЕНЬ-НОЖНИЦЫ-БУМАГА
@dp.callback_query(F.data.startswith("rps_"))
async def rps_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    
    player_choice = call.data.split("_")[1]
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    choices = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📄 Бумага"}
    bot_choice = random.choice(["rock", "scissors", "paper"])
    
    # Логика победы
    if player_choice == bot_choice:
        win = False
        multiplier = 0
        result_text = "🤝 НИЧЬЯ! Ставка возвращена"
        user_data["balance"] += bet
    elif (player_choice == "rock" and bot_choice == "scissors") or \
         (player_choice == "scissors" and bot_choice == "paper") or \
         (player_choice == "paper" and bot_choice == "rock"):
        win = True
        multiplier = 2
        win_amount = int(bet * multiplier)
        user_data["balance"] += win_amount
        result_text = f"✅ ПОБЕДА! +{win_amount} m¢"
    else:
        win = False
        multiplier = 0
        result_text = f"❌ ПРОИГРЫШ! -{bet} m¢"
    
    text = (f"🪨✂️📄 **КАМЕНЬ-НОЖНИЦЫ-БУМАГА**\n{DOTS}\n"
            f"👉 Ты: {choices[player_choice]}\n"
            f"👈 Бот: {choices[bot_choice]}\n{DOTS}\n"
            f"{result_text}\n"
            f"💰 Баланс: {user_data['balance']} m¢")
    
    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()

# --- МИНЫ ---

def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")]
    ])

@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    text = f"Рамиль\n💣 *Мины · выбери мины!*\n{DOTS}\n💸 *Ставка: {user_data['bet']} m¢*"
    await call.message.edit_text(text, reply_markup=mines_start_kb())

@dp.callback_query(F.data == "mines_double")
async def mines_double(call: types.CallbackQuery):
    user_data['bet'] *= 2
    await call.answer(f"💸 Ставка удвоена! Теперь: {user_data['bet']} m¢")
    await mines_menu(call)

@dp.callback_query(F.data.startswith("setmines_"))
async def start_mines_game(call: types.CallbackQuery):
    m_count = int(call.data.split("_")[1])
    user_id = call.from_user.id
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    user_data["balance"] -= user_data["bet"]
    board = [0]*25
    for idx in random.sample(range(25), m_count):
        board[idx] = 1
    game_sessions[user_id] = {'board': board, 'bet': user_data['bet'], 'mines': m_count, 'opened': [], 'game_over': False}
    await call.message.edit_text(f"Рамиль\n🍀 *Мины · начни игру!*\n{DOTS}\n💣 *Мин: {m_count}*\n💸 *Ставка: {user_data['bet']} m¢*", reply_markup=get_mines_board_kb(user_id))

def get_mines_board_kb(user_id):
    s = game_sessions.get(user_id)
    if not s:
        return mines_start_kb()
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            if idx in s['opened']:
                char = "💥" if s['board'][idx] == 1 else "💎"
            else:
                char = "❓"
            row.append(InlineKeyboardButton(text=char, callback_data=f"mopen_{idx}"))
        kb.append(row)
    if not s['game_over']:
        opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
        total_safe = 25 - s['mines']
        multiplier = 1.0
        if opened_safe > 0:
            multiplier = 1 + (opened_safe / total_safe) * 2
        kb.append([InlineKeyboardButton(text=f"💰 Забрать x{multiplier:.2f}", callback_data="m_cashout")])
        kb.append([InlineKeyboardButton(text="◀️ Выход", callback_data="to_main")])
    else:
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {s['bet']} m¢", callback_data=f"setmines_{s['mines']}")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.callback_query(F.data.startswith("mopen_"))
async def mines_step(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    s = game_sessions.get(call.from_user.id)
    if not s or s['game_over'] or idx in s['opened']:
        return
    s['opened'].append(idx)
    if s['board'][idx] == 1:
        s['game_over'] = True
        text = f"Рамиль\n💥 *Мины · Проигрыш!*\n{DOTS}\n💣 *Мин: {s['mines']}*\n💸 *Ставка: {s['bet']} m¢*\n💰 *Баланс: {user_data['balance']} m¢*"
    else:
        opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
        total_safe = 25 - s['mines']
        multiplier = 1 + (opened_safe / total_safe) * 2
        text = f"Рамиль\n💎 *Мины · игра идёт.*\n{DOTS}\n💣 *Мин: {s['mines']}*\n💸 *Ставка: {s['bet']} m¢*\n💰 *Множитель: x{multiplier:.2f}*"
    await call.message.edit_text(text, reply_markup=get_mines_board_kb(call.from_user.id))

@dp.callback_query(F.data == "m_cashout")
async def mines_cashout(call: types.CallbackQuery):
    user_id = call.from_user.id
    s = game_sessions.get(user_id)
    if not s or s['game_over']:
        return
    opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
    total_safe = 25 - s['mines']
    multiplier = 1.0
    if opened_safe > 0:
        multiplier = 1 + (opened_safe / total_safe) * 2
    win_amount = int(s['bet'] * multiplier)
    user_data["balance"] += win_amount
    text = (f"Рамиль\n💰 *Ты забрал выигрыш!*\n{DOTS}\n"
            f"💸 *Ставка:* {s['bet']} m¢\n"
            f"🎲 *Множитель:* x{multiplier:.2f}\n"
            f"✅ *Выигрыш:* {win_amount} m¢\n"
            f"💰 *Новый баланс:* {user_data['balance']} m¢")
    await call.message.edit_text(text, reply_markup=main_kb())
    del game_sessions[user_id]

# --- ОБЩЕЕ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await message.answer(text, reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=main_kb())

@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    bets = [10, 25, 50, 100, 250, 500, 1000]
    current = user_data['bet']
    next_idx = (bets.index(current) + 1) % len(bets)
    user_data['bet'] = bets[next_idx]
    await call.answer(f"💸 Ставка изменена на {user_data['bet']} m¢")
    await back_to_main(call)

@dp.callback_query(F.data == "under_dev")
async def dev(call: types.CallbackQuery):
    await call.answer("🚧 В разработке", show_alert=True)

async def main():
    print("🤖 ИГРОВОЙ БОТ ЗАПУЩЕН!")
    print(f"💰 Начальный баланс: {user_data['balance']} m¢")
    print("🎮 Доступны игры: Баскетбол, Футбол, Дартс, Боулинг, Кубик, Слоты, Мины, Рулетка, Камень-ножницы-бумага")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
