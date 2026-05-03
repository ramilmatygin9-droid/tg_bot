import asyncio
import logging
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- НАСТРОЙКИ ---
TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"
ADMIN_ID = 0  # Впиши сюда свой ID (узнай его через @userinfobot), чтобы иметь доступ к админке

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Расширенная база данных
users_data = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "balance": 100,
            "clicks": 0,
            "last_bonus": None,
            "items": [],
            "luck_boost": 1.0
        }
    return users_data[user_id]

# --- КЛАВИАТУРЫ ---
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Игры", callback_data="menu_games"), 
         InlineKeyboardButton(text="💎 Магазин", callback_data="menu_shop")],
        [InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="get_bonus")],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="menu_profile")],
        [InlineKeyboardButton(text="🛠 Сообщить о баге", callback_data="report_bug")]
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]])

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"👑 **Добро пожаловать в Phoenix Ultra!**\n\n"
        f"💰 Баланс: `{user['balance']}` 💎\n"
        f"Здесь ты можешь играть, копить бонусы и помогать нам фиксить баги.",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# Ежедневный бонус
@dp.callback_query(F.data == "get_bonus")
async def daily_bonus(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    now = datetime.now()
    
    if user["last_bonus"] and now < user["last_bonus"] + timedelta(days=1):
        wait_time = (user["last_bonus"] + timedelta(days=1)) - now
        hours = wait_time.seconds // 3600
        await callback.answer(f"⏳ Приходи через {hours} ч.", show_alert=True)
    else:
        reward = random.randint(50, 200)
        user["balance"] += reward
        user["last_bonus"] = now
        await callback.message.answer(f"🎁 Ты получил ежедневную награду: {reward} коинов!")
        await callback.answer()

# Профиль
@dp.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = (
        f"👤 **Твой профиль**\n\n"
        f"💰 Баланс: `{user['balance']}`\n"
        f"🖱 Всего кликов: `{user['clicks']}`\n"
        f"🍀 Коэффициент удачи: `x{user['luck_boost']}`\n"
    )
    await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode="Markdown")

# Магазин
@dp.callback_query(F.data == "menu_shop")
async def show_shop(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍀 Клевер удачи (500 💎)", callback_data="buy_luck")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("🛒 **Магазин предметов**\n\nКупи клевер, чтобы повысить шанс выигрыша в слотах!", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "buy_luck")
async def buy_luck(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["balance"] >= 500:
        user["balance"] -= 500
        user["luck_boost"] += 0.2
        await callback.answer("✅ Куплено! Твоя удача выросла.", show_alert=True)
    else:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)

# Меню игр
@dp.callback_query(F.data == "menu_games")
async def show_games(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="play_slots"),
         InlineKeyboardButton(text="🖱 Кликер", callback_data="play_clicker")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("🎮 **Выбери игру**", reply_markup=kb, parse_mode="Markdown")

# Логика слотов (с учетом удачи)
@dp.callback_query(F.data == "play_slots")
async def play_slots(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["balance"] < 10:
        return await callback.answer("Нужно хотя бы 10 коинов для ставки!", show_alert=True)
    
    user["balance"] -= 10
    msg = await callback.message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)
    
    # Шанс выигрыша увеличивается от luck_boost
    win_list = [1, 22, 43, 64]
    if msg.dice.value in win_list or (random.random() < (user["luck_boost"] - 1)):
        reward = 300
        user["balance"] += reward
        await callback.message.answer(f"🎉 Победа! Ты выиграл {reward} коинов!")
    else:
        await callback.message.answer("💨 Мимо. Баланс -10.")
    await callback.answer()

# Админка
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total_users = len(users_data)
        await message.answer(f"⚙️ **Админ-панель**\n\nВсего пользователей: {total_users}\nСервер: Стабилен")
    else:
        await message.answer("🛑 У тебя нет прав доступа.")

# Баг-репорты
@dp.message(F.text.startswith("БАГ"))
async def handle_bug(message: types.Message):
    print(f"REPORT: {message.text} FROM {message.from_user.id}")
    await message.reply("🐞 Спасибо за репорт! Мы передали его разработчикам.")

@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"👑 **Phoenix Ultra!**\n\n💰 Баланс: `{user['balance']}` 💎",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Phoenix Ultra запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
