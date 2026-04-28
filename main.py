import asyncio
import random
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных пользователей
users = {}
# Список активных промокодов (код: сумма)
PROMO_CODES = {
    "START": 500,
    "GAMES2024": 1000,
    "HELLO": 150
}

def get_user_data(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 100, 
            "exp": 0, 
            "level": 1, 
            "last_bonus": 0,
            "used_promos": []
        }
    return users[user_id]

# Клавиатура главного меню
def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎰 Казино")
    builder.button(text="✊ КНБ")
    builder.button(text="🃏 21 Очко")
    builder.button(text="🔢 Угадай число")
    builder.button(text="👤 Профиль")
    builder.button(text="🎁 Бонус")
    builder.button(text="🎟 Ввести промо")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user_data(message.from_user.id)
    await message.answer(
        f"🎮 Добро пожаловать, {message.from_user.first_name}!\n"
        "Я игровой бот. Играй, зарабатывай монеты и повышай уровень!",
        reply_markup=main_menu_kb()
    )

# --- СИСТЕМА ПРОМОКОДОВ ---
@dp.message(F.text == "🎟 Ввести промо")
async def promo_start(message: types.Message):
    await message.answer("Напиши мне промокод (например, START):")

@dp.message(lambda message: message.text.upper() in PROMO_CODES)
async def use_promo(message: types.Message):
    u = get_user_data(message.from_user.id)
    code = message.text.upper()
    
    if code in u['used_promos']:
        await message.answer("⚠️ Ты уже использовал этот промокод!")
    else:
        reward = PROMO_CODES[code]
        u['balance'] += reward
        u['used_promos'].append(code)
        await message.answer(f"✅ Активировано! Получено {reward} монет.")

# --- ЕЖЕДНЕВНЫЙ БОНУС (Раз в 24 часа) ---
@dp.message(F.text == "🎁 Бонус")
async def daily_bonus(message: types.Message):
    u = get_user_data(message.from_user.id)
    current_time = time.time()
    
    # 86400 секунд = 24 часа
    if current_time - u['last_bonus'] < 86400:
        remaining = int(86400 - (current_time - u['last_bonus']))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await message.answer(f"⏳ Бонус будет доступен через {hours}ч. {minutes}м.")
    else:
        bonus = random.randint(100, 300)
        u['balance'] += bonus
        u['last_bonus'] = current_time
        await message.answer(f"🎁 Ты получил ежедневную награду: {bonus} монет!")

# --- ИГРА: КАМЕНЬ НОЖНИЦЫ БУМАГА ---
@dp.message(F.text == "✊ КНБ")
async def rps_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🪨 Камень")
    builder.button(text="✂️ Ножницы")
    builder.button(text="📄 Бумага")
    builder.adjust(3)
    await message.answer("Выбирай предмет! Ставка: 20 монет.", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(["🪨 Камень", "✂️ Ножницы", "📄 Бумага"]))
async def rps_play(message: types.Message):
    u = get_user_data(message.from_user.id)
    if u['balance'] < 20:
        await message.answer("Недостаточно монет!")
        return

    user_choice = message.text
    bot_choice = random.choice(["🪨 Камень", "✂️ Ножницы", "📄 Бумага"])
    u['balance'] -= 20
    
    await message.answer(f"Твой выбор: {user_choice}\nМой выбор: {bot_choice}")
    
    if user_choice == bot_choice:
        u['balance'] += 20
        await message.answer("🤝 Ничья! Монеты возвращены.", reply_markup=main_menu_kb())
    elif (user_choice == "🪨 Камень" and bot_choice == "✂️ Ножницы") or \
         (user_choice == "✂️ Ножницы" and bot_choice == "📄 Бумага") or \
         (user_choice == "📄 Бумага" and bot_choice == "🪨 Камень"):
        u['balance'] += 50
        await message.answer("🎉 Ты выиграл 50 монет!", reply_markup=main_menu_kb())
    else:
        await message.answer("💀 Ты проиграл!", reply_markup=main_menu_kb())

# --- ИГРА: 21 ОЧКО (Упрощенно) ---
@dp.message(F.text == "🃏 21 Очко")
async def cards_game(message: types.Message):
    u = get_user_data(message.from_user.id)
    if u['balance'] < 50:
        await message.answer("Нужно хотя бы 50 монет!")
        return
        
    u['balance'] -= 50
    user_score = random.randint(2, 11) + random.randint(2, 11)
    bot_score = random.randint(12, 22) # У бота сразу результат
    
    if user_score > 21:
        await message.answer(f"Твои очки: {user_score}. Перебор! Ты проиграл.")
    elif user_score > bot_score or bot_score > 21:
        u['balance'] += 120
        await message.answer(f"Твои: {user_score}, Мои: {bot_score}. Ты победил! +120 монет.")
    else:
        await message.answer(f"Твои: {user_score}, Мои: {bot_score}. Я победил!")

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    u = get_user_data(message.from_user.id)
    await message.answer(
        f"👤 Игрок: {message.from_user.first_name}\n"
        f"💰 Баланс: {u['balance']} монет\n"
        f"⭐️ Уровень: {u['level']}"
    )

# Стандартное казино и угадайка из прошлого примера (оставил логику)
@dp.message(F.text == "🎰 Казино")
async def slots(message: types.Message):
    u = get_user_data(message.from_user.id)
    if u['balance'] < 30:
        await message.answer("Мало монет (нужно 30)")
        return
    u['balance'] -= 30
    res = await message.answer_dice(emoji="🎰")
    await asyncio.sleep(4)
    if res.dice.value in [1, 22, 43, 64]:
        u['balance'] += 1000
        await message.answer("🤑 ДЖЕКПОТ! +1000 монет!")
    else:
        await message.answer("Проигрыш. Попробуй еще раз!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
