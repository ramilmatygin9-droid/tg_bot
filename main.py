# casino_bot.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

import asyncio
import random
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# ========== КОНФИГ ==========
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # СЮДА ВСТАВЬ ТОКЕН ОТ @BotFather
ADMIN_IDS = [123456789]  # СЮДА ВСТАВЬ СВОЙ ID

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  balance INTEGER DEFAULT 1000,
                  games_played INTEGER DEFAULT 0,
                  games_won INTEGER DEFAULT 0,
                  last_bonus TEXT,
                  last_command TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS jackpot
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  amount INTEGER DEFAULT 0)''')
    c.execute("SELECT COUNT(*) FROM jackpot")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO jackpot (amount) VALUES (0)")
    conn.commit()
    conn.close()

def get_user(user_id: int):
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
        "games_played": user[3],
        "games_won": user[4],
        "last_bonus": user[5],
        "last_command": user[6]
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
    c.execute("UPDATE users SET games_played = games_played + 1 WHERE user_id = ?", (user_id,))
    if win > 0:
        c.execute("UPDATE users SET games_won = games_won + 1 WHERE user_id = ?", (user_id,))
    # Джекпот налог
    tax = int(bet * 0.01)
    if tax > 0:
        c.execute("UPDATE jackpot SET amount = amount + ?", (tax,))
    conn.commit()
    conn.close()

def update_last_command(user_id: int):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_command = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_last_command_time(user_id: int):
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

def get_top_players(limit=10):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    result = c.fetchall()
    conn.close()
    return result

def format_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")

# ========== ИГРЫ ==========
def roulette_spin(bet_type: str):
    number = random.randint(0, 36)
    if number == 0:
        color = "green"
    elif number % 2 == 0:
        color = "black"
    else:
        color = "red"
    
    if bet_type == "red" and color == "red":
        return number, True
    if bet_type == "black" and color == "black":
        return number, True
    if bet_type.isdigit() and int(bet_type) == number:
        return number, True
    return number, False

def slots_spin():
    symbols = ["🍒", "🍋", "🍊", "🍉", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    combo = "".join(result)
    mult = {
        "🍒🍒🍒": 3, "🍋🍋🍋": 3, "🍊🍊🍊": 3,
        "🍉🍉🍉": 3, "💎💎💎": 10, "7️⃣7️⃣7️⃣": 50
    }
    return combo, mult.get(combo, 0)

def dice_roll():
    return random.randint(1, 6), random.randint(1, 6)

# ========== БОТ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()
    
    user = get_user(user_id)
    await message.answer(
        f"🎰 <b>Добро пожаловать в Казино!</b>\n\n"
        f"💰 Твой баланс: {format_num(user['balance'])} 🪙\n\n"
        f"🎮 <b>Команды:</b>\n"
        f"/roulette [ставка] [красное/черное/число]\n"
        f"/slots [ставка]\n"
        f"/dice [ставка] [больше/меньше/ничья]\n"
        f"/bonus - ежедневный бонус (+200)\n"
        f"/profile - статистика\n"
        f"/top - топ игроков\n"
        f"/jackpot - джекпот",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("bonus"))
async def bonus(message: types.Message):
    user = get_user(message.from_user.id)
    last = datetime.fromisoformat(user['last_bonus']) if user['last_bonus'] else None
    
    if last:
        diff = (datetime.now() - last).total_seconds()
        if diff < 86400:
            hours = int((86400 - diff) // 3600)
            mins = int(((86400 - diff) % 3600) // 60)
            await message.answer(f"⏰ Бонус через {hours}ч {mins}мин")
            return
    
    update_balance(message.from_user.id, 200)
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (datetime.now().isoformat(), message.from_user.id))
    conn.commit()
    conn.close()
    await message.answer("✅ Получено +200 🪙")

@dp.message(Command("profile"))
async def profile(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"👤 <b>Профиль</b>\n\n"
        f"💰 Баланс: {format_num(user['balance'])} 🪙\n"
        f"🎮 Сыграно: {user['games_played']}\n"
        f"🏆 Побед: {user['games_won']}",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("top"))
async def top(message: types.Message):
    top_list = get_top_players()
    text = "🏆 <b>Топ игроков</b>\n\n"
    for i, (uid, name, bal) in enumerate(top_list[:10], 1):
        text += f"{i}. {name or uid} — {format_num(bal)} 🪙\n"
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("jackpot"))
async def jackpot(message: types.Message):
    jp = get_jackpot()
    await message.answer(f"🎰 <b>Джекпот:</b> {format_num(jp)} 🪙", parse_mode=ParseMode.HTML)

@dp.message(Command("roulette"))
async def roulette(message: types.Message):
    last = get_last_command_time(message.from_user.id)
    if last:
        diff = (datetime.now() - last).total_seconds()
        if diff < 3:
            await message.answer(f"⏰ Подожди {int(3-diff)} сек")
            return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Пример: /roulette 100 красное")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка должна быть числом")
        return
    
    user = get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"❌ Не хватает! Баланс: {format_num(user['balance'])}")
        return
    
    option = parts[2].lower()
    bet_type = None
    mult = 1
    
    if option in ["красное", "красный", "red"]:
        bet_type = "red"
        mult = 2
    elif option in ["черное", "черный", "black"]:
        bet_type = "black"
        mult = 2
    else:
        try:
            num = int(option)
            if 0 <= num <= 36:
                bet_type = str(num)
                mult = 35
        except:
            pass
    
    if not bet_type:
        await message.answer("❌ Выбери: красное, черное или число 0-36")
        return
    
    number, won = roulette_spin(bet_type)
    color = "зеленое" if number == 0 else ("красное" if number % 2 else "черное")
    
    if won:
        win_sum = bet * mult
        update_balance(message.from_user.id, win_sum)
        add_game_log(message.from_user.id, "roulette", bet, win_sum)
        await message.answer(f"🎡 Выпало: {number} ({color})\n✅ Выигрыш +{format_num(win_sum)} 🪙")
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "roulette", bet, 0)
        await message.answer(f"🎡 Выпало: {number} ({color})\n❌ Проигрыш -{format_num(bet)} 🪙")
    
    update_last_command(message.from_user.id)

@dp.message(Command("slots"))
async def slots(message: types.Message):
    last = get_last_command_time(message.from_user.id)
    if last and (datetime.now() - last).total_seconds() < 3:
        await message.answer("⏰ Подожди 3 сек")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Пример: /slots 100")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка числом")
        return
    
    user = get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"❌ Не хватает! Баланс: {format_num(user['balance'])}")
        return
    
    combo, mult = slots_spin()
    if mult > 0:
        win_sum = bet * mult
        update_balance(message.from_user.id, win_sum)
        add_game_log(message.from_user.id, "slots", bet, win_sum)
        await message.answer(f"🎰 {combo} x{mult}\n✅ +{format_num(win_sum)} 🪙")
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "slots", bet, 0)
        await message.answer(f"🎰 {combo}\n❌ -{format_num(bet)} 🪙")
    
    update_last_command(message.from_user.id)

@dp.message(Command("dice"))
async def dice(message: types.Message):
    last = get_last_command_time(message.from_user.id)
    if last and (datetime.now() - last).total_seconds() < 3:
        await message.answer("⏰ Подожди 3 сек")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Пример: /dice 100 больше")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка числом")
        return
    
    bet_type = parts[2].lower()
    if bet_type not in ["больше", "меньше", "ничья"]:
        await message.answer("❌ больше/меньше/ничья")
        return
    
    user = get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer(f"❌ Не хватает! {format_num(user['balance'])}")
        return
    
    p, b = dice_roll()
    win = False
    if (bet_type == "больше" and p > b) or (bet_type == "меньше" and p < b) or (bet_type == "ничья" and p == b):
        win = True
    
    if win:
        win_sum = bet * 2
        update_balance(message.from_user.id, win_sum)
        add_game_log(message.from_user.id, "dice", bet, win_sum)
        await message.answer(f"🎲 Твой {p} | Бот {b}\n✅ +{format_num(win_sum)} 🪙")
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "dice", bet, 0)
        await message.answer(f"🎲 Твой {p} | Бот {b}\n❌ -{format_num(bet)} 🪙")
    
    update_last_command(message.from_user.id)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "🎮 <b>Команды:</b>\n"
        "/roulette 100 красное\n"
        "/slots 50\n"
        "/dice 200 больше\n"
        "/bonus - ежедневно +200\n"
        "/profile - статистика\n"
        "/top - топ\n"
        "/jackpot - джекпот",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("give"))
async def give_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет прав")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ /give @username 500")
        return
    
    target = parts[1].replace("@", "")
    try:
        amount = int(parts[2])
    except:
        await message.answer("❌ Число")
        return
    
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, target))
    if c.rowcount == 0:
        await message.answer("❌ Не найден")
    else:
        conn.commit()
        await message.answer(f"✅ Выдано {amount} @{target}")
    conn.close()

# ========== ЗАПУСК ==========
async def main():
    init_db()
    print("🤖 Бот запущен! Проверь Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
