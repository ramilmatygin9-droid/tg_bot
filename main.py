import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'game': None, 'name': name}
    return user_db[uid]

def get_main_menu(uid):
    u = get_user(uid)
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {u['bal']} m₽\n💸 **Ставка:** {u['bet']} m₽\n\n👇 *Выбери игру и начинай!*"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["⚽", "🏀", "🎯", "🎳", "🎲", "🎰"]],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="tab_cases"), InlineKeyboardButton(text="Режимы 💣", callback_data="mines_settings")],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- ОБРАБОТЧИК ДЛЯ ВСЕХ СООБЩЕНИЙ (если /start не нажали) ---
@dp.message()
async def all_messages_handler(message: types.Message):
    # Если пользователь зашел впервые и просто что-то написал
    uid = message.from_user.id
    name = message.from_user.first_name
    get_user(uid, name) # Регистрируем
    
    text, kb = get_main_menu(uid)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- ПОДМЕНЮ ИГР ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_submenu(callback: types.CallbackQuery):
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id)
    text = f"👤 **{u['name']}**\n{emoji} **Игра: {emoji}**\n...\n💸 **Ставка:** {u['bet']} m₽"
    
    # (Здесь остаются все ряды кнопок для футбола, баскетбола и т.д., как в прошлом коде)
    # Для краткости примера добавлю только кнопку назад
    rows = [[InlineKeyboardButton(text="⬅️ назад", callback_data="to_main")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@dp.callback_query(F.data == "to_main")
async def to_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

async def main():
    print("Бот запущен! Он ответит на любое сообщение.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
