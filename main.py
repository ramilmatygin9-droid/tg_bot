# casino_bot.py - полный код Telegram бота казино

import asyncio
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ========== КОНФИГ ==========
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замени на свой токен от @BotFather
ADMIN_IDS = [123456789]  # Замени на свой Telegram ID

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  balance INTEGER DEFAULT 1000,
                  total_bet INTEGER DEFAULT 0,
                  total_win INTEGER DEFAULT 0,
                  games_played INTEGER DEFAULT 0,
                  games_won INTEGER DEFAULT 0,
                  last_bonus TEXT,
                  last_command TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  game_type TEXT,
                  bet INTEGER,
                  win INTEGER,
                  timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS jackpot
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  amount INTEGER DEFAULT 0)''')
    c.execute("SELECT COUNT(*) FROM jackpot")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO jackpot (amount) VALUES (0)")
    conn.commit()
    conn.close()

def get_user(user_id: int) -> Dict:
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
    conn.close()
    return {
        "user_id": user[0],
        "username": user[1],
        "balance": user[2],
        "total_bet": user[3],
        "total_win": user[4],
        "games_played": user[5],
        "games_won": user[6],
        "last_bonus": user[7],
        "last_command": user[8]
    }

def update_balance(user_id: int, amount: int) -> bool:
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    current = c.fetchone()[0]
    if current + amount < 0:
        conn.close()
        return False
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True

def add_game_log(user_id: int, game_type: str, bet: int, win: int):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET games_played = games_played + 1, total_bet = total_bet + ? WHERE user_id = ?", (bet, user_id))
    if win > 0:
        c.execute("UPDATE users SET games_won = games_won + 1, total_win = total_win + ? WHERE user_id = ?", (win, user_id))
    jackpot_tax = int(bet * 0.01)
    if jackpot_tax > 0:
        c.execute("UPDATE jackpot SET amount = amount + ?", (jackpot_tax,))
    c.execute("INSERT INTO game_logs (user_id, game_type, bet, win, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, game_type, bet, win, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_last_command(user_id: int):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_command = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_last_command_time(user_id: int) -> Optional[datetime]:
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT last_command FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        return datetime.fromisoformat(result[0])
    return None

def get_jackpot() -> int:
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT amount FROM jackpot LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def reset_jackpot() -> int:
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT amount FROM jackpot LIMIT 1")
    amount = c.fetchone()[0]
    c.execute("UPDATE jackpot SET amount = 0")
    conn.commit()
    conn.close()
    return amount

def get_top_players(limit=10):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT user_id, username, balance, games_played, games_won FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    result = c.fetchall()
    conn.close()
    return result

def update_username(user_id: int, username: str):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()

# ========== УТИЛИТЫ ==========
def check_cooldown(last_time: Optional[datetime], seconds: int) -> Tuple[bool, int]:
    if not last_time:
        return True, 0
    diff = (datetime.now() - last_time).total_seconds()
    return (diff >= seconds, max(0, int(seconds - diff)))

def format_number(num: int) -> str:
    return f"{num:,}".replace(",", ".")

def roulette_spin(bet_type: str) -> Tuple[int, bool]:
    number = random.randint(0, 36)
    if number == 0:
        color = "green"
    elif number % 2 == 0:
        color = "black" if 1 <= number <= 10 or 19 <= number <= 28 else "red"
    else:
        color = "red" if 1 <= number <= 10 or 19 <= number <= 28 else "black"
    if bet_type == "red" and color == "red":
        return number, True
    if bet_type == "black" and color == "black":
        return number, True
    if bet_type.isdigit() and int(bet_type) == number:
        return number, True
    return number, False

def slots_spin() -> Tuple[str, int]:
    symbols = ["🍒", "🍋", "🍊", "🍉", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    combo = "".join(result)
    multipliers = {
        "🍒🍒🍒": 3, "🍋🍋🍋": 3, "🍊🍊🍊": 3,
        "🍉🍉🍉": 3, "💎💎💎": 10, "7️⃣7️⃣7️⃣": 50
    }
    return combo, multipliers.get(combo, 0)

def dice_roll() -> Tuple[int, int]:
    return random.randint(1, 6), random.randint(1, 6)

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="menu_slots"),
         InlineKeyboardButton(text="🎲 Кости", callback_data="menu_dice")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="menu_roulette"),
         InlineKeyboardButton(text="🎡 Колесо удачи", callback_data="menu_wheel")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
         InlineKeyboardButton(text="🏆 Топ игроков", callback_data="menu_top")]
    ])

def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

# ========== ОБРАБОТЧИКИ ==========
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    update_username(message.from_user.id, message.from_user.username or str(message.from_user.id))
    await message.answer(
        f"🎰 <b>Добро пожаловать в Казино!</b>\n\n"
        f"У тебя <b>{format_number(get_user(message.from_user.id)['balance'])} 🪙</b>\n\n"
        f"🎮 <b>Игры:</b>\n"
        f"• /roulette [ставка] [красное/черное/число] - Рулетка\n"
        f"• /slots [ставка] - Слоты (x3-x50)\n"
        f"• /dice [ставка] [больше/меньше/ничья] - Кости (x2)\n"
        f"• /wheel - Колесо удачи (бесплатно раз в 2 часа)\n"
        f"• /bonus - Ежедневный бонус\n"
        f"• /profile - Статистика\n"
        f"• /top - Топ игроков\n"
        f"• /jackpot - Текущий джекпот",
        reply_markup=main_menu()
    )

@dp.callback_query(lambda c: c.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("❌ Отменено")

@dp.callback_query(lambda c: c.data.startswith("menu_"))
async def menu_callback(callback: types.CallbackQuery):
    action = callback.data.replace("menu_", "")
    if action == "profile":
        user = get_user(callback.from_user.id)
        await callback.message.answer(
            f"👤 <b>Профиль</b>\n\n"
            f"🪙 Баланс: {format_number(user['balance'])}\n"
            f"🎮 Сыграно игр: {user['games_played']}\n"
            f"🏆 Побед: {user['games_won']}\n"
            f"💰 Всего ставок: {format_number(user['total_bet'])}\n"
            f"💎 Всего выигрышей: {format_number(user['total_win'])}"
        )
    elif action == "top":
        top = get_top_players()
        text = "🏆 <b>Топ игроков</b>\n\n"
        for i, (uid, name, balance, games, wins) in enumerate(top[:10], 1):
            text += f"{i}. {name or uid} — {format_number(balance)} 🪙\n"
        await callback.message.answer(text)
    else:
        await callback.message.answer(f"Используй команду /{action}")
    await callback.answer()

@dp.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    user = get_user(message.from_user.id)
    last_bonus = datetime.fromisoformat(user['last_bonus']) if user['last_bonus'] else None
    can_claim, wait = check_cooldown(last_bonus, 86400)
    if not can_claim:
        hours = wait // 3600
        minutes = (wait % 3600) // 60
        await message.answer(f"⏰ Бонус будет доступен через {hours}ч {minutes}мин")
        return
    update_balance(message.from_user.id, 200)
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (datetime.now().isoformat(), message.from_user.id))
    conn.commit()
    conn.close()
    await message.answer("✅ Ты получил ежедневный бонус: +200 🪙")

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"👤 <b>Профиль</b>\n\n"
        f"🪙 Баланс: {format_number(user['balance'])}\n"
        f"🎮 Сыграно игр: {user['games_played']}\n"
        f"🏆 Побед: {user['games_won']}\n"
        f"💰 Всего ставок: {format_number(user['total_bet'])}\n"
        f"💎 Всего выигрышей: {format_number(user['total_win'])}"
    )

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    top = get_top_players()
    text = "🏆 <b>Топ игроков</b>\n\n"
    for i, (uid, name, balance, games, wins) in enumerate(top[:10], 1):
        text += f"{i}. {name or uid} — {format_number(balance)} 🪙\n"
    await message.answer(text)

@dp.message(Command("jackpot"))
async def cmd_jackpot(message: types.Message):
    jackpot = get_jackpot()
    await message.answer(f"🎰 <b>Текущий джекпот:</b> {format_number(jackpot)} 🪙")

@dp.message(Command("roulette"))
async def cmd_roulette(message: types.Message):
    user = get_user(message.from_user.id)
    last_cmd = get_last_command_time(message.from_user.id)
    can, wait = check_cooldown(last_cmd, 3)
    if not can:
        await message.answer(f"⏰ Подожди {wait} сек перед следующей ставкой")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Пример: /roulette 100 красное\nВарианты: красное, черное, число 0-36")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка должна быть числом")
        return
    
    if bet <= 0:
        await message.answer("❌ Ставка должна быть положительной")
        return
    
    if user['balance'] < bet:
        await message.answer(f"❌ Не хватает монет! Твой баланс: {format_number(user['balance'])}")
        return
    
    option = parts[2].lower()
    bet_type = None
    multiplier = 1
    
    if option in ["красное", "красный", "red"]:
        bet_type = "red"
        multiplier = 2
    elif option in ["черное", "черный", "black"]:
        bet_type = "black"
        multiplier = 2
    else:
        try:
            num = int(option)
            if 0 <= num <= 36:
                bet_type = str(num)
                multiplier = 35
            else:
                raise ValueError
        except:
            await message.answer("❌ Выбери: красное, черное или число 0-36")
            return
    
    number, won = roulette_spin(bet_type)
    color_text = "зеленое (0)" if number == 0 else "красное" if number % 2 != 0 else "черное"
    
    if won:
        win_amount = bet * multiplier
        update_balance(message.from_user.id, win_amount)
        add_game_log(message.from_user.id, "roulette", bet, win_amount)
        await message.answer(
            f"🎡 <b>Рулетка</b>\n\n"
            f"Выпало: {number} ({color_text})\n"
            f"✅ Ты выиграл! +{format_number(win_amount)} 🪙"
        )
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "roulette", bet, 0)
        await message.answer(
            f"🎡 <b>Рулетка</b>\n\n"
            f"Выпало: {number} ({color_text})\n"
            f"❌ Ты проиграл {format_number(bet)} 🪙"
        )
    
    update_last_command(message.from_user.id)

@dp.message(Command("slots"))
async def cmd_slots(message: types.Message):
    user = get_user(message.from_user.id)
    last_cmd = get_last_command_time(message.from_user.id)
    can, wait = check_cooldown(last_cmd, 3)
    if not can:
        await message.answer(f"⏰ Подожди {wait} сек")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Пример: /slots 100")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка должна быть числом")
        return
    
    if bet <= 0:
        await message.answer("❌ Ставка положительная")
        return
    
    if user['balance'] < bet:
        await message.answer(f"❌ Не хватает монет! Баланс: {format_number(user['balance'])}")
        return
    
    combo, multiplier = slots_spin()
    emoji_combo = " ".join(list(combo))
    
    if multiplier > 0:
        win_amount = bet * multiplier
        update_balance(message.from_user.id, win_amount)
        add_game_log(message.from_user.id, "slots", bet, win_amount)
        await message.answer(
            f"🎰 <b>Слоты</b>\n\n"
            f"[ {emoji_combo} ]\n\n"
            f"✅ ВЫИГРЫШ x{multiplier}! +{format_number(win_amount)} 🪙"
        )
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "slots", bet, 0)
        await message.answer(
            f"🎰 <b>Слоты</b>\n\n"
            f"[ {emoji_combo} ]\n\n"
            f"❌ Проигрыш -{format_number(bet)} 🪙"
        )
    
    update_last_command(message.from_user.id)

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    user = get_user(message.from_user.id)
    last_cmd = get_last_command_time(message.from_user.id)
    can, wait = check_cooldown(last_cmd, 3)
    if not can:
        await message.answer(f"⏰ Подожди {wait} сек")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Пример: /dice 100 больше\nВарианты: больше, меньше, ничья")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка должна быть числом")
        return
    
    bet_type = parts[2].lower()
    if bet_type not in ["больше", "меньше", "ничья"]:
        await message.answer("❌ Выбери: больше, меньше, ничья")
        return
    
    if bet <= 0:
        await message.answer("❌ Ставка положительная")
        return
    
    if user['balance'] < bet:
        await message.answer(f"❌ Не хватает монет! Баланс: {format_number(user['balance'])}")
        return
    
    player_dice, bot_dice = dice_roll()
    
    if (bet_type == "больше" and player_dice > bot_dice) or \
       (bet_type == "меньше" and player_dice < bot_dice) or \
       (bet_type == "ничья" and player_dice == bot_dice):
        win_amount = bet * 2
        update_balance(message.from_user.id, win_amount)
        add_game_log(message.from_user.id, "dice", bet, win_amount)
        await message.answer(
            f"🎲 <b>Кости</b>\n\n"
            f"Твой кубик: {player_dice}\n"
            f"Кубик бота: {bot_dice}\n\n"
            f"✅ Ты выиграл! +{format_number(win_amount)} 🪙"
        )
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "dice", bet, 0)
        await message.answer(
            f"🎲 <b>Кости</b>\n\n"
            f"Твой кубик: {player_dice}\n"
            f"Кубик бота: {bot_dice}\n\n"
            f"❌ Ты проиграл {format_number(bet)} 🪙"
        )
    
    update_last_command(message.from_user.id)

@dp.message(Command("wheel"))
async def cmd_wheel(message: types.Message):
    user = get_user(message.from_user.id)
    last_wheel = datetime.fromisoformat(user['last_bonus']) if user['last_bonus'] else None
    can, wait = check_cooldown(last_wheel, 7200)
    if not can:
        hours = wait // 3600
        minutes = (wait % 3600) // 60
        await message.answer(f"⏰ Колесо удачи доступно через {hours}ч {minutes}мин")
        return
    
    prizes = [50, 100, 200, 500, 1000, 5000]
    win = random.choice(prizes)
    
    if win == 5000:
        jackpot = get_jackpot()
        win += jackpot
        reset_jackpot()
        await message.answer(f"🎡 <b>ДЖЕКПОТ КОЛЕСО УДАЧИ!</b>\n\nТы выиграл {format_number(win)} 🪙!!!")
    else:
        await message.answer(f"🎡 <b>Колесо удачи</b>\n\nТы выиграл {format_number(win)} 🪙")
    
    update_balance(message.from_user.id, win)
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (datetime.now().isoformat(), message.from_user.id))
    conn.commit()
    conn.close()

@dp.message(Command("give"))
async def cmd_give(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет прав")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Пример: /give @username 500")
        return
    
    target = parts[1].replace("@", "")
    try:
        amount = int(parts[2])
    except:
        await message.answer("❌ Сумма должна быть числом")
        return
    
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, target))
    if c.rowcount == 0:
        await message.answer("❌ Пользователь не найден")
    else:
        conn.commit()
        await message.answer(f"✅ Выдано {format_number(amount)} 🪙 пользователю @{target}")
    conn.close()

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🎰 <b>Команды казино:</b>\n\n"
        "/roulette [ставка] [красное/черное/число] - Рулетка (x2 или x35)\n"
        "/slots [ставка] - Слоты (x3, x10, x50)\n"
        "/dice [ставка] [больше/меньше/ничья] - Кости (x2)\n"
        "/wheel - Колесо удачи\n"
        "/bonus - Ежедневный бонус (+200)\n"
        "/profile - Статистика\n"
        "/top - Топ игроков\n"
        "/jackpot - Джекпот\n"
        "/help - Это меню"
    )

async def main():
    init_db()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
