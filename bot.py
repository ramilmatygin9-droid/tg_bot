import asyncio
import logging
import random
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"
OWNER_ID = 8462392581 

# Кастомные ID для эмодзи
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
GIFT_ID = "5792071541084659564"       
SKUPSHIK_ID = "5452136652111620778"   

DIAMOND_COMMON = "6269061400568532047"  
DIAMOND_UNCOMMON = "626938354888535501" 
DIAMOND_RARE = "6269242583763913842"     

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
                   (user_id INTEGER PRIMARY KEY, 
                   balance INTEGER, 
                   pick_lvl INTEGER, 
                   used_promos TEXT, 
                   username TEXT, 
                   last_bonus INTEGER DEFAULT 0,
                   count_common INTEGER DEFAULT 0,
                   count_uncommon INTEGER DEFAULT 0,
                   count_rare INTEGER DEFAULT 0)''')
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
        return {"balance": 0, "pick_lvl": 1, "common": 0, "uncommon": 0, "rare": 0}
    return {
        "balance": data[0], "pick_lvl": data[1], "common": data[4], "uncommon": data[5], "rare": data[6]
    }

# --- ОБРАБОТЧИКИ ---

@dp_main.message(Command("start"))
async def cmd_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> Привет, {message.from_user.first_name}!\n'
        f'Готов копать до посинения? Жми /menu',
        parse_mode="HTML"
    )

@dp_main.message(Command("mine"))
async def cmd_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 10)
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: <b>{wait_time}</b> сек.', parse_mode="HTML")
    
    for s in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: <b>{s}</b> сек.', parse_mode="HTML")
        except: break
    
    luck = random.random()
    diamond_text = ""
    if luck < 0.05:
        db_query("UPDATE players SET count_rare = count_rare + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_RARE}">💎</tg-emoji> <b>Нашел редкий алмаз!</b>'
    elif luck < 0.15:
        db_query("UPDATE players SET count_uncommon = count_uncommon + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_UNCOMMON}">💎</tg-emoji> <b>Нашел полуредкий алмаз!</b>'
    elif luck < 0.40:
        db_query("UPDATE players SET count_common = count_common + 1 WHERE user_id = ?", (message.from_user.id,), commit=True)
        diamond_text = f'\n<tg-emoji emoji-id="{DIAMOND_COMMON}">💎</tg-emoji> <b>Нашел обычный алмаз!</b>'

    reward = int(random.randint(200, 700) * SHOP_PICKS[p["pick_lvl"]]["mult"])
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (reward, message.from_user.id), commit=True)
    
    try: await status_msg.delete()
    except: pass
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> Прибыль: <b>{reward}</b> монет{diamond_text}', parse_mode="HTML")

@dp_main.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    p = get_player(message.from_user.id)
    pick_name = SHOP_PICKS.get(p['pick_lvl'], {}).get('name', 'Руки')
    
    total_val = (p['common'] * 1000) + (p['uncommon'] * 5000) + (p['rare'] * 15000)
    
    text = (f"🎒 <b>Твой инвентарь:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⛏ <b>Кирка:</b> {pick_name}\n\n"
            f"💎 <b>Ресурсы:</b>\n"
            f"├ <tg-emoji emoji-id='{DIAMOND_COMMON}'>💎</tg-emoji> Обычные: <b>{p['common']}</b> шт.\n"
            f"├ <tg-emoji emoji-id='{DIAMOND_UNCOMMON}'>💎</tg-emoji> Полуредкие: <b>{p['uncommon']}</b> шт.\n"
            f"└ <tg-emoji emoji-id='{DIAMOND_RARE}'>💎</tg-emoji> Редкие: <b>{p['rare']}</b> шт.\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤑 Оценка скупщика: <b>{total_val:,}</b> 💵")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Продать всё", callback_data="sale_action")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu_back")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp_main.message(Command("sale"))
async def cmd_sale(message: types.Message):
    p = get_player(message.from_user.id)
    total = (p['common'] * 1000) + (p['uncommon'] * 5000) + (p['rare'] * 15000)
    if total == 0:
        await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> У тебя пусто! Иди копай.")
        return
    db_query("UPDATE players SET balance = balance + ?, count_common=0, count_uncommon=0, count_rare=0 WHERE user_id = ?", (total, message.from_user.id), commit=True)
    await message.answer(f"<tg-emoji emoji-id='{SKUPSHIK_ID}'>🤓</tg-emoji> Сдал камни на <b>{total:,}</b> монет!")

@dp_main.message(Command("menu"))
async def cmd_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏ Копать", callback_data="mine_action")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv_action"),
         InlineKeyboardButton(text="🛒 Магазин", callback_data="shop_action")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus_action"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top_action")],
        [InlineKeyboardButton(text="💳 Баланс", callback_data="bal_action")]
    ])
    await message.answer(f"<b>ГЛАВНОЕ МЕНЮ</b>", reply_markup=kb, parse_mode="HTML")

# --- CALLBACKS ---
@dp_main.callback_query(F.data.endswith("_action") | (F.data == "menu_back"))
async def handle_actions(c: types.CallbackQuery):
    action = c.data.replace("_action", "")
    await c.answer()
    
    if action == "mine": await cmd_mine(c.message)
    elif action == "inv": await cmd_inventory(c.message)
    elif action == "sale": await cmd_sale(c.message)
    elif action == "shop": 
        p = get_player(c.from_user.id)
        kb = [[InlineKeyboardButton(text=f"{v['name']} — {v['price']:,} 💵", callback_data=f"buy_{k}")] for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]]
        await c.message.answer("🛒 <b>Магазин кирок:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    elif action == "bonus": 
        # Вызов функции через message, чтобы не дублировать код
        from aiogram.filters import CommandObject
        await cmd_bonus(c.message)
    elif action == "bal": 
        p = get_player(c.from_user.id)
        await c.answer(f"На балансе: {p['balance']:,} монет", show_alert=True)
    elif action == "menu_back":
        await cmd_menu(c.message)

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_h(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", (SHOP_PICKS[lvl]["price"], lvl, c.from_user.id), commit=True)
        await c.answer(f"✅ Куплено: {SHOP_PICKS[lvl]['name']}!", show_alert=True)
        await cmd_inventory(c.message)
    else: 
        await c.answer("❌ Денег не хватает!", show_alert=True)

# --- ПРОЧИЕ КОМАНДЫ (Бонус, Топ, Баланс) ---
@dp_main.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    p = db_query("SELECT last_bonus FROM players WHERE user_id = ?", (message.chat.id,), fetchone=True)
    last_bonus = p[0] if p else 0
    now = int(time.time())
    if now - last_bonus < 86400:
        rem = 86400 - (now - last_bonus)
        await message.answer(f"⏳ Рано! Приходи через {rem//3600}ч.")
        return
    gift = random.randint(1000, 5000)
    db_query("UPDATE players SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (gift, now, message.chat.id), commit=True)
    await message.answer(f"🎁 Бонус взят: <b>{gift}</b> монет!", parse_mode="HTML")

@dp_main.message(Command("balance"))
async def cmd_bal(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f"💳 Баланс: <b>{p['balance']:,}</b>", parse_mode="HTML")

async def main():
    init_db()
    await main_bot.set_my_commands([
        BotCommand(command="menu", description="📱 Главное меню"),
        BotCommand(command="mine", description="⛏ Копать"),
        BotCommand(command="inventory", description="🎒 Инвентарь"),
        BotCommand(command="shop", description="🛒 Магазин")
    ])
    print("Бот запущен!")
    await dp_main.start_polling(main_bot)

if __name__ == "__main__":
    asyncio.run(main())
