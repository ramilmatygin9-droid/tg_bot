import asyncio
import logging
import random
import sqlite3
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
OWNER_ID = 8462392581 

# Эмодзи и Кастомные ID
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
SKUPSHIK_ID = "5452136652111620778"   

# Алмазы
DIAMOND_COMMON = "6269061400568532047"  
DIAMOND_UNCOMMON = "626938354888535501" 
DIAMOND_RARE = "6269242583763913842"     

# Премиум кубки для ТОПа
CUP_GOLD = "5318821943825154339"
CUP_SILVER = "5318991475512453472"
CUP_BRONZE = "5319114256245863261"

# ЦЕНЫ НА КИРКИ
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 25000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 100000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 500000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 2000000, "mult": 10.0}
}

main_bot = Bot(token=MAIN_TOKEN)
dp_main = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, 
                   used_promos TEXT, username TEXT, last_bonus INTEGER DEFAULT 0,
                   count_common INTEGER DEFAULT 0, count_uncommon INTEGER DEFAULT 0, count_rare INTEGER DEFAULT 0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promocodes 
                   (code TEXT PRIMARY KEY, reward INTEGER, expire_time INTEGER)''')
    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute(query, params)
    res = cur.fetchone() if fetchone else (cur.fetchall() if fetchall else None)
    if commit: conn.commit()
    conn.close()
    return res

def get_player(user_id, username=None):
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, count_common, count_uncommon, count_rare FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, last_bonus) VALUES (?, 0, 1, '', ?, 0)", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "common": 0, "uncommon": 0, "rare": 0}
    if username: db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    return {"balance": data[0], "pick_lvl": data[1], "used_promos": data[2].split(",") if data[2] else [], "last_bonus": data[3], "common": data[4], "uncommon": data[5], "rare": data[6]}

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ПРОМОКОДАМИ (АДМИН) ---

@dp_main.message(Command("add"))
async def admin_add(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID: return
    args = command.args.split() if command.args else []
    if len(args) < 3: return await message.answer("Команды:\n• /add НАЗВАНИЕ СУММА ЧАСЫ")
    
    code, reward, hours = args[0].upper(), int(args[1]), int(args[2])
    expire = 0 if hours == 0 else int(time.time()) + (hours * 3600)
    db_query("INSERT OR REPLACE INTO promocodes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
    
    time_str = "вечный" if expire == 0 else datetime.fromtimestamp(expire).strftime('%Y-%m-%d %H:%M:%S')
    await message.answer(f"✅ Код <b>{code}</b> на {reward} монет создан! (До: {time_str})", parse_mode="HTML")

@dp_main.message(Command("del"))
async def admin_del(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID: return
    if not command.args: return await message.answer("• /del НАЗВАНИЕ")
    db_query("DELETE FROM promocodes WHERE code = ?", (command.args.upper(),), commit=True)
    await message.answer(f"❌ Код {command.args.upper()} удален.")

@dp_main.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    codes = db_query("SELECT code, reward, expire_time FROM promocodes", fetchall=True)
    if not codes: return await message.answer("Пусто.")
    res = "📜 <b>Список кодов:</b>\n"
    for c, r, e in codes:
        t = "вечный" if e == 0 else datetime.fromtimestamp(e).strftime('%H:%M %d.%m')
        res += f"• <code>{c}</code> | {r}💰 | До: {t}\n"
    await message.answer(res, parse_mode="HTML")

# --- ИГРОВЫЕ КОМАНДЫ (СТАРЫЕ ТЕКСТЫ) ---

@dp_main.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == OWNER_ID:
        return await message.answer("🛠 <b>Панель управления промокодами</b>\n\n• /add КОД СУММА ЧАСЫ (0 - вечный)\n• /del КОД - Удалить\n• /list - Все коды", parse_mode="HTML")
    
    p = get_player(message.from_user.id, message.from_user.username)
    pick = SHOP_PICKS[p["pick_lvl"]]
    
    welcome_text = (
        f"<b><tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> ДОБРО ПОЖАЛОВАТЬ В MINER SIMULATOR <tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Привет, <b>@{message.from_user.username or message.from_user.first_name}</b>!\n\n"
        f"⚙️ <b>Твое снаряжение:</b>\n"
        f"└ Кирка: <code>{pick['name']}</code>\n"
        f"└ Множитель: <code>x{pick['mult']}</code>\n\n"
        f"🎒 <b>Твой инвентарь:</b>\n"
        f"<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Обычные: <b>{p['common']}</b>\n"
        f"<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> Редкие: <b>{p['uncommon']}</b>\n"
        f"<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> Эпик: <b>{p['rare']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Баланс: <b>{p['balance']:,}</b> монет\n\n"
        f"⛏ Копай через /mine и стань лучшим!"
    )
    await message.answer(welcome_text, parse_mode="HTML")

@dp_main.message(Command("mine"))
async def cmd_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 12)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    
    for s in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try: await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except: pass
    
    luck = random.random()
    diamond_text = ""
    if luck < 0.05:
        db_query("UPDATE players SET count_rare = count_rare + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_RARE}">💎</tg-emoji> <b>Редкий алмаз!</b>'
    elif luck < 0.15:
        db_query("UPDATE players SET count_uncommon = count_uncommon + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_UNCOMMON}">💎</tg-emoji> <b>Полуредкий алмаз!</b>'
    elif luck < 0.40:
        db_query("UPDATE players SET count_common = count_common + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_COMMON}">💎</tg-emoji> <b>Обычный алмаз!</b>'

    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Добыто: <b>{reward}</b> монет{diamond_text}', parse_mode="HTML")

@dp_main.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    p = get_player(message.from_user.id)
    text = (f"🎒 <b>Твой инвентарь:</b>\n\n"
            f"<tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Обычные: <b>{p['common']}</b> шт.\n"
            f"<tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> Полуредкие: <b>{p['uncommon']}</b> шт.\n"
            f"<tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> Редкие: <b>{p['rare']}</b> шт.")
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("top"))
async def cmd_top(message: types.Message):
    top_players = db_query("SELECT username, balance FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = "🏆 <b>ТОП 10 МАЙНЕРОВ:</b>\n━━━━━━━━━━━━━━\n"
    for i, (name, bal) in enumerate(top_players, 1):
        user = f"@{name}" if name else "Аноним"
        pref = f"{i}."
        if i == 1: pref = f"<tg-emoji emoji-id='{CUP_GOLD}'>🥇</tg-emoji>"
        elif i == 2: pref = f"<tg-emoji emoji-id='{CUP_SILVER}'>🥈</tg-emoji>"
        elif i == 3: pref = f"<tg-emoji emoji-id='{CUP_BRONZE}'>🥉</tg-emoji>"
        text += f"{pref} <b>{user}</b> — 💰 <code>{bal:,}</code>\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("sale"))
async def cmd_sale(message: types.Message):
    p = get_player(message.from_user.id)
    total = (p['common'] * 1000) + (p['uncommon'] * 5000) + (p['rare'] * 15000)
    if total == 0:
        return await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> У тебя нет алмазов на продажу!", parse_mode="HTML")
    db_query("UPDATE players SET balance = balance + ?, count_common=0, count_uncommon=0, count_rare=0 WHERE user_id = ?", (total, message.from_user.id), commit=True)
    await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> Продано за <b>{total:,}</b> монет!", parse_mode="HTML")

@dp_main.message(Command("promo"))
async def cmd_promo(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Введите промокод: <code>/promo START</code>", parse_mode="HTML")
    code = command.args.upper()
    p = get_player(message.from_user.id)
    if code in p["used_promos"]: return await message.answer("❌ Вы уже использовали этот промокод!")
    
    data = db_query("SELECT reward, expire_time FROM promocodes WHERE code = ?", (code,), fetchone=True)
    if not data: return await message.answer("❌ Такого промокода не существует!")
    
    reward, expire = data
    if expire != 0 and int(time.time()) > expire: return await message.answer("❌ Срок действия промокода истек!")
    
    db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (reward, ",".join(p["used_promos"] + [code]), message.from_user.id), commit=True)
    await message.answer(f"✅ Промокод активирован!\nНачислено: <b>{reward:,}</b> монет", parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        rem = 86400 - (now - p["last_bonus"])
        return await message.answer(f"⏳ Бонус будет через <b>{rem//3600}ч. {(rem%3600)//60}м.</b>", parse_mode="HTML")
    gift = random.randint(500, 2500)
    db_query("UPDATE players SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (gift, now, message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Бонус: <b>{gift}</b> монет!', parse_mode="HTML")

@dp_main.message(Command("shop"))
async def cmd_shop(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"{v['name']} — {v['price']:,} 💵", callback_data=f"buy_{k}")] for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
    await message.answer(f'🛒 <b>Магазин кирок</b>', reply_markup=InlineKeyboardMarkup(inline_keyboard=kb or [[InlineKeyboardButton(text="Макс. уровень", callback_data="max")]]), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_h(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.message.edit_text(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!")
    else: await c.answer("Недостаточно монет!", show_alert=True)

async def main():
    init_db()
    await main_bot.delete_webhook(drop_pending_updates=True)
    await main_bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главная"),
        BotCommand(command="mine", description="⛏ Копать"),
        BotCommand(command="inventory", description="🎒 Инвентарь"),
        BotCommand(command="shop", description="🛒 Магазин"),
        BotCommand(command="sale", description="💎 Скупщик"),
        BotCommand(command="top", description="🏆 Топ"),
        BotCommand(command="promo", description="🎟 Промокод"),
        BotCommand(command="bonus", description="🎁 Бонус")
    ])
    await dp_main.start_polling(main_bot)

if __name__ == "__main__":
    asyncio.run(main())
