import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ТОКЕНОВ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"  # Основной бот
ADMIN_TOKEN = "8692818015:AAFr1AppqwvoF4lrmebWnWSaDgpAX7VB5LA" # Бот для промокодов
OWNER_ID = 8462392581  # Твой ID для управления

# Emoji ID
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
SUPPORT_ID = "5924712865763170353"    
GIFT_ID = "5792071541084659564"       
SHOP_ICON_ID = "5197269100878907942"  

# Инициализация ботов и диспетчеров
main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)

dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute(query, params)
    res = None
    if fetchone: res = cur.fetchone()
    if fetchall: res = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id):
    data = db_query("SELECT balance, pick_lvl, used_promos FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players VALUES (?, ?, ?, ?)", (user_id, 0, 1, ""), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": []}
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else []}

# --- ЛОГИКА АДМИН-БОТА (УПРАВЛЕНИЕ ПРОМО) ---

@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления промокодами</b>\n\n"
                         "• <code>/add КОД СУММА ЧАСЫ</code> (0 - вечный)\n"
                         "• <code>/del КОД</code> - Удалить\n"
                         "• <code>/list</code> - Все коды", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        _, code, reward, hours = message.text.split()
        expire = "NEVER" if hours == "0" else (datetime.now() + timedelta(hours=int(hours))).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code.upper(), int(reward), expire), commit=True)
        await message.answer(f"✅ Код <b>{code.upper()}</b> на {reward} монет создан! (До: {expire})", parse_mode="HTML")
    except: await message.answer("Ошибка! Пример: <code>/add START 5000 0</code>")

@dp_admin.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    code = message.text.split()[1].upper()
    db_query("DELETE FROM promo_codes WHERE code = ?", (code,), commit=True)
    await message.answer(f"🗑 Промокод {code} удален.")

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    text = "🎫 <b>Список кодов:</b>\n" + "\n".join([f"• {p[0]} - {p[1]} монет (До: {p[2]})" for p in promos])
    await message.answer(text if promos else "Кодов нет.", parse_mode="HTML")

# --- ЛОГИКА ОСНОВНОГО БОТА (ИГРА) ---

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Майнер запущен!</b>', parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait = random.randint(5, 10)
    msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>', parse_mode="HTML")
    
    for i in range(wait, 0, -1):
        await asyncio.sleep(1)
        try: await msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ {i} сек.', parse_mode="HTML")
        except: pass
    
    mults = {1: 1, 2: 1.5, 3: 2.5, 4: 5, 5: 10}
    reward = int(random.randint(200, 700) * mults.get(p["pick_lvl"], 1))
    new_bal = p["balance"] + reward
    db_query("UPDATE players SET balance = ? WHERE user_id = ?", (new_bal, message.from_user.id), commit=True)
    
    await msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Найдено: <b>{reward}</b>\nБаланс: <b>{new_bal}</b>', parse_mode="HTML")

@dp_main.message(Command("promo"))
async def main_promo_info(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{SHOP_ICON_ID}">📝</tg-emoji> <b>Введите промокод в чат:</b>', parse_mode="HTML")

@dp_main.message(F.text)
async def main_handle_text(message: types.Message):
    if message.text.startswith('/'): return
    code = message.text.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    
    if promo:
        reward, expire = promo
        p = get_player(message.from_user.id)
        if expire != "NEVER" and datetime.now() > datetime.strptime(expire, "%Y-%m-%d %H:%M:%S"):
            await message.reply("❌ Код просрочен!")
        elif code in p["used_promos"]:
            await message.reply("❌ Уже использовано!")
        else:
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", 
                     (reward, ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ +{reward} монет!")

# --- ЗАПУСК ОБОИХ БОТОВ ---
async def main():
    init_db()
    # Установка меню для основного бота
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Старт"),
        BotCommand(command="/mine", description="⛏ Копать"),
        BotCommand(command="/promo", description="🎫 Промо"),
        BotCommand(command="/balance", description="💰 Баланс")
    ], scope=BotCommandScopeDefault())
    
    print("Запуск обоих ботов...")
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
