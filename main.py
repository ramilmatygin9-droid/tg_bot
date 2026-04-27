import asyncio
import json
import os
import time
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8693763218:AAGoc7Y2xTFZeXsaZ_mzksRkFUhOnA3Zj10" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "game_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

def get_profile(user_id, name="Игрок"):
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "name": name,
            "balance": 0,
            "click_power": 1,
            "lvl": 1,
            "exp": 0,
            "last_bonus": 0
        }
    else:
        db[uid]["name"] = name # Обновляем имя, если сменил в ТГ
    return db[uid]

# --- Клавиатуры ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛏ Работать"), KeyboardButton(text="🎰 Казино")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🏆 ТОП-10"), KeyboardButton(text="🎁 Бонус")]
    ],
    resize_keyboard=True
)

# --- Обработчики ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    get_profile(message.from_user.id, message.from_user.first_name)
    save_data(db)
    await message.answer("💎 **Добро пожаловать в элиту Clicker Tycoon!**\n\nПробивайся в топ и стань легендой.", 
                         reply_markup=main_kb, parse_mode="Markdown")

# 1. Механика работы (Клик)
@dp.message(F.text == "⛏ Работать")
async def work(message: types.Message):
    p = get_profile(message.from_user.id, message.from_user.first_name)
    reward = p["click_power"] * (5 if random.random() < 0.1 else 1)
    p["balance"] += reward
    p["exp"] += 1
    if p["exp"] >= p["lvl"] * 50:
        p["lvl"] += 1
        await message.answer(f"⭐ **Уровень UP!** Твой уровень теперь: {p['lvl']}")
    save_data(db)
    await message.answer(f"Заработано: **{reward} 💰**", parse_mode="Markdown")

# 2. Мини-игра Казино (Слоты)
@dp.message(F.text == "🎰 Казино")
async def casino(message: types.Message):
    p = get_profile(message.from_user.id, message.from_user.first_name)
    if p["balance"] < 100:
        return await message.answer("❌ Ставка в казино — 100 💰. У тебя маловато!")

    p["balance"] -= 100
    # Отправляем кубик-казино (автоматическая анимация ТГ)
    msg = await message.answer_dice(emoji="🎰")
    
    # В эмодзи 🎰 значения: 1, 22, 43, 64 — это выигрышные комбинации
    # Но проще проверить значение msg.dice.value (от 1 до 64)
    # Выигрышные в 🎰: 1 (три бара), 22 (три вишни), 43 (три лимона), 64 (три семерки)
    await asyncio.sleep(4)
    
    if msg.dice.value in [1, 22, 43]:
        win = 1000
        p["balance"] += win
        await message.answer(f"💸 **ВЫИГРЫШ!** Ты поднял {win} 💰!")
    elif msg.dice.value == 64:
        win = 5000
        p["balance"] += win
        await message.answer(f"🔥 **ДЖЕКПОТ!** Ты выиграл {win} 💰!")
    else:
        await message.answer("😢 Не повезло. Попробуй еще раз!")
    save_data(db)

# 3. Глобальный ТОП игроков
@dp.message(F.text == "🏆 ТОП-10")
async def show_top(message: types.Message):
    # Сортируем всех пользователей по балансу (от большего к меньшему)
    sorted_users = sorted(db.items(), key=lambda x: x[1]['balance'], reverse=True)
    top_list = "🏆 **ТОП-10 БОГАТЕЕВ:**\n\n"
    
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        top_list += f"{i}. {data['name']} — {data['balance']} 💰 (Lvl {data['lvl']})\n"
    
    await message.answer(top_list, parse_mode="Markdown")

# 4. Система Промокодов (команда /promo)
@dp.message(Command("promo"))
async def use_promo(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Введи: `/promo ТВОЙ_КОД`", parse_mode="Markdown")
    
    promo = args[1].lower()
    p = get_profile(message.from_user.id, message.from_user.first_name)
    
    if promo == "carrot": # Пример кода
        p["balance"] += 1000
        save_data(db)
        await message.answer("🎁 Код активирован! +1000 💰")
    else:
        await message.answer("❌ Неверный или просроченный код.")

# Остальные функции (Профиль, Магазин, Бонус) можно оставить из прошлого примера...

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
