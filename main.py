import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ ---
TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"
ADMIN_ID = 0  # УЗНАЙ СВОЙ ID ЧЕРЕЗ @userinfobot И ВПИШИ СЮДА

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Глобальные настройки бота (можно менять из чата)
bot_settings = {
    "welcome_text": "👑 Добро пожаловать в Phoenix Ultra!",
    "reward_amount": 1,
    "bonus_min": 50,
    "bonus_max": 200
}

# Состояния для изменения настроек
class SetupState(StatesGroup):
    waiting_for_welcome = State()
    waiting_for_reward = State()

# --- КЛАВИАТУРЫ ---
def main_menu_kb(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎮 Игры", callback_data="menu_games")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="get_bonus")],
        [InlineKeyboardButton(text="🛠 Сообщить о баге", callback_data="report_bug")]
    ]
    # Если ты админ, добавляем кнопку настроек
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        bot_settings["welcome_text"],
        reply_markup=main_menu_kb(message.from_user.id)
    )

# --- АДМИНКА ---
@dp.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Доступ запрещен!")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить приветствие", callback_data="set_welcome")],
        [InlineKeyboardButton(text="💰 Награда за клик", callback_data="set_reward")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ])
    
    status = (f"⚙️ **НАСТРОЙКИ БОТА**\n\n"
              f"Приветствие: `{bot_settings['welcome_text']}`\n"
              f"Награда за клик: `{bot_settings['reward_amount']}`")
    
    await callback.message.edit_text(status, reply_markup=kb, parse_mode="Markdown")

# Процесс смены приветствия
@dp.callback_query(F.data == "set_welcome")
async def set_welcome_step1(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Пришли новый текст приветствия:")
    await state.set_state(SetupState.waiting_for_welcome)
    await callback.answer()

@dp.message(SetupState.waiting_for_welcome)
async def set_welcome_step2(message: types.Message, state: FSMContext):
    bot_settings["welcome_text"] = message.text
    await message.answer(f"✅ Приветствие изменено на:\n_{message.text}_", parse_mode="Markdown")
    await state.clear()

# Процесс смены награды
@dp.callback_query(F.data == "set_reward")
async def set_reward_step1(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи число (сколько давать за 1 клик):")
    await state.set_state(SetupState.waiting_for_reward)
    await callback.answer()

@dp.message(SetupState.waiting_for_reward)
async def set_reward_step2(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        bot_settings["reward_amount"] = int(message.text)
        await message.answer(f"✅ Теперь за клик дают: {message.text}")
        await state.clear()
    else:
        await message.answer("Ошибка! Введи только число.")

# --- ОБЩИЕ ФУНКЦИИ ---
@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        bot_settings["welcome_text"],
        reply_markup=main_menu_kb(callback.from_user.id)
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот с онлайн-настройками запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
