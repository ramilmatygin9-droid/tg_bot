import asyncio
import random
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk"

bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# БАЗА ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ
users_db = {}
game_sessions = {}
DOTS = "· · · · · · · · · · · · · · · · ·"


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ---
def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 1000,
            "bet": 100,
            "mines_count": 3,
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0
        }
    return users_db[user_id]


def update_balance(user_id, amount, game_result="unknown"):
    user = get_user(user_id)
    old_balance = user["balance"]
    user["balance"] += amount
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
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽ Футбол", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯 Дартс", callback_data="prep_darts")
        ],
        [
            InlineKeyboardButton(text="🎳 Боулинг", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲 Кубик", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰 Слоты", callback_data="prep_slots")
        ],
        [
            InlineKeyboardButton(text="🎡 Рулетка", callback_data="prep_wheel"),
            InlineKeyboardButton(text="🪨✂️📄 КНБ", callback_data="prep_rps"),
            InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines")
        ],
        [
            InlineKeyboardButton(text="🎮 Режимы", callback_data="menu_modes"),
            InlineKeyboardButton(text="🎰 КЕЙСЫ", web_app=WebAppInfo(url="https://ramilmatygin9-droid.github.io/GLITCH-WIN/"))
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
            InlineKeyboardButton(text="📝 Ставка", callback_data="change_bet")
        ]
    ])


def modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Алмазы", callback_data="under_dev"), InlineKeyboardButton(text="🧱 Башня", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="⬆️⬇️ HiLo", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21 Очко", callback_data="under_dev"), InlineKeyboardButton(text="🏜 Пирамида", callback_data="under_dev")],
        [InlineKeyboardButton(text="🥊 Арена", callback_data="under_dev"), InlineKeyboardButton(text="⚡ Быстрые", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])


# --- УМНАЯ ЛОГИКА СЛОТОВ ---
class SlotMachine:
    def __init__(self):
        self.symbols = [
            {"emoji": "🍒", "name": "Вишня", "multiplier": 2, "weight": 25},
            {"emoji": "🍊", "name": "Апельсин", "multiplier": 3, "weight": 20},
            {"emoji": "🍋", "name": "Лимон", "multiplier": 4, "weight": 18},
            {"emoji": "🍉", "name": "Арбуз", "multiplier": 5, "weight": 15},
            {"emoji": "🔔", "name": "Колокол", "multiplier": 8, "weight": 10},
            {"emoji": "💎", "name": "Алмаз", "multiplier": 15, "weight": 7},
            {"emoji": "7️⃣", "name": "Семерка", "multiplier": 25, "weight": 4},
            {"emoji": "⭐", "name": "Звезда", "multiplier": 50, "weight": 1}
        ]
        self.special_combos = [
            {"name": "💥 ДЖЕКПОТ", "condition": ["7️⃣", "7️⃣", "7️⃣"], "multiplier": 100},
            {"name": "💠 СУПЕР", "condition": ["💎", "💎", "💎"], "multiplier": 50},
            {"name": "🌟 МЕГА", "condition": ["⭐", "⭐", "⭐"], "multiplier": 75}
        ]

    def get_random_symbol(self):
        total_weight = sum(s["weight"] for s in self.symbols)
        rand = random.randint(1, total_weight)
        cumulative = 0
        for symbol in self.symbols:
            cumulative += symbol["weight"]
            if rand <= cumulative:
                return symbol.copy()
        return self.symbols[0].copy()

    def check_win(self, reel1, reel2, reel3, bet):
        combo_symbols = [reel1["emoji"], reel2["emoji"], reel3["emoji"]]

        for combo in self.special_combos:
            if combo_symbols == combo["condition"]:
                win_amount = int(bet * combo["multiplier"])
                return {"win": True, "multiplier": combo["multiplier"], "win_amount": win_amount, "combo_name": combo["name"]}

        if reel1["emoji"] == reel2["emoji"] == reel3["emoji"]:
            multiplier = reel1["multiplier"]
            win_amount = int(bet * multiplier)
            return {"win": True, "multiplier": multiplier, "win_amount": win_amount, "combo_name": f"ТРИ {reel1['name']}"}

        if reel1["emoji"] == reel2["emoji"] or reel2["emoji"] == reel3["emoji"] or reel1["emoji"] == reel3["emoji"]:
            if reel1["emoji"] == reel2["emoji"]:
                multiplier = reel1["multiplier"] * 0.5
                win_amount = int(bet * multiplier)
                return {"win": True, "multiplier": multiplier, "win_amount": win_amount, "combo_name": f"ПАРА {reel1['name']}"}
            elif reel2["emoji"] == reel3["emoji"]:
                multiplier = reel2["multiplier"] * 0.5
                win_amount = int(bet * multiplier)
                return {"win": True, "multiplier": multiplier, "win_amount": win_amount, "combo_name": f"ПАРА {reel2['name']}"}
            else:
                multiplier = reel1["multiplier"] * 0.5
                win_amount = int(bet * multiplier)
                return {"win": True, "multiplier": multiplier, "win_amount": win_amount, "combo_name": f"ПАРА {reel1['name']}"}

        return {"win": False, "multiplier": 0, "win_amount": 0}


slot_machine = SlotMachine()


# --- ОБРАБОТЧИКИ ---
@dp.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    await call.answer(f"💰 Баланс: {user['balance']} m¢", show_alert=True)


@dp.callback_query(F.data == "show_stats")
async def show_stats(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    win_rate = (user["total_wins"] / user["total_games"] * 100) if user["total_games"] > 0 else 0
    text = (f"📊 **ТВОЯ СТАТИСТИКА**\n{DOTS}\n"
            f"🎮 Всего игр: {user['total_games']}\n"
            f"✅ Побед: {user['total_wins']}\n"
            f"❌ Поражений: {user['total_losses']}\n"
            f"📈 Винрейт: {win_rate:.1f}%\n"
            f"💰 Баланс: {user['balance']} m¢\n"
            f"💸 Ставка: {user['bet']} m¢")
    await call.message.edit_text(text, reply_markup=main_kb())


@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user['balance']} m¢\n"
            f"💸 **Ставка:** {user['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=main_kb())


@dp.callback_query(F.data == "menu_modes")
async def show_modes(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = (f"🎮 **ДОПОЛНИТЕЛЬНЫЕ РЕЖИМЫ**\n{DOTS}\n"
            f"💰 Баланс: {user['balance']} m¢\n"
            f"💸 Ставка: {user['bet']} m¢\n\n"
            f"👇 *Выбирай:*")
    await call.message.edit_text(text, reply_markup=modes_kb())


@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bets = [10, 25, 50, 100, 250, 500, 1000]
    current = user['bet']
    next_idx = (bets.index(current) + 1) % len(bets)
    user['bet'] = bets[next_idx]
    await call.answer(f"💸 Ставка изменена на {user['bet']} m¢")
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

    games_config = {
        "basketball": {"text": f"🏀 *Баскетбол*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nКуда попадёт мяч?",
                       "buttons": [[InlineKeyboardButton(text="🏀 ПОПАДАНИЕ (x2.4)", callback_data="play_bask_goal")],
                                   [InlineKeyboardButton(text="🙈 МИМО (x1.6)", callback_data="play_bask_miss")]]},
        "football": {"text": f"⚽ *Футбол*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nЗабьют или нет?",
                     "buttons": [[InlineKeyboardButton(text="⚽ ГОЛ (x1.6)", callback_data="play_foot_goal")],
                                 [InlineKeyboardButton(text="🥅 МИМО (x2.4)", callback_data="play_foot_miss")]]},
        "darts": {"text": f"🎯 *Дартс*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nКуда попадёт дротик?",
                  "buttons": [[InlineKeyboardButton(text="🔴 КРАСНОЕ (x1.94)", callback_data="play_dart_red"),
                               InlineKeyboardButton(text="⚪ БЕЛОЕ (x2.9)", callback_data="play_dart_white")],
                              [InlineKeyboardButton(text="🎯 ЦЕНТР (x5.8)", callback_data="play_dart_center"),
                               InlineKeyboardButton(text="😟 МИМО (x5.8)", callback_data="play_dart_miss")]]},
        "bowling": {"text": f"🎳 *Боулинг*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nСколько кегель упадет?",
                    "buttons": [[InlineKeyboardButton(text="1 КЕГЛЯ", callback_data="play_bowl_1"),
                                 InlineKeyboardButton(text="3 КЕГЛИ", callback_data="play_bowl_3")],
                                [InlineKeyboardButton(text="4 КЕГЛИ", callback_data="play_bowl_4"),
                                 InlineKeyboardButton(text="5 КЕГЕЛЬ", callback_data="play_bowl_5")],
                                [InlineKeyboardButton(text="🎳 СТРАЙК (x5.8)", callback_data="play_bowl_6"),
                                 InlineKeyboardButton(text="😟 МИМО (x5.8)", callback_data="play_bowl_0")]]},
        "dice": {"text": f"🎲 *Кубик*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nКакое число выпадет?",
                 "buttons": [[InlineKeyboardButton(text="1", callback_data="play_dice_1"),
                              InlineKeyboardButton(text="2", callback_data="play_dice_2"),
                              InlineKeyboardButton(text="3", callback_data="play_dice_3")],
                             [InlineKeyboardButton(text="4", callback_data="play_dice_4"),
                              InlineKeyboardButton(text="5", callback_data="play_dice_5"),
                              InlineKeyboardButton(text="6", callback_data="play_dice_6")],
                             [InlineKeyboardButton(text="⚖️ ЧЁТНЫЙ (x1.94)", callback_data="play_dice_even"),
                              InlineKeyboardButton(text="🔰 НЕЧЁТНЫЙ (x1.94)", callback_data="play_dice_odd")],
                             [InlineKeyboardButton(text="🎯 РАВНО 3 (x5.8)", callback_data="play_dice_equal3")],
                             [InlineKeyboardButton(text="➕ БОЛЬШЕ 3 (x1.94)", callback_data="play_dice_high"),
                              InlineKeyboardButton(text="➖ МЕНЬШЕ 3 (x2.9)", callback_data="play_dice_low")]]},
        "slots": {"text": f"🎰 *Слоты*\n{DOTS}\n💸 Ставка: {bet} m¢\n\n🎲 Символы: 🍒🍊🍋🍉🔔💎7️⃣⭐\n🔥 Джекпот: 777 = x100!",
                  "buttons": [[InlineKeyboardButton(text="🎰 КРУТИТЬ", callback_data="play_slots_spin")]]},
        "wheel": {"text": f"🎡 *Рулетка*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nВыбери цвет и удвой ставку!",
                  "buttons": [[InlineKeyboardButton(text="🔴 КРАСНОЕ (x2)", callback_data="wheel_red")],
                              [InlineKeyboardButton(text="⚫ ЧЁРНОЕ (x2)", callback_data="wheel_black")],
                              [InlineKeyboardButton(text="🟢 ЗЕЛЁНОЕ (x14)", callback_data="wheel_green")]]},
        "rps": {"text": f"🪨✂️📄 *Камень-ножницы-бумага*\n{DOTS}\n💸 Ставка: {bet} m¢\n\nСыграй с ботом!",
                "buttons": [[InlineKeyboardButton(text="🪨 КАМЕНЬ (x2)", callback_data="rps_rock")],
                            [InlineKeyboardButton(text="✂️ НОЖНИЦЫ (x2)", callback_data="rps_scissors")],
                            [InlineKeyboardButton(text="📄 БУМАГА (x2)", callback_data="rps_paper")]]}
    }

    if game in games_config:
        config = games_config[game]
        kb = config["buttons"] + [[btn_back]]
        await call.message.edit_text(config["text"], reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        await call.answer("🚧 В разработке")


# --- ИГРЫ ---
@dp.callback_query(F.data.startswith("wheel_"))
async def wheel_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    color = call.data.split("_")[1]
    bet = user["bet"]

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet, "wheel")

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
        update_balance(call.from_user.id, win_amount, "wheel_win")
        text = (f"🎡 **РУЛЕТКА**\n{DOTS}\n"
                f"🎯 Выпало: {colors[result]} {results[result]}\n"
                f"✅ ПОБЕДА! x{multiplier} = +{win_amount} m¢\n"
                f"💰 Баланс: {user['balance']} m¢")
    else:
        text = (f"🎡 **РУЛЕТКА**\n{DOTS}\n"
                f"🎯 Выпало: {colors[result]} {results[result]}\n"
                f"❌ ПРОИГРЫШ! -{bet} m¢\n"
                f"💰 Баланс: {user['balance']} m¢")

    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()


@dp.callback_query(F.data.startswith("rps_"))
async def rps_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    player_choice = call.data.split("_")[1]
    bet = user["bet"]

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet, "rps")

    choices = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📄 Бумага"}
    bot_choice = random.choice(["rock", "scissors", "paper"])

    if player_choice == bot_choice:
        update_balance(call.from_user.id, bet, "rps_tie")
        text = (f"🪨✂️📄 **КНБ**\n{DOTS}\n"
                f"👉 Ты: {choices[player_choice]}\n"
                f"👈 Бот: {choices[bot_choice]}\n"
                f"🤝 НИЧЬЯ! Ставка возвращена\n"
                f"💰 Баланс: {user['balance']} m¢")
    elif (player_choice == "rock" and bot_choice == "scissors") or \
         (player_choice == "scissors" and bot_choice == "paper") or \
         (player_choice == "paper" and bot_choice == "rock"):
        win_amount = int(bet * 2)
        update_balance(call.from_user.id, win_amount, "rps_win")
        text = (f"🪨✂️📄 **КНБ**\n{DOTS}\n"
                f"👉 Ты: {choices[player_choice]}\n"
                f"👈 Бот: {choices[bot_choice]}\n"
                f"✅ ПОБЕДА! +{win_amount} m¢\n"
                f"💰 Баланс: {user['balance']} m¢")
    else:
        text = (f"🪨✂️📄 **КНБ**\n{DOTS}\n"
                f"👉 Ты: {choices[player_choice]}\n"
                f"👈 Бот: {choices[bot_choice]}\n"
                f"❌ ПРОИГРЫШ! -{bet} m¢\n"
                f"💰 Баланс: {user['balance']} m¢")

    await call.message.answer(text, reply_markup=main_kb())
    await call.message.delete()


@dp.callback_query(F.data.startswith("play_slots"))
async def slots_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bet = user["bet"]

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet, "slots")

    await call.message.edit_text("🎰 **КРУТИМ БАРАБАНЫ** 🎰\n" + DOTS + "\n\n🔄 *Идёт вращение...*")
    await asyncio.sleep(1)

    reel1 = slot_machine.get_random_symbol()
    reel2 = slot_machine.get_random_symbol()
    reel3 = slot_machine.get_random_symbol()

    result = slot_machine.check_win(reel1, reel2, reel3, bet)

    if result["win"]:
        update_balance(call.from_user.id, result["win_amount"], "slots_win")
        result_text = (f"┌─────────────────┐\n"
                       f"│  {reel1['emoji']}   {reel2['emoji']}   {reel3['emoji']}  │\n"
                       f"└─────────────────┘\n"
                       f"🎉 {result['combo_name']}!\n"
                       f"💎 Множитель: x{result['multiplier']}\n"
                       f"✅ Выигрыш: +{result['win_amount']} m¢")
    else:
        result_text = (f"┌─────────────────┐\n"
                       f"│  {reel1['emoji']}   {reel2['emoji']}   {reel3['emoji']}  │\n"
                       f"└─────────────────┘\n"
                       f"❌ ПРОИГРЫШ! -{bet} m¢")

    final_text = (f"🎰 **СЛОТЫ**\n{DOTS}\n"
                  f"{result_text}\n{DOTS}\n"
                  f"💰 Баланс: {user['balance']} m¢")

    await call.message.answer(final_text, reply_markup=main_kb())
    await call.message.delete()


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
    update_balance(call.from_user.id, -bet, game_code)

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
        win_cases = {"red": [1, 2], "white": [3, 4], "center": [5], "miss": [6]}
        if selection in win_cases:
            win = val in win_cases[selection]
            multiplier = {"red": 1.94, "white": 2.9, "center": 5.8, "miss": 5.8}.get(selection, 0)
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
        update_balance(call.from_user.id, win_amount, f"{game_code}_win")
        header = "🥳 ПОБЕДА! ✅"
        outcome_text = f"💰 Выигрыш: x{multiplier} = +{win_amount} m¢"
    else:
        header = "😭 ПРОИГРЫШ ❌"
        outcome_text = f"💸 Потеряно: -{bet} m¢"

    res_text = (f"{header}\n{DOTS}\n"
                f"💸 Ставка: {bet} m¢\n"
                f"🎲 Выбрано: {selection}\n"
                f"🎯 Выпало: {val}\n"
                f"{DOTS}\n"
                f"{outcome_text}\n"
                f"💰 Баланс: {user['balance']} m¢")

    await call.message.answer(res_text, reply_markup=main_kb())
    await call.message.delete()


# --- ВЕБАПП ОБРАБОТЧИК (СИНХРОНИЗАЦИЯ С САЙТОМ) ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    user = get_user(message.from_user.id)

    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        print(f"📱 WebApp от {message.from_user.id}: {action}")

        if action == 'get_web_balance':
            # Отправляем баланс на сайт
            await message.answer(json.dumps({
                'action': 'set_balance',
                'balance': user['balance']
            }))

        elif action == 'web_balance':
            # Получаем баланс с сайта
            new_balance = data.get('balance')
            if new_balance is not None and isinstance(new_balance, (int, float)):
                old_balance = user['balance']
                user['balance'] = int(new_balance)
                print(f"🔄 Синхронизация: {old_balance} → {user['balance']}")
                await message.answer(f"💰 Баланс синхронизирован: {user['balance']} m¢")

        elif action == 'game_result':
            # Результат игры с сайта
            win_amount = data.get('win_amount', 0)
            bet = data.get('bet', 100)

            old_balance = user['balance']
            user['balance'] = user['balance'] - bet + win_amount
            user['total_games'] += 1

            if win_amount > bet:
                user['total_wins'] += 1
            else:
                user['total_losses'] += 1

            text = (f"🎮 **WEB КЕЙСЫ**\n{DOTS}\n"
                    f"💰 Ставка: {bet} m¢\n"
                    f"🎁 Выигрыш: {win_amount} m¢\n"
                    f"{'✅ ПОБЕДА!' if win_amount > bet else '❌ ПРОИГРЫШ'}\n"
                    f"💰 Баланс: {user['balance']} m¢")

            await message.answer(text, reply_markup=main_kb())

        elif action == 'init_stats':
            # Отправляем статистику на сайт
            win_rate = (user["total_wins"] / user["total_games"] * 100) if user["total_games"] > 0 else 0
            await message.answer(json.dumps({
                'action': 'stats_data',
                'balance': user['balance'],
                'total_games': user['total_games'],
                'total_wins': user['total_wins'],
                'win_rate': round(win_rate, 1)
            }))

    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
    except Exception as e:
        print(f"WebApp Error: {e}")


# --- МИНЫ ---
def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Удвоить ставку", callback_data="mines_double")],
        [InlineKeyboardButton(text="1️⃣", callback_data="setmines_1"), InlineKeyboardButton(text="2️⃣", callback_data="setmines_2"), InlineKeyboardButton(text="3️⃣", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4️⃣", callback_data="setmines_4"), InlineKeyboardButton(text="5️⃣", callback_data="setmines_5"), InlineKeyboardButton(text="6️⃣", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_modes")]
    ])


@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = f"💣 **МИНЫ**\n{DOTS}\n💸 Ставка: {user['bet']} m¢\n\nВыбери количество мин:"
    await call.message.edit_text(text, reply_markup=mines_start_kb())


@dp.callback_query(F.data == "mines_double")
async def mines_double(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    user['bet'] *= 2
    await call.answer(f"💸 Ставка удвоена! Теперь: {user['bet']} m¢")
    await mines_menu(call)


@dp.callback_query(F.data.startswith("setmines_"))
async def start_mines_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    m_count = int(call.data.split("_")[1])
    user_id = call.from_user.id

    if user["balance"] < user["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(user_id, -user["bet"], "mines")

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

    await call.message.edit_text(f"💎 **МИНЫ**\n{DOTS}\n💣 Мин: {m_count}\n💸 Ставка: {user['bet']} m¢\n\nОткрывай ячейки!",
                                 reply_markup=get_mines_board_kb(user_id))


def get_mines_board_kb(user_id):
    s = game_sessions.get(user_id)
    if not s:
        return mines_start_kb()

    kb = []
    for r in range(5):
        row
