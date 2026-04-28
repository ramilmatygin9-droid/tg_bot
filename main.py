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

# Данные пользователя
user_data = {"balance": 1000, "bet": 10}
game_sessions = {} 
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- ГЛАВНОЕ МЕНЮ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basketball"),
            InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football"),
            InlineKeyboardButton(text="🎯 Дартс", callback_data="game_darts"),
            InlineKeyboardButton(text="🎳 Боулинг", callback_data="game_bowling"),
            InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice")
        ],
        [
            InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"),
            InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")
        ],
        [
            InlineKeyboardButton(text="📝 Ставка: " + str(user_data['bet']) + "¢", callback_data="change_bet"),
            InlineKeyboardButton(text="💰 Баланс: " + str(user_data['balance']) + "¢", callback_data="show_balance")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ])

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (f"🎮 **ДОБРО ПОЖАЛОВАТЬ В КАЗИНО!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await message.answer(text, reply_markup=main_kb())

@dp.callback_query(F.data == "main_menu")
async def main_menu(call: types.CallbackQuery):
    text = (f"🎮 **ГЛАВНОЕ МЕНЮ**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢")
    await call.message.edit_text(text, reply_markup=main_kb())

@dp.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    await call.answer(f"💰 Баланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    bets = [10, 25, 50, 100, 250, 500]
    current = user_data['bet']
    try:
        next_idx = (bets.index(current) + 1) % len(bets)
        user_data['bet'] = bets[next_idx]
    except:
        user_data['bet'] = 10
    
    # Обновляем кнопку
    new_kb = main_kb()
    await call.message.edit_reply_markup(reply_markup=new_kb)
    await call.answer(f"💸 Ставка изменена на {user_data['bet']} m¢")

# --- ИГРЫ ---
@dp.callback_query(F.data.startswith("game_"))
async def start_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    
    if game == "basketball":
        await basketball_game(call)
    elif game == "football":
        await football_game(call)
    elif game == "darts":
        await darts_game(call)
    elif game == "bowling":
        await bowling_game(call)
    elif game == "dice":
        await dice_game(call)
    elif game == "mines":
        await mines_menu(call)
    elif game == "slots":
        await slots_game(call)

# --- БАСКЕТБОЛ ---
async def basketball_game(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Попадание (x2.4)", callback_data="play_basketball_goal")],
        [InlineKeyboardButton(text="🙈 Промах (x1.6)", callback_data="play_basketball_miss")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        f"🏀 **БАСКЕТБОЛ**\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢\n\nВыбери исход:",
        reply_markup=kb
    )

# --- ФУТБОЛ ---
async def football_game(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚽ Гол (x1.6)", callback_data="play_football_goal")],
        [InlineKeyboardButton(text="🥅 Промах (x2.4)", callback_data="play_football_miss")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        f"⚽ **ФУТБОЛ**\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢\n\nВыбери исход:",
        reply_markup=kb
    )

# --- ДАРТС ---
async def darts_game(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x1.94)", callback_data="play_darts_red")],
        [InlineKeyboardButton(text="⚪ Белое (x2.9)", callback_data="play_darts_white")],
        [InlineKeyboardButton(text="🎯 Центр (x5.8)", callback_data="play_darts_center")],
        [InlineKeyboardButton(text="😟 Мимо (x5.8)", callback_data="play_darts_miss")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        f"🎯 **ДАРТС**\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢\n\nВыбери сектор:",
        reply_markup=kb
    )

# --- БОУЛИНГ ---
async def bowling_game(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎳 Страйк (x5.8)", callback_data="play_bowling_strike")],
        [InlineKeyboardButton(text="1-5 кегль (x2.4)", callback_data="play_bowling_low")],
        [InlineKeyboardButton(text="😟 Мимо (x5.8)", callback_data="play_bowling_miss")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        f"🎳 **БОУЛИНГ**\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢\n\nВыбери результат:",
        reply_markup=kb
    )

# --- КУБИК ---
async def dice_game(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="play_dice_1"),
         InlineKeyboardButton(text="2", callback_data="play_dice_2"),
         InlineKeyboardButton(text="3", callback_data="play_dice_3")],
        [InlineKeyboardButton(text="4", callback_data="play_dice_4"),
         InlineKeyboardButton(text="5", callback_data="play_dice_5"),
         InlineKeyboardButton(text="6", callback_data="play_dice_6")],
        [InlineKeyboardButton(text="🎲 Четное (x1.94)", callback_data="play_dice_even")],
        [InlineKeyboardButton(text="🎲 Нечетное (x1.94)", callback_data="play_dice_odd")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        f"🎲 **КУБИК**\n{DOTS}\n💸 Ставка: {user_data['bet']} m¢\n\nУгадай число:",
        reply_markup=kb
    )

# --- СЛОТЫ ---
async def slots_game(call: types.CallbackQuery):
    await call.message.edit_text("🎰 **СЛОТЫ**\n{DOTS}\nКручу барабаны...")
    
    # Проверка баланса
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        await main_menu(call)
        return
    
    # Списываем ставку
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    # Эмуляция слота
    symbols = ["🍒", "🍊", "🍋", "🍉", "🔔", "💎", "7️⃣"]
    reel1 = random.choice(symbols)
    reel2 = random.choice(symbols)
    reel3 = random.choice(symbols)
    
    # Проверка выигрыша
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
        result_text = f"✅ **ПОБЕДА!**\n💰 Выигрыш: x{multiplier} = {win_amount} m¢"
    else:
        result_text = f"❌ **ПРОИГРЫШ!**\n💸 Потеряно: {bet} m¢"
    
    text = (f"🎰 **СЛОТЫ**\n{DOTS}\n"
            f"[ {reel1} ] [ {reel2} ] [ {reel3} ]\n{DOTS}\n"
            f"{result_text}\n"
            f"💰 Баланс: {user_data['balance']} m¢")
    
    await call.message.edit_text(text, reply_markup=main_kb())

# --- ОБРАБОТКА ИГР ---
@dp.callback_query(F.data.startswith("play_"))
async def play_game(call: types.CallbackQuery):
    # Проверка баланса
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        await main_menu(call)
        return
    
    parts = call.data.split("_")
    game = parts[1]
    selection = parts[2]
    
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    # Отправляем анимацию
    emojis = {
        "basketball": "🏀",
        "football": "⚽", 
        "darts": "🎯",
        "bowling": "🎳",
        "dice": "🎲"
    }
    
    msg = await call.message.answer_dice(emoji=emojis.get(game, "🎲"))
    await asyncio.sleep(3)
    dice_value = msg.dice.value
    
    # Логика выигрыша
    win = False
    multiplier = 0
    
    if game == "basketball":
        if selection == "goal":
            win = dice_value >= 5
            multiplier = 2.4 if win else 0
        else:
            win = dice_value <= 2
            multiplier = 1.6 if win else 0
            
    elif game == "football":
        if selection == "goal":
            win = dice_value >= 5
            multiplier = 1.6 if win else 0
        else:
            win = dice_value <= 2
            multiplier = 2.4 if win else 0
            
    elif game == "darts":
        if selection == "red":
            win = dice_value in [1, 2]
            multiplier = 1.94 if win else 0
        elif selection == "white":
            win = dice_value in [3, 4]
            multiplier = 2.9 if win else 0
        elif selection == "center":
            win = dice_value == 5
            multiplier = 5.8 if win else 0
        elif selection == "miss":
            win = dice_value == 6
            multiplier = 5.8 if win else 0
            
    elif game == "bowling":
        if selection == "strike":
            win = dice_value == 6
            multiplier = 5.8 if win else 0
        elif selection == "low":
            win = 1 <= dice_value <= 5
            multiplier = 2.4 if win else 0
        elif selection == "miss":
            win = dice_value == 1
            multiplier = 5.8 if win else 0
            
    elif game == "dice":
        if selection.isdigit():
            win = dice_value == int(selection)
            multiplier = 5.8 if win else 0
        elif selection == "even":
            win = dice_value % 2 == 0
            multiplier = 1.94 if win else 0
        elif selection == "odd":
            win = dice_value % 2 == 1
            multiplier = 1.94 if win else 0
    
    # Начисляем выигрыш
    if win:
        win_amount = int(bet * multiplier)
        user_data["balance"] += win_amount
        result_text = f"✅ **ПОБЕДА!**\n💰 Выигрыш: x{multiplier} = {win_amount} m¢"
    else:
        result_text = f"❌ **ПРОИГРЫШ!**\n💸 Потеряно: {bet} m¢"
    
    text = (f"🎲 **Выпало:** {dice_value}\n"
            f"📊 **Выбор:** {selection}\n{DOTS}\n"
            f"{result_text}\n{DOTS}\n"
            f"💰 **Баланс:** {user_data['balance']} m¢")
    
    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()

# --- МИНЫ ---
async def mines_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 💣", callback_data="mines_1"),
         InlineKeyboardButton(text="2 💣", callback_data="mines_2"),
         InlineKeyboardButton(text="3 💣", callback_data="mines_3")],
        [InlineKeyboardButton(text="4 💣", callback_data="mines_4"),
         InlineKeyboardButton(text="5 💣", callback_data="mines_5"),
         InlineKeyboardButton(text="6 💣", callback_data="mines_6")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(
        f"💣 **МИНЫ**\n{DOTS}\n"
        f"💸 Ставка: {user_data['bet']} m¢\n\n"
        f"Выбери количество мин на поле 5x5:",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("mines_"))
async def start_mines(call: types.CallbackQuery):
    mines_count = int(call.data.split("_")[1])
    user_id = call.from_user.id
    
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        await main_menu(call)
        return
    
    user_data["balance"] -= user_data["bet"]
    bet = user_data["bet"]
    
    # Создаем поле
    board = [0] * 25
    mine_positions = random.sample(range(25), mines_count)
    for pos in mine_positions:
        board[pos] = 1
    
    game_sessions[user_id] = {
        'board': board,
        'bet': bet,
        'mines': mines_count,
        'opened': [],
        'game_over': False
    }
    
    await show_mines_field(call, user_id)

async def show_mines_field(call: types.CallbackQuery, user_id: int):
    s = game_sessions.get(user_id)
    if not s:
        return
    
    kb = []
    for i in range(5):
        row = []
        for j in range(5):
            idx = i * 5 + j
            if idx in s['opened']:
                if s['board'][idx] == 1:
                    row.append(InlineKeyboardButton(text="💣", callback_data="mines_no"))
                else:
                    row.append(InlineKeyboardButton(text="💎", callback_data="mines_no"))
            else:
                row.append(InlineKeyboardButton(text="❓", callback_data=f"mines_open_{idx}"))
        kb.append(row)
    
    # Добавляем кнопки управления
    kb.append([InlineKeyboardButton(text="💰 Забрать выигрыш", callback_data="mines_cashout")])
    kb.append([InlineKeyboardButton(text="◀️ Выйти", callback_data="main_menu")])
    
    # Считаем множитель
    opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
    total_safe = 25 - s['mines']
    multiplier = 1.0
    if opened_safe > 0:
        multiplier = 1 + (opened_safe / total_safe) * 2
        multiplier = min(multiplier, 8)
    
    text = (f"💣 **МИНЫ**\n{DOTS}\n"
            f"💣 Мин: {s['mines']}\n"
            f"💸 Ставка: {s['bet']} m¢\n"
            f"🔓 Открыто: {opened_safe}/{total_safe}\n"
            f"💰 Множитель: x{multiplier:.2f}")
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("mines_open_"))
async def open_mines_cell(call: types.CallbackQuery):
    user_id = call.from_user.id
    s = game_sessions.get(user_id)
    
    if not s or s['game_over']:
        await call.answer("Игра не активна!")
        return
    
    idx = int(call.data.split("_")[2])
    
    if idx in s['opened']:
        await call.answer("Клетка уже открыта!")
        return
    
    s['opened'].append(idx)
    
    if s['board'][idx] == 1:
        s['game_over'] = True
        text = (f"💥 **ВЗРЫВ! Ты наступил на мину!**\n{DOTS}\n"
                f"💣 Мин: {s['mines']}\n"
                f"💸 Ставка: {s['bet']} m¢\n"
                f"💀 Потеряно: {s['bet']} m¢\n"
                f"💰 Баланс: {user_data['balance']} m¢")
        await call.message.edit_text(text, reply_markup=main_kb())
        del game_sessions[user_id]
    else:
        await show_mines_field(call, user_id)

@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(call: types.CallbackQuery):
    user_id = call.from_user.id
    s = game_sessions.get(user_id)
    
    if not s or s['game_over']:
        await call.answer("Нечего забирать!")
        return
    
    opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
    total_safe = 25 - s['mines']
    multiplier = 1.0
    if opened_safe > 0:
        multiplier = 1 + (opened_safe / total_safe) * 2
        multiplier = min(multiplier, 8)
    
    win_amount = int(s['bet'] * multiplier)
    user_data["balance"] += win_amount
    
    text = (f"💰 **ТЫ ЗАБРАЛ ВЫИГРЫШ!**\n{DOTS}\n"
            f"💸 Ставка: {s['bet']} m¢\n"
            f"🎲 Множитель: x{multiplier:.2f}\n"
            f"✅ Выигрыш: {win_amount} m¢\n"
            f"💰 Новый баланс: {user_data['balance']} m¢")
    
    await call.message.edit_text(text, reply_markup=main_kb())
    del game_sessions[user_id]

@dp.callback_query(F.data == "mines_no")
async def mines_no(call: types.CallbackQuery):
    await call.answer("⏳ Игра не активна, начни новую!")

async def main():
    print("🤖 ИГРОВОЙ БОТ ЗАПУЩЕН!")
    print(f"💰 Начальный баланс: {user_data['balance']} m¢")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
