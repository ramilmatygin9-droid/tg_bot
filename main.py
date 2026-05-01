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
rocket_sessions = {}  # Для игры Ракета
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


def update_balance(user_id, amount, skip_stats=False):
    user = get_user(user_id)
    old_balance = user["balance"]
    user["balance"] += amount
    if not skip_stats and amount != 0:
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
            InlineKeyboardButton(text="🚀 РАКЕТА", callback_data="prep_rocket"),
            InlineKeyboardButton(text="🎡 РУЛЕТКА", callback_data="prep_wheel"),
            InlineKeyboardButton(text="🪨✂️📄", callback_data="prep_rps")
        ],
        [
            InlineKeyboardButton(text="💣 МИНЫ", callback_data="menu_mines"),
            InlineKeyboardButton(text="🎮 Режимы", callback_data="menu_modes")
        ],
        [
            InlineKeyboardButton(text="🕹 WEB", web_app=WebAppInfo(url="https://ramilmatygin9-droid.github.io/GLITCH-WIN/"))
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance"),
            InlineKeyboardButton(text="📝 Ставка", callback_data="change_bet"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")
        ]
    ])


def rocket_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ЗАБРАТЬ 💰", callback_data="rocket_cashout")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])


def rocket_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ЗАПУСТИТЬ РАКЕТУ", callback_data="rocket_start")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
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


# --- ИГРА РАКЕТА (CRASH GAME) ---
def generate_multiplier():
    """Генерирует случайный множитель от 1.01 до 10.00"""
    # Шанс взрыва на малых множителях меньше
    rand = random.random()
    if rand < 0.3:  # 30% - взрыв до x2
        return round(random.uniform(1.01, 2.00), 2)
    elif rand < 0.55:  # 25% - взрыв до x3
        return round(random.uniform(2.01, 3.00), 2)
    elif rand < 0.75:  # 20% - взрыв до x5
        return round(random.uniform(3.01, 5.00), 2)
    elif rand < 0.9:  # 15% - взрыв до x8
        return round(random.uniform(5.01, 8.00), 2)
    else:  # 10% - взрыв до x10
        return round(random.uniform(8.01, 10.00), 2)


def get_rocket_animation(multiplier):
    """Анимация ракеты в зависимости от множителя"""
    if multiplier < 1.5:
        rocket = "🚀"
        trail = "💨"
    elif multiplier < 2.5:
        rocket = "🚀➡️"
        trail = "💨💨"
    elif multiplier < 4:
        rocket = "🚀🚀"
        trail = "💨💨💨"
    elif multiplier < 6:
        rocket = "⚡🚀⚡"
        trail = "🔥🔥🔥"
    elif multiplier < 8:
        rocket = "💥🚀⚡"
        trail = "💥💥💥"
    else:
        rocket = "💢🚀💢"
        trail = "💢💢💢"
    
    bar_length = min(int(multiplier * 5), 50)
    bar = "▓" * bar_length + "░" * (50 - bar_length)
    
    return f"""
{rocket} {trail}
[{bar}] x{multiplier:.2f}
"""


@dp.callback_query(F.data == "prep_rocket")
async def prepare_rocket(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = f"""🚀 <b>ИГРА РАКЕТА (CRASH)</b> 🚀
{DOTS}

🎲 <b>ПРАВИЛА:</b>
1️⃣ Сделай ставку и запусти ракету
2️⃣ Множитель будет расти от x1.00 до x10.00
3️⃣ Забери деньги ДО того, как ракета улетит!
4️⃣ Чем выше множитель - тем больше выигрыш!

💸 <b>Твоя ставка:</b> {user['bet']} m¢
💰 <b>Баланс:</b> {user['balance']} m¢

👇 <i>Нажми на кнопку, чтобы начать!</i>"""
    
    await call.message.edit_text(text, reply_markup=rocket_start_kb())


@dp.callback_query(F.data == "rocket_start")
async def rocket_start(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bet = user['bet']
    
    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    # Списываем ставку
    update_balance(call.from_user.id, -bet, skip_stats=True)
    
    # Создаем сессию игры
    rocket_sessions[call.from_user.id] = {
        'bet': bet,
        'active': True,
        'crashed': False,
        'cashed_out': False,
        'multiplier': 1.00,
        'message_id': None,
        'chat_id': call.message.chat.id
    }
    
    # Генерируем множитель краша
    crash_multiplier = generate_multiplier()
    rocket_sessions[call.from_user.id]['crash_multiplier'] = crash_multiplier
    
    text = f"""🚀 <b>РАКЕТА ЗАПУЩЕНА!</b> 🚀
{DOTS}
💰 Ставка: {bet} m¢
📈 Текущий множитель: <b>x1.00</b>
💎 Потенциальный выигрыш: {bet} m¢

{get_rocket_animation(1.00)}

⏳ Множитель растёт...
👇 Забери деньги до того, как ракета улетит!"""
    
    msg = await call.message.edit_text(text, reply_markup=rocket_kb())
    rocket_sessions[call.from_user.id]['message_id'] = msg.message_id
    
    # Запускаем анимацию роста множителя
    asyncio.create_task(rocket_animation(call.from_user.id, msg.chat.id, msg.message_id, crash_multiplier))


async def rocket_animation(user_id, chat_id, message_id, crash_multiplier):
    """Анимация роста множителя"""
    session = rocket_sessions.get(user_id)
    if not session:
        return
    
    multiplier = 1.00
    step = 0.03  # Шаг увеличения
    
    while multiplier < crash_multiplier and session.get('active', False) and not session.get('cashed_out', False):
        multiplier = round(multiplier + step, 2)
        session['multiplier'] = multiplier
        
        win_amount = int(session['bet'] * multiplier)
        
        text = f"""🚀 <b>РАКЕТА ЛЕТИТ!</b> 🚀
{DOTS}
💰 Ставка: {session['bet']} m¢
📈 Текущий множитель: <b>x{multiplier:.2f}</b>
💎 Потенциальный выигрыш: <b>{win_amount} m¢</b>

{get_rocket_animation(multiplier)}

⚠️ Забери деньги, пока не поздно!"""
        
        try:
            await bot.edit_message_text(text, chat_id, message_id, reply_markup=rocket_kb())
        except:
            pass
        
        await asyncio.sleep(0.3)
    
    # Ракета взорвалась / улетела
    if not session.get('cashed_out', False) and session.get('active', False):
        session['active'] = False
        session['crashed'] = True
        
        text = f"""💥 <b>РАКЕТА ВЗОРВАЛАСЬ / УЛЕТЕЛА!</b> 💥
{DOTS}
💰 Ставка: {session['bet']} m¢
💥 Множитель в момент взрыва: <b>x{crash_multiplier:.2f}</b>
{DOTS}
❌ <b>ВЫ ПРОИГРАЛИ!</b> -{session['bet']} m¢
💰 Баланс: {get_user(user_id)['balance']} m¢

🚀 <i>Попробуй снова - в следующий раз повезёт!</i>"""
        
        try:
            await bot.edit_message_text(text, chat_id, message_id, reply_markup=main_kb())
        except:
            pass
        
        # Обновляем статистику
        user = get_user(user_id)
        user['total_games'] += 1
        user['total_losses'] += 1
        
        # Удаляем сессию
        del rocket_sessions[user_id]


@dp.callback_query(F.data == "rocket_cashout")
async def rocket_cashout(call: types.CallbackQuery):
    session = rocket_sessions.get(call.from_user.id)
    
    if not session or not session.get('active', False) or session.get('cashed_out', False):
        await call.answer("Игра не активна!", show_alert=True)
        return
    
    # Забираем выигрыш
    session['cashed_out'] = True
    session['active'] = False
    
    multiplier = session['multiplier']
    bet = session['bet']
    win_amount = int(bet * multiplier)
    
    # Начисляем выигрыш
    update_balance(call.from_user.id, win_amount)
    
    user = get_user(call.from_user.id)
    
    text = f"""🎉 <b>ВЫ ЗАБРАЛИ ВЫИГРЫШ!</b> 🎉
{DOTS}
🚀 Ставка: {bet} m¢
📈 Множитель: <b>x{multiplier:.2f}</b>
💰 Выигрыш: <b>+{win_amount} m¢</b>
{DOTS}
💎 Новый баланс: <b>{user['balance']} m¢</b>

✅ <i>Отличный забег! Сыграй ещё!</i>"""
    
    await call.message.edit_text(text, reply_markup=main_kb())
    
    # Обновляем статистику
    user['total_games'] += 1
    user['total_wins'] += 1
    
    # Удаляем сессию
    del rocket_sessions[call.from_user.id]


# --- ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    text = f"""🎮 <b>ДОБРО ПОЖАЛОВАТЬ В GLITCH WIN!</b> 🎮

💰 <b>Баланс:</b> {user['balance']} m¢
💸 <b>Ставка:</b> {user['bet']} m¢

🚀 <b>НОВАЯ ИГРА - РАКЕТА!</b>
Играй как в казино: запусти ракету и забери деньги до взрыва!

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
    text = f"""🎮 <b>ДОБРО ПОЖАЛОВАТЬ В GLITCH WIN!</b> 🎮

💰 <b>Баланс:</b> {user['balance']} m¢
💸 <b>Ставка:</b> {user['bet']} m¢

🚀 <b>НОВАЯ ИГРА - РАКЕТА!</b>

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


# --- ПОДГОТОВКА ДРУГИХ ИГР ---
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
                  "buttons": []},
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


# --- СЛОТЫ ---
@dp.callback_query(F.data == "play_slots")
async def slots_game(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    bet = user['bet']

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return

    update_balance(call.from_user.id, -bet, skip_stats=True)
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

    update_balance(call.from_user.id, -bet, skip_stats=True)

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

    update_balance(call.from_user.id, -bet, skip_stats=True)

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
    update_balance(call.from_user.id, -bet, skip_stats=True)

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
            multiplier = 5.
