import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- МЕНЮ ВЫБОРА ИСХОДА ---
def get_basketball_bet():
    kb = [
        [InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="bet_goal")],
        [InlineKeyboardButton(text="🏀 Мимо - x1.6", callback_data="bet_miss")],
        [InlineKeyboardButton(text="⬅️ назад", callback_data="to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ГЛАВНОЕ МЕНЮ (из видео) ---
def get_main_menu():
    # ... (тут те же кнопки, что мы делали раньше)
    kb = [
        [InlineKeyboardButton(text="🏀", callback_data="game_basketball"), 
         InlineKeyboardButton(text="⚽", callback_data="game_football"),
         InlineKeyboardButton(text="🎯", callback_data="game_darts"),
         InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
         InlineKeyboardButton(text="🎲", callback_data="game_dice"),
         InlineKeyboardButton(text="🎰", callback_data="game_slots")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"), 
         InlineKeyboardButton(text="Режимы 💣", callback_data="modes")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# 1. Нажали на иконку мяча
@dp.callback_query(F.data == "game_basketball")
async def basketball_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        f"👤 {call.from_user.first_name}\n"
        "🏀 Баскетбол - выбери исход!\n\n"
        "💰 Ставка: 10 m¢",
        reply_markup=get_basketball_bet()
    )

# 2. Логика самой игры
@dp.callback_query(F.data.startswith("bet_"))
async def play_basketball(call: types.CallbackQuery):
    user_choice = call.data.split("_")[1] # goal или miss
    
    # Отправляем стикер баскетбола
    # Значения 4 и 5 в баскетболе — это попадание
    msg = await call.message.answer_dice(emoji="🏀")
    result_value = msg.dice.value
    is_goal = result_value >= 4 

    # Ждем пока анимация закончится (около 3-4 секунд)
    await asyncio.sleep(3.5)

    if (user_choice == "goal" and is_goal) or (user_choice == "miss" and not is_goal):
        win_text = "🥳 **Победа! ✅**"
        profit = "24 m¢" if user_choice == "goal" else "16 m¢"
        result_str = "попадание" if is_goal else "мимо"
        
        await call.message.answer(
            f"👤 {call.from_user.first_name}\n"
            f"{win_text}\n\n"
            f"💰 Ставка: 10 m¢\n"
            f"🎯 Выбрано: {'Попадание' if user_choice == 'goal' else 'Мимо'}\n"
            f"💰 Выигрыш: {profit}\n\n"
            f"✨ Итог: {result_str}",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    else:
        await call.message.answer(
            f"👤 {call.from_user.first_name}\n"
            "❌ **Проигрыш!**\n\n"
            "Попробуй еще раз!",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

# Запуск
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
