import asyncio
import random
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"
CHANNEL_ID = "@твой_канал"  # ЗАМЕНИ НА ID своего канала (например @my_channel)
ADMIN_USERNAME = "Ramilpopa_4" # Твой ник в ТГ

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

def get_user_data(user_id, username, name="Игрок"):
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "balance": 1000 if username == ADMIN_USERNAME else 250, 
            "exp": 0, 
            "level": 1, 
            "last_bonus": 0
        }
    return users[user_id]

# --- КЛАВИАТУРЫ ---
def main_menu_kb(username):
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🎰 Казино"), types.KeyboardButton(text="🎲 Кости"))
    builder.row(types.KeyboardButton(text="👤 Профиль"), types.KeyboardButton(text="🎁 Бонус"))
    
    # Если зашел Ramilpopa_4, добавляем ему кнопку админки
    if username == ADMIN_USERNAME:
        builder.row(types.KeyboardButton(text="⚙️ Админка"))
        
    return builder.as_markup(resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    u = get_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    welcome_text = f"🎮 Привет, {message.from_user.first_name}!"
    if message.from_user.username == ADMIN_USERNAME:
        welcome_text += "\n🌟 Добро пожаловать, Создатель!"
    
    await message.answer(welcome_text, reply_markup=main_menu_kb(message.from_user.username))

# ЛОГИКА ОТПРАВКИ В КАНАЛ
@dp.message(F.text & ~F.text.in_(["🎰 Казино", "🎲 Кости", "👤 Профиль", "🎁 Бонус", "⚙️ Админка"]))
async def ask_channel_post(message: types.Message):
    u = get_user_data(message.from_user.id, message.from_user.username)
    u['temp_msg'] = message.text # Запоминаем текст
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить в канал", callback_data="send_to_chan")
    builder.button(text="❌ Отмена", callback_data="cancel_post")
    
    await message.answer(f"Ты написал: \"{message.text}\"\nХочешь опубликовать это в канале?", 
                         reply_markup=builder.as_markup())

@dp.callback_query(F.data == "send_to_chan")
async def send_to_chan(callback: types.CallbackQuery):
    u = users.get(callback.from_user.id)
    if u and 'temp_msg' in u:
        try:
            await bot.send_message(CHANNEL_ID, f"📢 Сообщение от @{callback.from_user.username}:\n\n{u['temp_msg']}")
            await callback.answer("Успешно отправлено!", show_alert=True)
            await callback.message.edit_text("Ваш пост опубликован в канале!")
            u.pop('temp_msg')
        except Exception as e:
            await callback.answer("Ошибка! Проверь, что бот админ в канале.", show_alert=True)
    else:
        await callback.answer("Текст не найден.")

# ИГРЫ С УТЕШИТЕЛЬНЫМ ПРИЗОМ
@dp.message(F.text == "🎲 Кости")
async def dice(message: types.Message):
    u = get_user_data(message.from_user.id, message.from_user.username)
    if u['balance'] < 50: return await message.answer("Мало монет!")
    
    u['balance'] -= 50
    user_v = random.randint(1, 6)
    bot_v = random.randint(1, 6)
    
    if user_v > bot_v:
        u['balance'] += 120
        await message.answer(f"🎲 {user_v} vs {bot_v}: Победа! +120 монет.")
    elif user_v == bot_v:
        u['balance'] += 50
        await message.answer(f"🎲 {user_v} vs {bot_v}: Ничья. Возврат.")
    else:
        u['balance'] += 10 # Утешительный приз
        await message.answer(f"🎲 {user_v} vs {bot_v}: Проигрыш. Но держи +10 монет утешительно!")

@dp.message(F.text == "🎰 Казино")
async def casino(message: types.Message):
    u = get_user_data(message.from_user.id, message.from_user.username)
    if u['balance'] < 100: return await message.answer("Нужно 100 монет!")
    u['balance'] -= 100
    res = await message.answer_dice(emoji="🎰")
    await asyncio.sleep(4)
    if res.dice.value in [1, 22, 43, 64]:
        u['balance'] += 2000
        await message.answer("💰 ДЖЕКПОТ! +2000 монет!")
    else:
        u['balance'] += 15 # Утешительный приз
        await message.answer("Не повезло. Но держи +15 монет утешительно!")

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    u = get_user_data(message.from_user.id, message.from_user.username)
    await message.answer(f"👤 Игрок: @{u['username']}\n💰 Баланс: {u['balance']} монет")

@dp.message(F.text == "⚙️ Админка")
async def admin_panel(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.answer("У тебя нет прав!")
    await message.answer("👑 Панель управления создателя:\n1. Все системы работают.\n2. Твой баланс неограничен (почти).")

@dp.message(F.text == "🎁 Бонус")
async def bonus(message: types.Message):
    u = get_user_data(message.from_user.id, message.from_user.username)
    now = time.time()
    if now - u['last_bonus'] < 86400:
        await message.answer("Приходи завтра!")
    else:
        u['balance'] += 500
        u['last_bonus'] = now
        await message.answer("🎁 Получено 500 монет!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
