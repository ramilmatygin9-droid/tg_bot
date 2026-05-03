import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- НАСТРОЙКИ ---
TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"

# Настройка логирования, чтобы видеть всё в консоли PyCharm
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Простая база данных в памяти бота
users_data = {}

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="🎰 Играть в Слоты", callback_data="game_slots")],
        [InlineKeyboardButton(text="🖱 Кликер (Заработок)", callback_data="game_clicker")],
        [InlineKeyboardButton(text="🛠 Сообщить о баге", callback_data="report_bug")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="to_menu")]
    ])

# --- ОБРАБОТЧИКИ (ХЕНДЛЕРЫ) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0}
    
    await message.answer(
        f"🎮 **Phoenix Bot приветствует тебя!**\n\n"
        f"💰 Твой баланс: {users_data[user_id]['balance']} коинов\n"
        f"Выбери раздел ниже:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# Логика кликера
@dp.callback_query(F.data == "game_clicker")
async def game_clicker(callback: CallbackQuery):
    user_id = callback.from_user.id
    users_data[user_id]["balance"] += 1
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 КЛИК! (+1)", callback_data="game_clicker")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_menu")]
    ])
    
    try:
        await callback.message.edit_text(
            f"🖱 **КЛИКЕР**\n\nТвой счет: {users_data[user_id]['balance']} коинов",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception:
        pass  # Чтобы не вылетало, если нажать слишком быстро
    await callback.answer()

# Логика слотов
@dp.callback_query(F.data == "game_slots")
async def game_slots(callback: CallbackQuery):
    msg = await callback.message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)  # Ждем анимацию барабана
    
    user_id = callback.from_user.id
    # Значения джекпота в Telegram: 1, 22, 43, 64
    if msg.dice.value in [1, 22, 43, 64]:
        reward = 500
        users_data[user_id]["balance"] += reward
        await callback.message.answer(f"🔥 ВАУ! Тройной джекпот! +{reward} коинов!")
    else:
        await callback.message.answer("❌ Мимо! Попробуй еще раз.")
    
    await callback.answer()

# Логика баг-репортов
@dp.callback_query(F.data == "report_bug")
async def report_bug(callback: CallbackQuery):
    await callback.message.answer(
        "🛠 **Центр помощи**\n\nНапиши сообщение, начиная со слова БАГ.\n"
        "Пример: `БАГ Не работает кнопка кликера`",
        reply_markup=get_back_button()
    )
    await callback.answer()

@dp.message(F.text.startswith("БАГ"))
async def catch_bug(message: types.Message):
    # В консоли PyCharm мы увидим этот баг
    print(f"!!! НОВЫЙ БАГ: {message.text} от пользователя {message.from_user.id}")
    await message.reply("✅ Баг-репорт зафиксирован. Спасибо за помощь!")

# Возврат в меню
@dp.callback_query(F.data == "to_menu")
async def to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        f"🎮 **Главное меню**\n\n💰 Баланс: {users_data[user_id]['balance']} коинов",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    # Удаляем зависшие сообщения, чтобы бот ответил сразу
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 БОТ ЗАПУЩЕН! Напиши /start в Telegram.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
