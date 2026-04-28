import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
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
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽ Футбол", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯 Дартс", callback_data="prep_darts"),
            InlineKeyboardButton(text="🎳 Боулинг", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲 Кубик", callback_data="prep_dice"),
        ],
        [
            InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"),
        ],
        [
            InlineKeyboardButton(text="📝 Изменить ставку", callback_data="change_bet")
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance")
        ]
    ])

def modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- ЛОГИКА ИГР ---

@dp.callback_query(F.data == "menu_modes")
async def show_modes(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=modes_kb())

@dp.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    await call.answer(f"💰 Баланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_games(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    bet = user_data['bet']
    
    if game == "basketball":
        text = f"🏀 *Баскетбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_basketball_goal")],
            [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_basketball_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ])
    elif game == "football":
        text = f"⚽ *Футбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_football_goal")],
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_football_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ])
    elif game == "darts":
        text = f"🎯 *Дартс · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное - x1.94", callback_data="play_darts_red")],
            [InlineKeyboardButton(text="⚪ Белое - x2.9", callback_data="play_darts_white")],
            [InlineKeyboardButton(text="🎯 Центр - x5.8", callback_data="play_darts_center")],
            [InlineKeyboardButton(text="😟 Мимо - x5.8", callback_data="play_darts_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ])
    elif game == "bowling":
        text = f"🎳 *Боулинг · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1-5 кегли - x5.8", callback_data="play_bowling_low")],
            [InlineKeyboardButton(text="🎳 Страйк - x5.8", callback_data="play_bowling_strike")],
            [InlineKeyboardButton(text="😟 Мимо - x5.8", callback_data="play_bowling_miss")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ])
    elif game == "dice":
        text = f"🎲 *Кубик · выбери число!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data="play_dice_1"), 
             InlineKeyboardButton(text="2", callback_data="play_dice_2"), 
             InlineKeyboardButton(text="3", callback_data="play_dice_3")],
            [InlineKeyboardButton(text="4", callback_data="play_dice_4"), 
             InlineKeyboardButton(text="5", callback_data="play_dice_5"), 
             InlineKeyboardButton(text="6", callback_data="play_dice_6")],
            [InlineKeyboardButton(text="🎲 Четное x1.94", callback_data="play_dice_even")],
            [InlineKeyboardButton(text="🎲 Нечетное x1.94", callback_data="play_dice_odd")],
            [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
        ])
    else:
        return
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    # Проверяем баланс
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    parts = call.data.split("_")
    game = parts[1]
    selection = parts[2]
    
    # Списываем ставку
    bet = user_data["bet"]
    user_data["balance"] -= bet
    
    # Отправляем анимацию кубика/дартса и т.д.
    emojis = {
        "basketball": "🏀", "football": "⚽", 
        "darts": "🎯", "bowling": "🎳", "dice": "🎲"
    }
    
    msg = await call.message.answer_dice(emoji=emojis.get(game, "🎲"))
    await asyncio.sleep(3)
    dice_value = msg.dice.value
    
    # Логика выигрыша для каждой игры
    win = False
    multiplier = 0
    
    if game == "basketball":
        # Баскетбол: значение 5-6 = попадание
        if selection == "goal":
            win = dice_value >= 5
            multiplier = 2.4 if win else 0
        else:  # miss
            win = dice_value <= 2
            multiplier = 1.6 if win else 0
            
    elif game == "football":
        # Футбол: значение 5-6 = гол
        if selection == "goal":
            win = dice_value >= 5
            multiplier = 1.6 if win else 0
        else:  # miss
            win = dice_value <= 2
            multiplier = 2.4 if win else 0
            
    elif game == "darts":
        # Дартс: 1-2=красное, 3-4=белое, 5=центр, 6=мимо
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
        # Боулинг: значение кубика
        if selection == "strike":
            win = dice_value == 6
            multiplier = 5.8 if win else 0
        elif selection == "low":
            win = 1 <= dice_value <= 5
            multiplier = 5.8 if win else 0
        elif selection == "miss":
            win = dice_value == 1
            multiplier = 5.8 if win else 0
            
    elif game == "dice":
        # Кубик
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
    win_amount = 0
    if win:
        win_amount = int(bet * multiplier)
        user_data["balance"] += win_amount
        result_emoji = "✅ ПОБЕДА!"
        result_text = f"🥳 {result_emoji}\n💰 Выигрыш: x{multiplier} = {win_amount} m¢"
    else:
        result_text = f"❌ ПРОИГРЫШ!\n💸 Потеряно: {bet} m¢"
    
    # Показываем результат
    result = (f"🎲 *Выпало:* {dice_value}\n"
              f"📊 *Выбор:* {selection}\n"
              f"{DOTS}\n"
              f"{result_text}\n"
              f"{DOTS}\n"
              f"💰 *Новый баланс:* {user_data['balance']} m¢")
    
    await call.message.answer(result, reply_markup=main_kb())
    await call.message.delete()

# --- МИНЫ ---

def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 мина", callback_data="setmines_1"),
         InlineKeyboardButton(text="2 мины", callback_data="setmines_2"),
         InlineKeyboardButton(text="3 мины", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4 мины", callback_data="setmines_4"),
         InlineKeyboardButton(text="5 мин", callback_data="setmines_5"),
         InlineKeyboardButton(text="6 мин", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    text = f"💣 *Мины · выбери количество мин!*\n{DOTS}\n💸 *Ставка: {user_data['bet']} m¢*\n💰 *Баланс: {user_data['balance']} m¢*"
    await call.message.edit_text(text, reply_markup=mines_start_kb())

@dp.callback_query(F.data.startswith("setmines_"))
async def start_mines_game(call: types.CallbackQuery):
    m_count = int(call.data.split("_")[1])
    user_id = call.from_user.id
    
    # Проверка баланса
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
    
    # Списываем ставку
    user_data["balance"] -= user_data["bet"]
    
    # Создаем поле с минами
    board = [0] * 25  # 5x5 поле
    mine_positions = random.sample(range(25), m_count)
    for idx in mine_positions:
        board[idx] = 1  # 1 = мина
    
    game_sessions[user_id] = {
        'board': board,
        'bet': user_data['bet'],
        'mines': m_count,
        'opened': [],
        'game_over': False,
        'multiplier': 1.0
    }
    
    await call.message.edit_text(
        f"💣 *Мины · игра началась!*\n"
        f"{DOTS}\n"
        f"💣 *Мин:* {m_count}\n"
        f"💸 *Ставка:* {user_data['bet']} m¢\n\n"
        f"🔓 *Открывай клетки и не наступи на мину!*",
        reply_markup=get_mines_board_kb(user_id)
    )

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
                if s['board'][idx] == 1:
                    char = "💣"
                else:
                    char = "💎"
            else:
                char = "❓"
            row.append(InlineKeyboardButton(text=char, callback_data=f"mopen_{idx}"))
        kb.append(row)
    
    if not s['game_over']:
        # Расчет множителя
        opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
        total_safe = 25 - s['mines']
        if opened_safe > 0:
            multiplier = 1 + (opened_safe / total_safe) * 3
            s['multiplier'] = min(multiplier, 10)
        
        kb.append([InlineKeyboardButton(text=f"💰 Забрать x{s['multiplier']:.2f}", callback_data="m_cashout")])
        kb.append([InlineKeyboardButton(text="◀️ Выход", callback_data="to_main")])
    else:
        kb.append([InlineKeyboardButton(text="🔄 Играть снова", callback_data=f"setmines_{s['mines']}")])
        kb.append([InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.callback_query(F.data.startswith("mopen_"))
async def mines_step(call: types.CallbackQuery):
    user_id = call.from_user.id
    s = game_sessions.get(user_id)
    
    if not s or s['game_over']:
        return
    
    idx = int(call.data.split("_")[1])
    
    if idx in s['opened']:
        await call.answer("Ты уже открыл эту клетку!")
        return
    
    s['opened'].append(idx)
    
    # Проверяем, попали ли на мину
    if s['board'][idx] == 1:
        s['game_over'] = True
        text = (f"💥 *ВЗРЫВ! Ты наступил на мину!*\n"
                f"{DOTS}\n"
                f"💣 *Мин:* {s['mines']}\n"
                f"💸 *Ставка:* {s['bet']} m¢\n"
                f"💀 *Проигрыш:* {s['bet']} m¢\n"
                f"💰 *Баланс:* {user_data['balance']} m¢")
    else:
        opened_safe = len([x for x in s['opened'] if s['board'][x] == 0])
        total_safe = 25 - s['mines']
        multiplier = 1 + (opened_safe / total_safe) * 3
        multiplier = min(multiplier, 10)
        
        text = (f"💎 *Клетка открыта!*\n"
                f"{DOTS}\n"
                f"🔓 *Открыто:* {opened_safe}/{total_safe}\n"
                f"💰 *Множитель:* x{multiplier:.2f}\n"
                f"💸 *Ставка:* {s['bet']} m¢\n"
                f"💣 *Мин осталось:* {s['mines']}")
    
    await call.message.edit_text(text, reply_markup=get_mines_board_kb(user_id))

@dp.callback_query(F.data == "m_cashout")
async def mines_cashout(call: types.CallbackQuery):
    user_id = call.from_user.id
    s = game_sessions.get(user_id)
    
    if not s or s['game_over']:
        await call.answer("Игра уже закончена!")
        return
    
    win_amount = int(s['bet'] * s['multiplier'])
    user_data["balance"] += win_amount
    
    text = (f"💰 *Ты забрал выигрыш!*\n"
            f"{DOTS}\n"
            f"💸 *Ставка:* {s['bet']} m¢\n"
            f"🎲 *Множитель:* x{s['multiplier']:.2f}\n"
            f"✅ *Выигрыш:* {win_amount} m¢\n"
            f"💰 *Новый баланс:* {user_data['balance']} m¢")
    
    await call.message.edit_text(text, reply_markup=main_kb())
    
    # Очищаем сессию
    if user_id in game_sessions:
        del game_sessions[user_id]

# --- ОБЩЕЕ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (f"🎮 *ДОБРО ПОЖАЛОВАТЬ В КАЗИНО!*\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*\n\n"
            f"🎁 Каждый новый игрок получает 1000 m¢")
    await message.answer(text, reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = (f"🎮 *ГЛАВНОЕ МЕНЮ*\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢")
    await call.message.edit_text(text, reply_markup=main_kb())

@dp.callback_query(F.data == "change_bet")
async def change_bet(call: types.CallbackQuery):
    # Переключение ставок
    bets = [10, 25, 50, 100, 250, 500]
    current = user_data['bet']
    next_idx = (bets.index(current) + 1) % len(bets) if current in bets else 0
    user_data['bet'] = bets[next_idx]
    await call.answer(f"💸 Ставка изменена на {user_data['bet']} m¢")
    await back_to_main(call)

async def main():
    print("🤖 Бот запущен!")
    print("💰 Начальный баланс: 1000 m¢")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
