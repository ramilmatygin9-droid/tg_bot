import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Твой токен
TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных в памяти (после перезагрузки обнулится)
# В реальном проекте лучше использовать SQLite
users = {}

def get_user_data(user_id):
    if user_id not in users:
        users[user_id] = {"balance": 100, "exp": 0, "level": 1}
    return users[user_id]

# Главное меню
def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎰 Испытать удачу")
    builder.button(text="🔢 Угадай число")
    builder.button(text="👤 Мой профиль")
    builder.button(text="🎁 Ежедневный бонус")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    user = get_user_data(message.from_user.id)
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Добро пожаловать в игровой бот. У тебя на счету 100 монет.\n"
        "Выбирай игру и развлекайся!",
        reply_markup=main_menu_kb()
    )

@dp.message(F.text == "👤 Мой профиль")
async def profile(message: types.Message):
    u = get_user_data(message.from_user.id)
    await message.answer(
        f"📋 **Ваш профиль:**\n"
        f"💰 Баланс: {u['balance']} монет\n"
        f"📈 Уровень: {u['level']}\n"
        f"✨ Опыт: {u['exp']}/100"
    )

@dp.message(F.text == "🎰 Испытать удачу")
async def play_slots(message: types.Message):
    u = get_user_data(message.from_user.id)
    if u['balance'] < 10:
        await message.answer("У тебя недостаточно монет! (Нужно хотя бы 10)")
        return

    u['balance'] -= 10
    msg = await message.answer_dice(emoji="🎰")
    
    # Значения выигрыша в Telegram Slots: 1, 22, 43, 64 - это джекпоты
    # Но мы сделаем проще: если выпало что-то крутое, даем приз
    await asyncio.sleep(4) # Ждем анимацию
    
    if msg.dice.value in [1, 22, 43, 64]:
        win = 500
        u['balance'] += win
        await message.answer(f"JACKPOT! 😱 Ты выиграл {win} монет!")
    elif msg.dice.value in [16, 32, 48]:
        win = 50
        u['balance'] += win
        await message.answer(f"Победа! 🎉 Ты выиграл {win} монет!")
    else:
        await message.answer("Эх, в этот раз не повезло. Попробуй еще!")

@dp.message(F.text == "🔢 Угадай число")
async def guess_game(message: types.Message):
    u = get_user_data(message.from_user.id)
    number = random.randint(1, 5)
    u['temp_num'] = number
    
    builder = ReplyKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"Кнопка {i}")
    builder.adjust(3)
    
    await message.answer("Я загадал число от 1 до 5. Угадаешь?", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.startswith("Кнопка "))
async def check_guess(message: types.Message):
    u = get_user_data(message.from_user.id)
    if 'temp_num' not in u:
        await message.answer("Начни игру заново.", reply_markup=main_menu_kb())
        return

    guess = int(message.text.split()[1])
    if guess == u['temp_num']:
        u['balance'] += 30
        u['exp'] += 20
        await message.answer(f"Верно! 🎉 +30 монет и +20 опыта.", reply_markup=main_menu_kb())
    else:
        await message.answer(f"Не угадал! Это было число {u['temp_num']}.", reply_markup=main_menu_kb())
    
    del u['temp_num']
    
    # Проверка уровня
    if u['exp'] >= 100:
        u['level'] += 1
        u['exp'] = 0
        await message.answer(f"🆙 Поздравляем! Ты достиг {u['level']} уровня!")

@dp.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus(message: types.Message):
    u = get_user_data(message.from_user.id)
    bonus = random.randint(20, 100)
    u['balance'] += bonus
    await message.answer(f"Ты получил ежедневный бонус: {bonus} монет! 💸")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
