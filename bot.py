import asyncio
import logging
import random
import sqlite3
import time
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand, BotCommandScopeDefault, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAFkS4GaCYxGEyFyAwgqsqyah-d9PPNHeH0"
ADMIN_TOKEN = "8359920618:AAE4fi9nt5rZCihjYNuhVZxzEuvwPKjiDbk" 
OWNER_ID = 8462392581 

# --- PREMIUM EMOJI IDS (Для красоты интерфейса) ---
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"        
INVENTORY_ID = "5431445210141852444"
ERROR_EMOJI_ID = "5240241223632954241" 
NOTEBOOK_ID = "5461019131329402505"    
CHECK_MARK_ID = "5316939641503365999"
STAR_TOP_ID = "5472256585323522641"
CASE_EMOJI_ID = "5215535352319602416"

# Медальки для ТОПа
MEDAL_1_ID = "5440539497383087970"
MEDAL_2_ID = "5447203607294265305"
MEDAL_3_ID = "5453902265922376865"

# --- ДАННЫЕ О КРИСТАЛЛАХ ---
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "price": 5000},
    "Premium1": {"name": "Премиум кристалл I", "price": 10000},
    "Premium2": {"name": "Премиум кристалл II", "price": 15000},
    "Premium3": {"name": "Премиум кристалл III", "price": 25000}
}

# --- МАГАЗИН КЕЙСОВ ---
CASES_DATA = {
    "common": {"name": "📦 Обычный кейс", "price": 5000},
    "rare": {"name": "🎁 Редкий кейс", "price": 15000},
    "mythic": {"name": "👑 Мифический кейс", "price": 50000}
}

# --- МАГАЗИН КИРОК (10 УРОВНЕЙ) ---
SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.8},
    3: {"name": "Железная кирка", "price": 15000, "mult": 3.2},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 7.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 15.0},
    6: {"name": "Обсидиановая кирка", "price": 500000, "mult": 35.0},
    7: {"name": "Изумрудная кирка", "price": 1500000, "mult": 80.0},
    8: {"name": "Магматическая кирка", "price": 4000000, "mult": 200.0},
    9: {"name": "Незеритовая кирка", "price": 10000000, "mult": 500.0},
    10: {"name": "🌟 КИРКА БЕСКОНЕЧНОСТИ", "price": 25000000, "mult": 1500.0}
}

active_miners = set()
main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БЛОК РАБОТЫ С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('miner_game.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                    (user_id INTEGER PRIMARY KEY, balance INTEGER, pick_lvl INTEGER, used_promos TEXT, 
                    username TEXT, last_bonus INTEGER DEFAULT 0, inventory TEXT DEFAULT '1', 
                    crystals TEXT DEFAULT '{}', cases TEXT DEFAULT '{}')''')
    cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
                    (code TEXT PRIMARY KEY, reward INTEGER, expire_at TEXT)''')
    
    # Проверка структуры на наличие новых колонок
    cur.execute("PRAGMA table_info(players)")
    cols = [c[1] for c in cur.fetchall()]
    if 'crystals' not in cols: cur.execute("ALTER TABLE players ADD COLUMN crystals TEXT DEFAULT '{}'")
    if 'cases' not in cols: cur.execute("ALTER TABLE players ADD COLUMN cases TEXT DEFAULT '{}'")
    
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
    data = db_query("SELECT balance, pick_lvl, used_promos, last_bonus, inventory, crystals, username, cases FROM players WHERE user_id = ?", (user_id,), fetchone=True)
    if not data:
        db_query("INSERT INTO players (user_id, balance, pick_lvl, used_promos, username, inventory, crystals, cases) VALUES (?, 0, 1, '', ?, '1', '{}', '{}')", (user_id, username), commit=True)
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "inventory": [1], "crystals": {}, "username": username, "cases": {}}
    
    if username:
        db_query("UPDATE players SET username = ? WHERE user_id = ?", (username, user_id), commit=True)
    
    return {
        "balance": data[0], "pick_lvl": data[1], 
        "used_promos": data[2].split(",") if data[2] else [], 
        "last_bonus": data[3], 
        "inventory": [int(x) for x in data[4].split(",")] if data[4] else [1],
        "crystals": json.loads(data[5] if data[5] else "{}"), 
        "username": data[6],
        "cases": json.loads(data[7] if data[7] else "{}")
    }

# --- БЛОК АДМИНИСТРИРОВАНИЯ (ADMIN BOT) ---
@dp_admin.message(Command("start"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Панель управления промокодами</b>\n\n/add CODE REWARD HOURS\n/del CODE\n/list", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        args = message.text.split()
        code = args[1].upper()
        reward = int(args[2])
        hours = int(args[3])
        expire = "NEVER" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Промокод <b>{code}</b> создан!\nНаграда: {reward}💰\nИстекает: {expire}", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\nПример: /add NEWYEAR 5000 24")

@dp_admin.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        code = message.text.split()[1].upper()
        db_query("DELETE FROM promo_codes WHERE code = ?", (code,), commit=True)
        await message.answer(f"🗑 Промокод {code} удален.")
    except: pass

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    if not promos: return await message.answer("Список промокодов пуст.")
    text = "🎫 <b>Список активных промокодов:</b>\n\n"
    for p in promos:
        text += f"• <code>{p[0]}</code> | {p[1]}💰 | до {p[2]}\n"
    await message.answer(text, parse_mode="HTML")

# --- БЛОК ИГРОВЫХ КОМАНД (MAIN BOT) ---
@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    start_text = (
        f"<b>─── 〈 <tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> MINER WORLD 〉 ───</b>\n\n"
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        f"🔹 <b>/mine</b> — Отправиться в шахту\n"
        f"🔹 <b>/shop</b> — Магазин кирок\n"
        f"🔹 <b>/cases</b> — Магазин кейсов\n"
        f"🔹 <b>/sell</b> — Продать кристаллы\n"
        f"🔹 <b>/balance</b> — Проверить счет\n"
        f"🔹 <b>/inventory</b> — Твои вещи\n"
        f"🔹 <b>/top</b> — Рейтинг игроков\n"
        f"🔹 <b>/promo</b> — Ввести код\n"
    )
    await message.answer(start_text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners:
        return await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>Вы уже в шахте! Подождите...</b>', parse_mode="HTML")
    
    active_miners.add(user_id)
    p = get_player(user_id, message.from_user.username)
    
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Вы копаете ресурсы...</b>', parse_mode="HTML")
    await asyncio.sleep(random.randint(5, 8))
    
    reward = int(random.randint(200, 600) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    
    crystal_msg = ""
    if random.random() < 0.35:
        c_key = random.choices(["Common", "Rare", "SuperRare"], weights=[70, 25, 5])[0]
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        db_query("UPDATE players SET crystals = ? WHERE user_id = ?", (json.dumps(p["crystals"]), user_id), commit=True)
        crystal_msg = f'\n✨ Вы нашли: <b>{CRYSTALS_DATA[c_key]["name"]}</b>!'

    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, user_id), commit=True)
    active_miners.remove(user_id)
    
    await status_msg.delete()
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Вы добыли: <b>{reward}</b> монет!{crystal_msg}', parse_mode="HTML")

# --- СИСТЕМА КЕЙСОВ ---
@dp_main.message(Command("cases"))
async def cases_menu(message: types.Message):
    p = get_player(message.from_user.id)
    text = f'<tg-emoji emoji-id="{CASE_EMOJI_ID}">📦</tg-emoji> <b>Магазин и открытие кейсов</b>\n\n'
    kb = []
    
    for cid, info in CASES_DATA.items():
        count = p["cases"].get(cid, 0)
        text += f"▪️ {info['name']}\nЦена: <b>{info['price']}💰</b> | У вас: <b>{count}</b> шт.\n\n"
        kb.append([
            InlineKeyboardButton(text=f"Купить {info['name']}", callback_data=f"buycase_{cid}"),
            InlineKeyboardButton(text=f"Открыть {info['name']}", callback_data=f"opencase_{cid}")
        ])
    
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buycase_"))
async def buy_case_handler(c: types.CallbackQuery):
    cid = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    price = CASES_DATA[cid]["price"]
    
    if p["balance"] < price:
        return await c.answer("❌ Недостаточно средств на балансе!", show_alert=True)
    
    p["cases"][cid] = p["cases"].get(cid, 0) + 1
    db_query("UPDATE players SET balance = balance - ?, cases = ? WHERE user_id = ?", 
             (price, json.dumps(p["cases"]), c.from_user.id), commit=True)
    await c.answer(f"✅ Успешно куплен {CASES_DATA[cid]['name']}!")
    await cases_menu(c.message)
    await c.message.delete()

@dp_main.callback_query(F.data.startswith("opencase_"))
async def open_case_handler(c: types.CallbackQuery):
    cid = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    
    if p["cases"].get(cid, 0) <= 0:
        return await c.answer("❌ У вас нет этого кейса в инвентаре!", show_alert=True)
    
    p["cases"][cid] -= 1
    
    # Вероятности дропа
    if cid == "common":
        res = random.choices([("money", 5000), ("money", 10000), ("crystal", "Rare")], weights=[60, 30, 10])[0]
    elif cid == "rare":
        res = random.choices([("money", 20000), ("crystal", "SuperRare"), ("crystal", "Premium1")], weights=[50, 30, 20])[0]
    else: # mythic
        res = random.choices([("money", 150000), ("crystal", "Premium2"), ("crystal", "Premium3")], weights=[40, 30, 30])[0]
        
    if res[0] == "money":
        db_query("UPDATE players SET balance = balance + ?, cases = ? WHERE user_id = ?", (res[1], json.dumps(p["cases"]), c.from_user.id), commit=True)
        msg = f"🎊 Открыв кейс, вы получили: <b>{res[1]}💰</b>"
    else:
        p["crystals"][res[1]] = p["crystals"].get(res[1], 0) + 1
        db_query("UPDATE players SET crystals = ?, cases = ? WHERE user_id = ?", (json.dumps(p["crystals"]), json.dumps(p["cases"]), c.from_user.id), commit=True)
        msg = f"🎊 Джекпот! Выпал кристалл: <b>{CRYSTALS_DATA[res[1]]['name']}</b>"
        
    await c.message.answer(msg, parse_mode="HTML")
    await cases_menu(c.message)
    await c.message.delete()

# --- МАГАЗИН И ИНВЕНТАРЬ ---
@dp_main.message(Command("shop"))
async def main_shop(message: types.Message):
    p = get_player(message.from_user.id)
    text = f'<tg-emoji emoji-id="{NOTEBOOK_ID}">📓</tg-emoji> <b>Магазин профессиональных кирок</b>\n\n'
    kb = []
    
    # Показываем только ту кирку, которая идет следующей после текущей
    next_lvl = p["pick_lvl"] + 1
    if next_lvl in SHOP_PICKS:
        pick = SHOP_PICKS[next_lvl]
        text += f"Уровень {next_lvl}: <b>{pick['name']}</b>\n"
        text += f"Цена: <b>{pick['price']}💰</b>\n"
        text += f"Эффективность: <b>x{pick['mult']}</b> к добыче\n\n"
        kb.append([InlineKeyboardButton(text=f"Купить за {pick['price']}💰", callback_data=f"buy_{next_lvl}")])
    else:
        text += "🌟 У вас уже самая лучшая кирка в мире!"
            
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_callback(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        inv = p["inventory"]
        if lvl not in inv: inv.append(lvl)
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ?, inventory = ? WHERE user_id = ?", 
                 (SHOP_PICKS[lvl]["price"], lvl, ",".join(map(str, inv)), c.from_user.id), commit=True)
        await c.message.edit_text(f'<tg-emoji emoji-id="{CHECK_MARK_ID}">✅</tg-emoji> <b>Поздравляем! Вы приобрели {SHOP_PICKS[lvl]["name"]}!</b>', parse_mode="HTML")
    else:
        await c.answer("❌ Недостаточно монет для покупки!", show_alert=True)

@dp_main.message(Command("inventory"))
async def main_inventory(message: types.Message):
    p = get_player(message.from_user.id)
    text = f'<tg-emoji emoji-id="{INVENTORY_ID}">🎒</tg-emoji> <b>Ваш инвентарь:</b>\n\n'
    text += f'⛏ <b>Текущая кирка:</b> {SHOP_PICKS[p["pick_lvl"]]["name"]} (x{SHOP_PICKS[p["pick_lvl"]]["mult"]})\n'
    
    cry_text = ""
    for k, v in p["crystals"].items():
        if v > 0: cry_text += f"• {CRYSTALS_DATA[k]['name']}: <b>{v}</b> шт.\n"
    
    case_text = ""
    for k, v in p["cases"].items():
        if v > 0: case_text += f"• {CASES_DATA[k]['name']}: <b>{v}</b> шт.\n"
        
    text += f"\n💎 <b>Найденные кристаллы:</b>\n{cry_text if cry_text else '<i>Пусто</i>'}\n"
    text += f"\n📦 <b>Запасы кейсов:</b>\n{case_text if case_text else '<i>Пусто</i>'}"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("sell"))
async def main_sell(message: types.Message):
    p = get_player(message.from_user.id)
    kb = []
    text = "💎 <b>Рынок продажи кристаллов:</b>\n\n"
    for k, v in p["crystals"].items():
        if v > 0:
            price = CRYSTALS_DATA[k]["price"]
            kb.append([InlineKeyboardButton(text=f"Продать {CRYSTALS_DATA[k]['name']} ({price}💰)", callback_data=f"sell_{k}")])
    
    if not kb: text += "У вас пока нет кристаллов на продажу. Копайте в шахте!"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp_main.callback_query(F.data.startswith("sell_"))
async def sell_callback(c: types.CallbackQuery):
    key = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    if p["crystals"].get(key, 0) > 0:
        p["crystals"][key] -= 1
        price = CRYSTALS_DATA[key]["price"]
        db_query("UPDATE players SET balance = balance + ?, crystals = ? WHERE user_id = ?", (price, json.dumps(p["crystals"]), c.from_user.id), commit=True)
        await c.answer(f"💰 Вы получили +{price} монет!")
        await main_sell(c.message)
        await c.message.delete()

# --- СТАТИСТИКА И БОНУСЫ ---
@dp_main.message(Command("balance"))
async def main_balance(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Ваш игровой баланс: <b>{p["balance"]}</b> монет.', parse_mode="HTML")

@dp_main.message(Command("top"))
async def main_top(message: types.Message):
    top_users = db_query("SELECT username, balance FROM players ORDER BY balance DESC LIMIT 10", fetchall=True)
    text = f'<tg-emoji emoji-id="{STAR_TOP_ID}">✨</tg-emoji> <b>РЕЙТИНГ ТОП-10 МАЙНЕРОВ:</b>\n\n'
    for i, user in enumerate(top_users, 1):
        medal = ""
        if i == 1: medal = f'<tg-emoji emoji-id="{MEDAL_1_ID}">🥇</tg-emoji>'
        elif i == 2: medal = f'<tg-emoji emoji-id="{MEDAL_2_ID}">🥈</tg-emoji>'
        elif i == 3: medal = f'<tg-emoji emoji-id="{MEDAL_3_ID}">🥉</tg-emoji>'
        text += f"{i}. {medal} <b>{user[0] or 'Игрок'}</b> — {user[1]}💰\n"
    await message.answer(text, parse_mode="HTML")

@dp_main.message(Command("bonus"))
async def main_bonus(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        rem = 86400 - (now - p["last_bonus"])
        return await message.answer(f"❌ Следующий бонус можно забрать через: <b>{rem//3600}ч {(rem%3600)//60}м</b>", parse_mode="HTML")
    
    db_query("UPDATE players SET balance = balance + 2000, last_bonus = ? WHERE user_id = ?", (now, message.from_user.id), commit=True)
    await message.answer(f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> Ежедневная награда получена: <b>2000💰</b>!', parse_mode="HTML")

@dp_main.message(Command("promo"))
async def main_promo(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.reply("Введите код: <code>/promo КОД</code>", parse_mode="HTML")
    
    code = command.args.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    
    if not promo:
        return await message.reply("❌ Промокод не существует или уже неактивен.")
    
    p = get_player(message.from_user.id)
    if code in p["used_promos"]:
        return await message.reply("❌ Вы уже активировали этот код ранее.")
    
    if promo[1] != "NEVER" and datetime.now() > datetime.strptime(promo[1], "%Y-%m-%d %H:%M:%S"):
        return await message.reply("❌ Срок действия этого промокода уже закончился.")
    
    p["used_promos"].append(code)
    db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", (promo[0], ",".join(p["used_promos"]), message.from_user.id), commit=True)
    await message.reply(f"✅ Промокод успешно активирован!\nНачислено: <b>{promo[0]}💰</b>", parse_mode="HTML")

# --- ГЛАВНЫЙ ЗАПУСК ---
async def main():
    init_db()
    # Установка команд в меню Telegram
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/mine", description="Добывать ресурсы"),
        BotCommand(command="/cases", description="Кейсы"),
        BotCommand(command="/shop", description="Магазин кирок"),
        BotCommand(command="/sell", description="Продать камни"),
        BotCommand(command="/balance", description="Мои деньги"),
        BotCommand(command="/inventory", description="Что в рюкзаке"),
        BotCommand(command="/top", description="Лидеры игры"),
        BotCommand(command="/bonus", description="Подарок раз в день"),
        BotCommand(command="/promo", description="Активация кода")
    ], scope=BotCommandScopeDefault())
    
    print("--- СИСТЕМА ЗАПУЩЕНА ---")
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Работа ботов завершена!")

