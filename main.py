import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ВАЖНО: Используй НОВЫЙ токен, который получишь после Revoke в BotFather
TOKEN = "8693763218:AAGoc7Y2xTFZeXsaZ_mzksRkFUhOnA3Zj10"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "users.json"

# --- Логика базы данных ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

users = load_data()

def get_user_profile(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "click_power": 1,
            "level": 1,
            "exp": 0
        }
    return users[uid]

# --- Клавиатура ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Клик!")],
        [KeyboardButton(text="🔝 Улучшить (100 💰)"), KeyboardButton(text="📊 Профиль")]
    ],
    resize_keyboard=True
)

# --- Обработчики ---

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user_profile(message.from_user.id)
    save_data(users)
    await message.answer(
        "Добро пожаловать в кликер! Нажимай на кнопку, чтобы зарабатывать монеты и прокачивать уровень.",
        reply_markup=main_menu
    )

@dp.message(F.text == "⚡ Клик!")
async def click(message: types.Message):
    profile = get_user_profile(message.from_user.id)
    
    # Добавляем монеты и опыт
    reward = profile["click_power"]
    profile["balance"] += reward
    profile["exp"] += 1
    
    # Проверка на новый уровень (каждые 50 опыта)
    if profile["exp"] >= profile["level"] * 50:
        profile["level"] += 1
        await message.answer(f"🎉 Уровень повышен! Теперь твой уровень: {profile['level']}")

    save_data(users)
    await message.answer(f"Ты кликнул и получил {reward} 💰!")

@dp.message(F.text == "📊 Профиль")
async def profile_info(message: types.Message):
    p = get_user_profile(message.from_user.id)
    text = (
        f"👤 Игрок: {message.from_user.first_name}\n"
        f"⭐ Уровень: {p['level']}\n"
        f"💰 Баланс: {p['balance']}\n"
        f"💪 Сила клика: {p['click_power']}\n"
        f"📖 Опыт: {p['exp']}/{p['level'] * 50}"
    )
    await message.answer(text)

@dp.message(F.text.contains("Улучшить"))
async def upgrade(message: types.Message):
    p = get_user_profile(message.from_user.id)
    cost = 100 * p["click_power"] # Цена растет с каждым уровнем
    
    if p["balance"] >= cost:
        p["balance"] -= cost
        p["click_power"] += 1
        save_data(users)
        await message.answer(f"✅ Улучшение куплено! Теперь сила клика: {p['click_power']}\nСписано: {cost} 💰")
    else:
        await message.answer(f"❌ Недостаточно монет! Нужно еще {cost - p['balance']} 💰")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
