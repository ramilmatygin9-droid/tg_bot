import asyncio
import random
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk"

bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# БАЗА ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ
users_db = {}
game_sessions = {}
DOTS = "···················"

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ---
def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 1000,
            "bet": 10,
            "mines_count": 3,
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0
        }
    return users_db[user_id]


def update_balance(user_id, amount):
    user = get_user(user_id)
    old_balance = user["balance"]
    user["balance"] += amount
    if amount != 0:
        user["total_games"] += 1
        if amount > 0:
            user["total_wins"] += 1
        elif amount < 0:
            user["total_losses"] += 1
    print(f"💰 Пользователь {user_id}: {old_balance} → {user['balance']} ({'+' if amount > 0 else ''}{amount})")
    return user["balance"]


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
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_modes")
        ],
        [
            InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url="https://ramilmatygin9-droid.github.io/GLITCH-WIN/"))
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance"),
            InlineKeyboardButton(text="📝 Ставка", callback_data="change_bet"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")
        ]
    ])


def modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"), InlineKeyboardButton(text="💎 Алмазы", callback_data="under_dev")],
        [InlineKeyboardButton(text="🧱 Башня", callback_data="under_dev"), InlineKeyboardButton(text="⚜️ Золото", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="⬇️ HiLo", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21", callback_data="under_dev"), InlineKeyboardButton(text="🏜 Пирамида", callback_data="under_dev")],
        [InlineKeyboardButton(text="🥊 Арена", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])


def slots_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 КРУТИТЬ", callback_data="play_slots")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])


def wheel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="wheel_red")],
        [InlineKeyboardButton(text="⚫ Черное (x2)", callback_data="wheel_black")],
        [InlineKeyboardButton(text="🟢 Зеленое (x14)", callback_data="wheel_green")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])


def rps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪨 Камень (x2)", callback_data="rps_rock")],
        [InlineKeyboardButton(text="✂️ Ножницы (x2)", callback_data="rps_scissors")],
        [InlineKeyboardButton(text="📄 Бумага (x2)", callback_data="rps_paper")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])


# --- СЛОТ МАШИНА ---
class SlotMachine:
    def __init__(self):
        self.symbols = ["🍒", "🍊", "🍋", "🍉", "🔔", "💎", "7️⃣", "⭐"]
    
    def spin(self, bet):
        reel1 = random.choice(self.symbols)
        reel2 = random.choice(self.symbols)
        reel3 = random.choice(self.symbols)
        
        if reel1 == reel2 == reel3:
            if reel1 == "7️⃣":
                mult = 10
            elif reel1 == "⭐":
                mult = 8
            elif reel1 == "💎":
                mult = 6
            else:
                mult = 4
            win = True
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            mult = 2
            win = True
        else:
            mult = 0
            win = False
        
        return {"reels": [reel1, reel2, reel3], "win": win, "mult": mult, "win_amount": int(bet * mult) if win else 0}


slot_machine = SlotMachine()


# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    text = f"""🎮 <b>ДАВАЙ НАЧНЕМ ИГРАТЬ!</b> 🎮

💰 <b>Баланс:</b> {user['balance']} m¢
💸 <b>Ставка:</b> {user['bet']} m¢

👇 <i>Выбери игру и начинай!</i>"""
    await message.answer(text, reply_markup=main_kb())


@dp.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    await call.answer(f"💰 Баланс: {user['balance']} m¢", show_alert=True)


@dp.callback_query(F.data == "show_stats")
async def show_stats(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    win_rate = (user["total_wins"] / user["total_games"] * 100) if user["total_games"] > 0 else 0
    text = f"""📊 <b>ТВОЯ СТАТИСТИКА</b> 📊
{DOTS}
🎮 Всего игр: {user['total_games']}
✅ Побед: {user['total_wins']}
❌ Поражений: {user['total_losses']}
📈 Винрейт: {win_rate:.1f}%
💰 Баланс: {user['balance']} m¢
💸 Ставка: {user['bet']} m¢"""
    await call.message.edit_text(text, reply_markup=main_kb())


@dp.callback_query(F.data == "menu_modes")
async def show_modes(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = f"""🎮 <b>РЕЖИМЫ ИГР</b> 🎮

💰 Баланс: {user['balance']} m¢
💸 Ставка: {user['bet']} m¢

👇 <i>Выбери режим:</i>"""
    await call.message.edit_text(text, reply_markup=modes_kb())


@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = f"""🎮 <b>ДАВАЙ НАЧНЕМ ИГРАТЬ!</b> 🎮

💰 <b>Баланс:</b> {user['balance']} m¢
💸 <b>Ставка:</b> {user['bet']} m¢

👇 <i>Выбери игру и начинай!</i>"""
    await call.message.edit_text(text, reply_markup=main_kb())


@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bets = [10, 25, 50, 100, 250, 500, 1000]
    current = user['bet']
    next_idx = (bets.index(current) + 1) % len(bets)
    user['bet'] = bets[next_idx]
    await call.answer(f"💸 Ставка изменена на {user['bet']} m¢", show_alert=True)
    await back_to_main(call)


@dp.callback_query(F.data == "under_dev")
async def dev(call: types.CallbackQuery):
    await call.answer("🚧 В разработке", show_alert=True)


# --- ПОДГОТОВКА ИГР ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_games(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    user = get_user(call.from_user.id)
    bet = user['bet']
    btn_back = InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")

    games = {
        "basketball": {"text": f"🏀 <b>Баскетбол</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nКуда попадёт мяч?",
                       "buttons": [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_bask_goal")],
                                   [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_bask_miss")]]},
        "football": {"text": f"⚽ <b>Футбол</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nЗабьют или нет?",
                     "buttons": [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")],
                                 [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")]]},
        "darts": {"text": f"🎯 <b>Дартс</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nКуда попадёт дротик?",
                  "buttons": [[InlineKeyboardButton(text="🔴 Красное - x1.94", callback_data="play_dart_red"),
                               InlineKeyboardButton(text="⚪ Белое - x2.9", callback_data="play_dart_white")],
                              [InlineKeyboardButton(text="🎯 Центр - x5.8", callback_data="play_dart_center"),
                               InlineKeyboardButton(text="😟 Мимо - x5.8", callback_data="play_dart_miss")]]},
        "bowling": {"text": f"🎳 <b>Боулинг</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nСколько кегель упадет?",
                    "buttons": [[InlineKeyboardButton(text="1 кегля", callback_data="play_bowl_1"),
                                 InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
                                [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"),
                                 InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
                                [InlineKeyboardButton(text="🎳 Страйк - x5.8", callback_data="play_bowl_6"),
                                 InlineKeyboardButton(text="😟 Мимо - x5.8", callback_data="play_bowl_0")]]},
        "dice": {"text": f"🎲 <b>Кубик</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nКакое число выпадет?",
                 "buttons": [[InlineKeyboardButton(text="1", callback_data="play_dice_1"),
                              InlineKeyboardButton(text="2", callback_data="play_dice_2"),
                              InlineKeyboardButton(text="3", callback_data="play_dice_3")],
                             [InlineKeyboardButton(text="4", callback_data="play_dice_4"),
                              InlineKeyboardButton(text="5", callback_data="play_dice_5"),
                              InlineKeyboardButton(text="6", callback_data="play_dice_6")],
                             [InlineKeyboardButton(text="⚖️ Чётный - x1.94", callback_data="play_dice_even"),
                              InlineKeyboardButton(text="🔰 Нечётный - x1.94", callback_data="play_dice_odd")],
                             [InlineKeyboardButton(text="＝ Равно 3 - x5.8", callback_data="play_dice_equal3")],
                             [InlineKeyboardButton(text="➕ Больше 3 - x1.94", callback_data="play_dice_high"),
                              InlineKeyboardButton(text="➖ Меньше 3 - x2.9", callback_data="play_dice_low")]]},
        "slots": {"text": f"🎰 <b>Слоты</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nНажми на кнопку и крути барабаны!",
                  "buttons": [[InlineKeyboardButton(text="🎰 КРУТИТЬ", callback_data="play_slots")]]},
        "wheel": {"text": f"🎡 <b>Рулетка</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nВыбери цвет и удвой ставку!",
                  "buttons": []},
        "rps": {"text": f"🪨✂️📄 <b>Камень-ножницы-бумага</b>\n{DOTS}\n💸 Ставка: {bet} m¢\n\nСыграй с ботом!",
                "buttons": []}
    }

    if game in games:
        if game == "slots":
            await call.message.edit_text(games[game]["text"], reply_markup=slots_kb())
        elif game == "wheel":
            await call.message.edit_text(games[game]["text"], reply_markup=wheel_kb())
        elif game == "rps":
            await call.message.edit_text(games[game]["text"], reply_markup=rps_kb())
        else:
            kb = games[game]["buttons"] + [[btn_back]]
            await call.message.edit_text(games[game]["text"], reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        await call.answer("🚧 В разработке")


# --- ИГРА СЛОТЫ ---
@dp.callback_query(F.data == "play_slots")
async def slots_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bet = user['bet']

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet)

    result = slot_machine.spin(bet)

    if result["win"]:
        update_balance(call.from_user.id, result["win_amount"])
        text = f"""🎰 <b>СЛОТЫ</b> 🎰
{DOTS}
┌─────────────┐
│  {result['reels'][0]}   {result['reels'][1]}   {result['reels'][2]}  │
└─────────────┘
{DOTS}
✅ ПОБЕДА! x{result['mult']} = +{result['win_amount']} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        text = f"""🎰 <b>СЛОТЫ</b> 🎰
{DOTS}
┌─────────────┐
│  {result['reels'][0]}   {result['reels'][1]}   {result['reels'][2]}  │
└─────────────┘
{DOTS}
❌ ПРОИГРЫШ! -{bet} m¢
💰 Баланс: {user['balance']} m¢"""

    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()


# --- РУЛЕТКА ---
@dp.callback_query(F.data.startswith("wheel_"))
async def wheel_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    color = call.data.split("_")[1]
    bet = user["bet"]

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet)

    await call.message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)

    colors = ["🔴", "⚫", "🟢"]
    results = ["Красное", "Чёрное", "Зелёное"]
    result_idx = random.randint(0, 12)

    if result_idx == 0:
        result = 2
    elif result_idx <= 6:
        result = 0
    else:
        result = 1

    win = False
    multiplier = 0

    if color == "red" and result == 0:
        win, multiplier = True, 2
    elif color == "black" and result == 1:
        win, multiplier = True, 2
    elif color == "green" and result == 2:
        win, multiplier = True, 14

    if win:
        win_amount = int(bet * multiplier)
        update_balance(call.from_user.id, win_amount)
        text = f"""🎡 <b>РУЛЕТКА</b> 🎡
{DOTS}
🎯 Выпало: {colors[result]} {results[result]}
✅ ПОБЕДА! x{multiplier} = +{win_amount} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        text = f"""🎡 <b>РУЛЕТКА</b> 🎡
{DOTS}
🎯 Выпало: {colors[result]} {results[result]}
❌ ПРОИГРЫШ! -{bet} m¢
💰 Баланс: {user['balance']} m¢"""

    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()


# --- КАМЕНЬ-НОЖНИЦЫ-БУМАГА ---
@dp.callback_query(F.data.startswith("rps_"))
async def rps_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    player_choice = call.data.split("_")[1]
    bet = user["bet"]

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet)

    choices = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📄 Бумага"}
    bot_choice = random.choice(["rock", "scissors", "paper"])

    if player_choice == bot_choice:
        update_balance(call.from_user.id, bet)
        text = f"""🪨✂️📄 <b>КНБ</b>
{DOTS}
👉 Ты: {choices[player_choice]}
👈 Бот: {choices[bot_choice]}
{DOTS}
🤝 НИЧЬЯ! Ставка возвращена
💰 Баланс: {user['balance']} m¢"""
    elif (player_choice == "rock" and bot_choice == "scissors") or \
         (player_choice == "scissors" and bot_choice == "paper") or \
         (player_choice == "paper" and bot_choice == "rock"):
        win_amount = int(bet * 2)
        update_balance(call.from_user.id, win_amount)
        text = f"""🪨✂️📄 <b>КНБ</b>
{DOTS}
👉 Ты: {choices[player_choice]}
👈 Бот: {choices[bot_choice]}
{DOTS}
✅ ПОБЕДА! +{win_amount} m¢
💰 Баланс: {user['balance']} m¢"""
    else:
        text = f"""🪨✂️📄 <b>КНБ</b>
{DOTS}
👉 Ты: {choices[player_choice]}
👈 Бот: {choices[bot_choice]}
{DOTS}
❌ ПРОИГРЫШ! -{bet} m¢
💰 Баланс: {user['balance']} m¢"""

    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()


# --- ОСТАЛЬНЫЕ ИГРЫ С КУБИКОМ ---
@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    user = get_user(call.from_user.id)

    if user["balance"] < user["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    data = call.data.split("_")
    game_code = data[1]
    selection = data[2] if len(data) > 2 else "spin"

    bet = user["bet"]
    update_balance(call.from_user.id, -bet)

    emojis = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲"}
    dice_msg = await call.message.answer_dice(emoji=emojis.get(game_code, "🎲"))
    await asyncio.sleep(3)
    val = dice_msg.dice.value

    win = False
    multiplier = 0

    if game_code == "bask":
        if selection == "goal":
            win = val >= 5
            multiplier = 2.4 if win else 0
        else:
            win = val <= 2
            multiplier = 1.6 if win else 0
    elif game_code == "foot":
        if selection == "goal":
            win = val >= 5
            multiplier = 1.6 if win else 0
        else:
            win = val <= 2
            multiplier = 2.4 if win else 0
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
    elif game_code == "bowl":
        if selection == "6":
            win = val == 6
            multiplier = 5.8 if win else 0
        elif selection == "0":
            win = val == 1
            multiplier = 5.8 if win else 0
        else:
            win = 1 <= val <= 5
            multiplier = 5.8 if win else 0
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

    if win:
        win_amount = int(bet * multiplier)
        update_balance(call.from_user.id, win_amount)
        header = "🥳 ПОБЕДА! ✅"
        outcome_text = f"💰 Выигрыш: x{multiplier} = +{win_amount} m¢"
    else:
        header = "😭 ПРОИГРЫШ ❌"
        outcome_text = f"💸 Потеряно: -{bet} m¢"

    res_text = f"""{header}
{DOTS}
💸 Ставка: {bet} m¢
🎲 Выбрано: {selection}
🎯 Выпало: {val}
{DOTS}
{outcome_text}
💰 Баланс: {user['balance']} m¢"""

    await call.message.answer(res_text, reply_markup=main_kb())
    await call.message.delete()


# --- МИНЫ ---
def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Удвоить ставку", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_modes")]
    ])


@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = f"💣 <b>МИНЫ</b>\n{DOTS}\n💸 Ставка: {user['bet']} m¢\n\nВыбери количество мин:"
    await call.message.edit_text(text, reply_markup=mines_start_kb())


@dp.callback_query(F.data == "mines_double")
async def mines_double(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    user['bet'] *= 2
    await call.answer(f"💸 Ставка удвоена! Теперь: {user['bet']} m¢", show_alert=True)
    await mines_menu(call)


@dp.callback_query(F.data.startswith("setmines_"))
async def start_mines_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    m_count = int(call.data.split("_")[1])
    user_id = call.from_user.id

    if user["balance"] < user["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(user_id, -user["bet"])

    board = [0] * 25
    for idx in random.sample(range(25), m_count):
        board[idx] = 1

    game_sessions[user_id] = {
        'board': board,
        'bet': user['bet'],
        'mines': m_count,
        'opened': [],
        'game_over': False
    }

    await call.message.edit_text(f"💎 <b>МИНЫ</b>\n{DOTS}\n💣 Мин: {m_count}\n💸 Ставка: {user['bet']} m¢\n\nОткрывай ячейки!",
                                 reply_markup=get_mines_board_kb(user_id))


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
        multiplier = 1 + (opened_safe / total_safe) * 2 if opened_safe > 0 else 1
        kb.append([InlineKeyboardButton(text=f"💰 Забрать x{multiplier:.2f}", callback_data="m_cashout")])
        kb.append([InlineKeyboardButton(text="◀️ Выход", callback_data="to_main")])
    else:
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {s['bet']} m¢", callback_data=f"setmines_{s['mines']}")])
        kb.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_modes")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


@dp.callback_query(F.data.startswith("mopen_"))
async def mines_step(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    idx = int(call.data.split("_")[1])
    s = game_sessions.get(call.from_user.id)

    if not s or s['game_over'] or idx in s['opened']:
        return

    s['opened'].append(idx)

    if s['board'][idx] == 1:
        s['game_over'] = True
        text = f"💥 <b>МИНЫ · ПРОИГРЫШ!</b>\n{DOTS}\n💣 Мин: {s['mines']}\n💸 Ставка: {s['bet']} m¢\n💰 Баланс: {user['balance']} m¢"
    else:
        opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
        total_safe = 25 - s['mines']
        multiplier = 1 + (opened_safe / total_safe) * 2
        text = f"💎 <b>МИНЫ · ИГРА ИДЁТ</b>\n{DOTS}\n💣 Мин: {s['mines']}\n💸 Ставка: {s['bet']} m¢\n💰 Множитель: x{multiplier:.2f}"

    await call.message.edit_text(text, reply_markup=get_mines_board_kb(call.from_user.id))


@dp.callback_query(F.data == "m_cashout")
async def mines_cashout(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    user_id = call.from_user.id
    s = game_sessions.get(user_id)

    if not s or s['game_over']:
        return

    opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
    total_safe = 25 - s['mines']
    multiplier = 1 + (opened_safe / total_safe) * 2 if opened_safe > 0 else 1
    win_amount = int(s['bet'] * multiplier)
    update_balance(user_id, win_amount)

    text = f"""💰 <b>ТЫ ЗАБРАЛ ВЫИГРЫШ!</b>
{DOTS}
💸 Ставка: {s['bet']} m¢
🎲 Множитель: x{multiplier:.2f}
✅ Выигрыш: +{win_amount} m¢
💰 Новый баланс: {user['balance']} m¢"""

    await call.message.edit_text(text, reply_markup=main_kb())
    del game_sessions[user_id]


# --- ВЕБАПП СИНХРОНИЗАЦИЯ ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    user = get_user(message.from_user.id)
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        if action == 'get_balance':
            await message.answer(json.dumps({
                'action': 'set_balance',
                'balance': user['balance']
            }))
        elif action == 'game_result':
            win_amount = data.get('win_amount', 0)
            bet = data.get('bet', 100)
            old_balance = user['balance']
            user['balance'] = user['balance'] - bet + win_amount
            user['total_games'] += 1
            if win_amount > bet:
                user['total_wins'] += 1
            else:
                user['total_losses'] += 1
    except:
        pass


# --- ЗАПУСК ---
async def main():
    print("🤖 ИГРОВОЙ БОТ ЗАПУЩЕН!")
    print("🎮 Доступны игры: Баскетбол, Футбол, Дартс, Боулинг, Кубик, Слоты, Мины, Рулетка, КНБ")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
