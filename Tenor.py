import asyncio
import random
import sqlite3
from datetime import datetime
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ------------------- КОНФИГ -------------------
TOKEN = "8156857401:AAGxshuoGT-sV6hgMfpnFmQAHF7BsAjINjk"  # Замените на токен вашего бота
SPIN_COST = 10
# 25 секторов (как в рулетке)
SEGMENTS = []

def add_currency(amount):
    SEGMENTS.append(('currency', amount, f'+{amount}💰'))

def add_loss(amount):
    SEGMENTS.append(('loss', amount, f'{amount}💔'))

def add_empty():
    SEGMENTS.append(('empty', 0, '🚫 пусто'))

def add_case(rarity, disp, low, high):
    SEGMENTS.append(('case', (rarity, low, high), disp))

# Формирование 25 секторов (соответствует сайту)
add_currency(8); add_currency(12); add_currency(18); add_currency(25); add_currency(40); add_currency(60)
add_loss(-15); add_loss(-15); add_loss(-25); add_loss(-30)
add_empty(); add_empty(); add_empty()
for _ in range(4):
    add_case('common', '📦 обычный кейс', 8, 35)
for _ in range(3):
    add_case('legendary', '✨ легендарный кейс', 70, 160)
for _ in range(3):
    add_case('mythic', '🌀 мифический кейс', 200, 500)
for _ in range(2):
    add_case('mega', '💎 МЕГА кейс', 800, 2200)

assert len(SEGMENTS) == 25, "Не 25 секторов!"

# ---------- БАЗА ДАННЫХ (SQLite) ----------
def init_db():
    conn = sqlite3.connect('game_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  balance INTEGER DEFAULT 2500,
                  cases TEXT DEFAULT '[]',
                  last_spin TEXT)''')
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect('game_bot.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 2500))
        conn.commit()
        balance = 2500
    else:
        balance = row[0]
    conn.close()
    return balance

def set_user_balance(user_id, new_balance):
    conn = sqlite3.connect('game_bot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
    conn.commit()
    conn.close()

def add_cases_to_inventory(user_id, case_type, count=1):
    # Здесь можно реализовать инвентарь кейсов, но для простоты сразу открываем
    pass

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_spin_result():
    """Возвращает индекс сектора, тип и данные"""
    idx = random.randrange(25)
    seg = SEGMENTS[idx]
    return idx, seg

def process_prize(seg):
    """Обрабатывает приз, возвращает изменение баланса и описание"""
    if seg[0] == 'currency':
        return seg[1], f"💵 Выигрыш {seg[2]}"
    elif seg[0] == 'loss':
        return seg[1], f"💔 Проигрыш {seg[2]}"
    elif seg[0] == 'empty':
        return 0, f"🍃 {seg[2]}"
    elif seg[0] == 'case':
        rarity, low, high = seg[1]
        reward = random.randint(low, high)
        return reward, f"🎁 {seg[2]} открыт! +{reward}💰"
    return 0, "Ошибка"

# ---------- КОМАНДЫ БОТА ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(
        f"🎲 *Добро пожаловать в Мега Рулетку!*\n\n"
        f"💰 Твой баланс: *{balance}* монет\n"
        f"🎡 Спин стоит *{SPIN_COST}* монет\n\n"
        f"Используй команды:\n"
        f"/spin — крутить рулетку (25 слотов)\n"
        f"/balance — баланс\n"
        f"/help — помощь\n\n"
        f"✨ При выпадении кейса он открывается автоматически!",
        parse_mode="Markdown"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_user_balance(user_id)
    await update.message.reply_text(f"💰 Твой текущий баланс: *{bal}* монет", parse_mode="Markdown")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_user_balance(user_id)
    if bal < SPIN_COST:
        await update.message.reply_text(f"❌ Недостаточно монет! Нужно {SPIN_COST}, у тебя {bal}.\nПополнить можно через /start или выигрышем.")
        return

    # Списываем стоимость
    new_bal = bal - SPIN_COST
    set_user_balance(user_id, new_bal)

    # Анимация "кручения" (текстовая)
    msg = await update.message.reply_text("🎡 *Рулетка крутится...* 🎡\n▰▰▰▰▰▰▰▰▰▰ 0%", parse_mode="Markdown")
    for i in range(1, 6):
        await asyncio.sleep(0.4)
        percent = i * 20
        bar = "▰" * (percent // 10) + "▱" * (10 - percent // 10)
        await msg.edit_text(f"🎡 *Рулетка крутится...* 🎡\n{bar} {percent}%")
    await asyncio.sleep(0.3)

    # Получаем результат
    idx, seg = get_spin_result()
    delta, desc = process_prize(seg)
    final_bal = new_bal + delta
    set_user_balance(user_id, final_bal)

    # Формируем сообщение с сектором
    sector_name = seg[2] if seg[0] != 'case' else seg[2]
    result_text = (
        f"🎲 *Результат вращения:*\n"
        f"➡️ Выпал сектор: *{sector_name}*\n"
        f"{desc}\n\n"
        f"💰 *Баланс:* {new_bal} → {final_bal} монет"
    )
    await msg.edit_text(result_text, parse_mode="Markdown")

    # Если выпал кейс - дополнительный эффект
    if seg[0] == 'case':
        await update.message.reply_text(f"✨✨ *КЕЙС ОТКРЫТ!* ✨✨\n+{delta} монет добавлено на счёт!", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 *Игровой бот «Мега Рулетка»*\n\n"
        "/start — начать игру\n"
        "/spin — крутить рулетку (стоимость 10 монет)\n"
        "/balance — показать баланс\n"
        "/help — эта справка\n\n"
        "*Сектора рулетки:*\n"
        "💰 Валюта (+8, +12, +18, +25, +40, +60)\n"
        "💔 Проигрыш (-15, -15, -25, -30)\n"
        "🍃 Пусто (0)\n"
        "📦 Обычный кейс (+8..35)\n"
        "✨ Легендарный (+70..160)\n"
        "🌀 Мифический (+200..500)\n"
        "💎 МЕГА кейс (+800..2200)\n\n"
        "Удачи в игре!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Используй /help для списка команд.")

# ---------- ЗАПУСК ----------
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
