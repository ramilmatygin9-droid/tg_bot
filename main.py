import asyncio
import random
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Tuple

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# ========== КОНФИГ ==========
# ЗАМЕНИ ТОКЕН НА СВОЙ!
BOT_TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"
ADMIN_IDS = [8727191045]  # Твой ID (узнай в @userinfobot)

# Включаем логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

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
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 1000))
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
    res = c.fetchone()
    current = res[0] if res else 0
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
        try:
            return datetime.fromisoformat(result[0])
        except:
            return None
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
    return f"{n:,}".replace(",", " ")

# ========== ЛОГИКА ИГР ==========
def roulette_spin(bet_type: str):
    number = random.randint(0, 36)
    color = "green" if number == 0 else ("red" if number % 2 != 0 else "black")
    
    if bet_type == "red" and color == "red": return number, True
    if bet_type == "black" and color == "black": return number, True
    if bet_type.isdigit() and int(bet_type) == number: return number, True
    return number, False

def slots_spin():
    symbols = ["🍒", "🍋", "🍊", "🍉", "💎", "7️⃣"]
    res = [random.choice(symbols) for _ in range(3)]
    combo = "".join(res)
    mults = {"🍒🍒🍒": 3, "🍋🍋🍋": 3, "🍊🍊🍊": 3, "🍉🍉🍉": 5, "💎💎💎": 15, "7️⃣7️⃣7️⃣": 50}
    return combo, mults.get(combo, 0)

# ========== ХЕНДЛЕРЫ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"id{user_id}"
    
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    get_user(user_id) # Регистрируем если нет
    c.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()
    
    user = get_user(user_id)
    await message.answer(
        f"🎰 <b>Добро пожаловать, {username}!</b>\n\n"
        f"💰 Баланс: {format_num(user['balance'])} 🪙\n\n"
        f"🎮 <b>Команды:</b>\n"
        f"/roulette [ставка] [red/black/число]\n"
        f"/slots [ставка]\n"
        f"/dice [ставка] [больше/меньше/ничья]\n"
        f"/bonus - бонус раз в сутки\n"
        f"/profile - стата\n"
        f"/top - топ игроков",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("bonus"))
async def bonus(message: types.Message):
    user = get_user(message.from_user.id)
    last_str = user['last_bonus']
    
    if last_str:
        diff = (datetime.now() - datetime.fromisoformat(last_str)).total_seconds()
        if diff < 86400:
            rem = int(86400 - diff)
            await message.answer(f"⏰ Бонус будет доступен через {rem//3600}ч {(rem%3600)//60}мин")
            return
    
    update_balance(message.from_user.id, 200)
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (datetime.now().isoformat(), message.from_user.id))
    conn.commit()
    conn.close()
    await message.answer("✅ Ты получил 200 🪙!")

@router_roulette = F.text.startswith("/roulette") # Альтернативный способ
@dp.message(Command("roulette"))
async def roulette(message: types.Message):
    last = get_last_command_time(message.from_user.id)
    if last and (datetime.now() - last).total_seconds() < 3:
        await message.answer("⏰ Подожди 3 секунды!")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Формат: /roulette 100 red")
        return

    try:
        bet = int(args[1])
        if bet <= 0: raise ValueError
    except:
        await message.answer("❌ Ставка должна быть целым числом больше 0")
        return

    user = get_user(message.from_user.id)
    if user['balance'] < bet:
        await message.answer("❌ Недостаточно средств!")
        return

    target = args[2].lower()
    bet_type = None
    mult = 2
    
    if target in ["красное", "red", "к"]: bet_type = "red"
    elif target in ["черное", "black", "ч"]: bet_type = "black"
    elif target.isdigit() and 0 <= int(target) <= 36:
        bet_type = target
        mult = 35
    
    if not bet_type:
        await message.answer("❌ Выбери: red, black или число 0-36")
        return

    num, won = roulette_spin(bet_type)
    color = "🟢" if num == 0 else ("🔴" if num % 2 != 0 else "⚫️")
    
    if won:
        win_sum = bet * (mult - 1)
        update_balance(message.from_user.id, win_sum)
        add_game_log(message.from_user.id, "roulette", bet, win_sum)
        await message.answer(f"🎡 Выпало: {num} {color}\n✅ Выигрыш: +{format_num(bet*mult)} 🪙")
    else:
        update_balance(message.from_user.id, -bet)
        add_game_log(message.from_user.id, "roulette", bet, 0)
        await message.answer(f"🎡 Выпало: {num} {color}\n❌ Проигрыш: -{format_num(bet)} 🪙")
    
    update_last_command(message.from_user.id)

@dp.message(Command("slots"))
async def slots(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Формат: /slots 100")
        return
    
    try:
        bet = int(args[1])
    except:
        await message.answer("❌ Ошибка в ставке")
        return

    if not update_balance(message.from_user.id, -bet):
        await message.answer("❌ Нет денег!")
        return

    combo, mult = slots_spin()
    if mult > 0:
        win = bet * mult
        update_balance(message.from_user.id, win)
        await message.answer(f"🎰 {combo}\n✅ Джекпот! +{format_num(win)} 🪙")
    else:
        await message.answer(f"🎰 {combo}\n❌ Мимо! -{format_num(bet)} 🪙")

@dp.message(Command("top"))
async def top_cmd(message: types.Message):
    players = get_top_players()
    msg = "🏆 <b>ТОП ИГРОКОВ:</b>\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p[1]} — {format_num(p[2])} 🪙\n"
    await message.answer(msg, parse_mode=ParseMode.HTML)

@dp.message(Command("give"))
async def give(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    args = message.text.split()
    if len(args) < 3: return
    
    target = args[1].replace("@", "")
    amount = int(args[2])
    
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, target))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Выдано {amount} пользователю {target}")

# ========== ЗАПУСК ==========
async def main():
    init_db()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
