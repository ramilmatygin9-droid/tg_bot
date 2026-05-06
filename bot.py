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
MAIN_TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"  # Основной игровой бот
ADMIN_TOKEN = "8692818015:AAFr1AppqwvoF4lrmebWnWSaDgpAX7VB5LA" # Бот-админка для промокодов
OWNER_ID = 8462392581  # Твой ID (Ramil) для управления промокодами

# Premium Emoji IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"    
SUPPORT_ID = "5924712865763170353"    
GIFT_ID = "5792071541084659564"       
SHOP_ICON_ID = "5197269100878907942"  
ERROR_EMOJI_ID = "5240241223632954241" # Эмодзи из image_10.png

# Инициализация ботов
main_bot = Bot(token=MAIN_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)

dp_main = Dispatcher()
dp_admin = Dispatcher()

# --- БАЗА ДАННЫХ ---
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
                         "• <code>/add КОД СУММА ЧАСЫ</code> (0 - навсегда)\n"
                         "• <code>/del КОД</code> - Удалить код\n"
                         "• <code>/list</code> - Список всех кодов", parse_mode="HTML")

@dp_admin.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        parts = message.text.split()
        code = parts[1].upper()
        reward = int(parts[2])
        hours = int(parts[3])
        expire = "NEVER" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db_query("INSERT OR REPLACE INTO promo_codes VALUES (?, ?, ?)", (code, reward, expire), commit=True)
        await message.answer(f"✅ Промокод <b>{code}</b> создан!\n💰 Награда: {reward}\n⏰ Истекает: {expire}", parse_mode="HTML")
    except: await message.answer("Ошибка! Формат: <code>/add START 5000 0</code>")

@dp_admin.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        code = message.text.split()[1].upper()
        db_query("DELETE FROM promo_codes WHERE code = ?", (code,), commit=True)
        await message.answer(f"🗑 Промокод <b>{code}</b> удален.")
    except: await message.answer("Ошибка! Формат: <code>/del КОД</code>")

@dp_admin.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    promos = db_query("SELECT * FROM promo_codes", fetchall=True)
    if not promos:
        await message.answer("Активных кодов нет.")
        return
    text = "🎫 <b>Активные промокоды:</b>\n"
    for p in promos:
        text += f"• <code>{p[0]}</code> — {p[1]} монет (До: {p[2]})\n"
    await message.answer(text, parse_mode="HTML")

# --- ЛОГИКА ОСНОВНОГО БОТА (ИГРА) ---

SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

@dp_main.message(Command("start"))
async def main_start(message: types.Message):
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать в Майнер бот</b><tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji>\n\n'
        f'Используй /mine или меню чтобы начать копать руду',
        parse_mode="HTML"
    )

@dp_main.message(Command("mine"))
async def main_mine(message: types.Message):
    p = get_player(message.from_user.id)
    wait_time = random.randint(5, 12)
    
    # Старый интерфейс текста
    status_msg = await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n'
        f'⏳ Осталось: <b>{wait_time}</b> сек.', 
        parse_mode="HTML"
    )
    
    for seconds_left in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(
                f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n'
                f'⏳ Осталось: <b>{seconds_left}</b> сек.',
                parse_mode="HTML"
            )
        except: pass
    
    multiplier = SHOP_PICKS.get(p["pick_lvl"], SHOP_PICKS[1])["mult"]
    reward = int(random.randint(200, 700) * multiplier)
    new_bal = p["balance"] + reward
    
    db_query("UPDATE players SET balance = ? WHERE user_id = ?", (new_bal, message.from_user.id), commit=True)
    await status_msg.delete()
    
    # Итоговое сообщение без множителя
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Успешная добыча!</b>\n'
        f'━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="{CASH_ID}">💵</tg-emoji> Найдено: <b>{reward}</b> монет\n'
        f'<tg-emoji emoji-id="{BALANCE_ID}">💰</tg-emoji> Баланс: <b>{new_bal}</b>',
        parse_mode="HTML"
    )

@dp_main.message(Command("bonus"))
async def bonus_cmd(message: types.Message):
    gift_amount = random.randint(10, 500)
    db_query("UPDATE players SET balance = balance + ? WHERE user_id = ?", (gift_amount, message.from_user.id), commit=True)
    
    text = (
        f'<tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji> <b>вам доступен подарок заберите</b> <tg-emoji emoji-id="{GIFT_ID}">🎁</tg-emoji>\n\n'
        f'Вы получили: <b>{gift_amount}</b> монет!\n'
        f'Заходи чаще, чтобы забирать бонусы.'
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="ЗАБРАТЬ ✅", callback_data="close_bonus")]])
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@dp_main.callback_query(F.data == "close_bonus")
async def close_bonus_cb(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Монеты зачислены!")

@dp_main.message(Command("shop"))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    current_pick = SHOP_PICKS.get(p["pick_lvl"], SHOP_PICKS[1])["name"]
    
    text = (
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>покупай кирки и получай больше всех</b>\n\n'
        f'Также у нас есть промокоды <tg-emoji emoji-id="{SHOP_ICON_ID}">📋</tg-emoji>\n'
        f'━━━━━━━━━━━━━━\n'
        f'Твоя кирка: <b>{current_pick}</b>\n'
        f'Выбери инструмент для улучшения:'
    )
    
    keyboard = []
    for lvl, info in SHOP_PICKS.items():
        if lvl > p["pick_lvl"]:
            keyboard.append([InlineKeyboardButton(text=f"{info['name']} — {info['price']} 💵", callback_data=f"buy_{lvl}")])
    
    keyboard.append([InlineKeyboardButton(text="🎫 Ввести промокод", callback_data="open_promo")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

@dp_main.callback_query(F.data == "open_promo")
async def open_promo_cb(callback: types.CallbackQuery):
    await callback.message.answer(f'<tg-emoji emoji-id="{SHOP_ICON_ID}">📝</tg-emoji> <b>Введите промокод в чат ответным сообщением:</b>', parse_mode="HTML")
    await callback.answer()

@dp_main.callback_query(F.data.startswith("buy_"))
async def buy_cb(callback: types.CallbackQuery):
    lvl = int(callback.data.split("_")[1])
    p = get_player(callback.from_user.id)
    pick = SHOP_PICKS[lvl]
    
    if p["balance"] >= pick["price"]:
        db_query("UPDATE players SET balance = balance - ?, pick_lvl = ? WHERE user_id = ?", 
                 (pick["price"], lvl, callback.from_user.id), commit=True)
        await callback.message.edit_text(f'✅ <b>Успешная покупка!</b>\nВы приобрели: <b>{pick["name"]}</b>', parse_mode="HTML")
    else:
        await callback.answer("Недостаточно монет!", show_alert=True)

@dp_main.message(Command("promo"))
async def main_promo_cmd(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{SHOP_ICON_ID}">📝</tg-emoji> <b>Введите промокод в чат:</b>', parse_mode="HTML")

@dp_main.message(Command("balance"))
async def balance_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> <b>Ваш баланс:</b>\n💰 <b>{p["balance"]}</b> монет', parse_mode="HTML")

@dp_main.message(Command("support"))
async def support_cmd(message: types.Message):
    await message.answer(f'<tg-emoji emoji-id="{SUPPORT_ID}">🎧</tg-emoji> <b>Техническая поддержка</b>\n\nПиши админу:\n👉 @Ramilpopa_4', parse_mode="HTML")

@dp_main.message(F.text)
async def handle_promos(message: types.Message):
    if message.text.startswith('/'): return
    
    code = message.text.upper().strip()
    promo = db_query("SELECT reward, expire_at FROM promo_codes WHERE code = ?", (code,), fetchone=True)
    
    if promo:
        reward, expire = promo
        p = get_player(message.from_user.id)
        
        # Проверка срока действия
        is_expired = False
        if expire != "NEVER":
            if datetime.now() > datetime.strptime(expire, "%Y-%m-%d %H:%M:%S"):
                is_expired = True

        if is_expired:
            await message.reply(
                f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует или срок действия истек <tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji>',
                parse_mode="HTML"
            ) # Текст и эмодзи из image_11.png/image_12.png
        elif code in p["used_promos"]:
            await message.reply("❌ Вы уже использовали этот промокод!")
        else:
            # Успешная активация
            p["used_promos"].append(code)
            db_query("UPDATE players SET balance = balance + ?, used_promos = ? WHERE user_id = ?", 
                     (reward, ",".join(p["used_promos"]), message.from_user.id), commit=True)
            await message.reply(f"✅ <b>Активировано!</b>\nВы получили <b>{reward}</b> монет!", parse_mode="HTML")
    else:
        # Если промокод не найден в базе
        await message.reply(
            f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> Промокод не существует или срок действия истек <tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji>',
            parse_mode="HTML"
        ) # Текст и эмодзи из image_11.png/image_12.png

# --- ЗАПУСК ---
async def main():
    init_db()
    # Меню для основного бота
    await main_bot.set_my_commands([
        BotCommand(command="/start", description="🏠 Главное меню"),
        BotCommand(command="/mine", description="⛏ Копать руду"),
        BotCommand(command="/bonus", description="🎁 Забрать подарок"),
        BotCommand(command="/shop", description="🛒 Магазин"),
        BotCommand(command="/promo", description="🎫 Промокод"),
        BotCommand(command="/balance", description="💰 Баланс"),
        BotCommand(command="/support", description="🎧 Поддержка")
    ], scope=BotCommandScopeDefault())
    
    print("Боты запущены!")
    await asyncio.gather(dp_main.start_polling(main_bot), dp_admin.start_polling(admin_bot))

if __name__ == "__main__":
    asyncio.run(main())
