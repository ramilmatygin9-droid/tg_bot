import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ КНОПКИ ---
def get_main_menu():
    kb = [
        [
            InlineKeyboardButton(text="🏀", callback_data="game_basketball"), 
            InlineKeyboardButton(text="⚽", callback_data="game_football"),
            InlineKeyboardButton(text="🎯", callback_data="game_darts"),
            InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="game_dice"),
            InlineKeyboardButton(text="🎰", callback_data="game_slots")
        ],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"), 
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_bet_menu(game_type):
    # В видео для баскетбола и футбола похожие меню выбора
    prefix = "🏀" if game_type == "basketball" else "⚽"
    kb = [
        [InlineKeyboardButton(text=f"{prefix} Попадание - x2.4", callback_data=f"play_{game_type}_goal")],
        [InlineKeyboardButton(text=f"{prefix} Мимо - x1.6", callback_data=f"play_{game_type}_miss")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\nВыбирай игру в меню ниже:",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text("Выбирай игру:", reply_markup=get_main_menu())

# Выбор конкретной игры
@dp.callback_query(F.data.in_(["game_basketball", "game_football"]))
async def choose_game(call: types.CallbackQuery):
    game_type = "basketball" if "basketball" in call.data else "football"
    game_name = "Баскетбол" if game_type == "basketball" else "Футбол"
    
    await call.message.edit_text(
        f"👤 {call.from_user.first_name} (ID: `{call.from_user.id}`)\n"
        f"🏆 Ваш уровень: 1\n\n"
        f"**{game_name}** — выберите исход матча!\n"
        f"💰 Ставка: 10 m¢",
        reply_markup=get_bet_menu(game_type),
        parse_mode="Markdown"
    )

# Логика броска/удара
@dp.callback_query(F.data.startswith("play_"))
async def process_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]  # basketball / football
    user_choice = data[2] # goal / miss
    
    emoji = "🏀" if game_type == "basketball" else "⚽"
    
    # Отправляем дайс (анимацию)
    dice_msg = await call.message.answer_dice(emoji=emoji)
    
    # Логика Telegram Dice:
    # Баскетбол: 4, 5 - гол. Футбол: 3, 4, 5 - гол.
    if game_type == "basketball":
        is_win_val = dice_msg.dice.value >= 4
    else:
        is_win_val = dice_msg.dice.value >= 3

    await asyncio.sleep(3.5) # Ждем завершения анимации

    success = (user_choice == "goal" and is_win_val) or (user_choice == "miss" and not is_win_val)
    
    if success:
        multiplier = 2.4 if user_choice == "goal" else 1.6
        res_text = "🥳 **Победа! ✅**"
        profit = f"{int(10 * multiplier)} m¢"
    else:
        res_text = "❌ **Проигрыш!**"
        profit = "0 m¢"

    result_desc = "попадание" if is_win_val else "мимо"

    final_text = (
        f"👤 {call.from_user.first_name} | ID: `{call.from_user.id}`\n"
        f"{res_text}\n\n"
        f"💰 Ставка: 10 m¢\n"
        f"🎯 Выбрано: {'Попадание' if user_choice == 'goal' else 'Мимо'}\n"
        f"💰 Выигрыш: {profit}\n\n"
        f"✨ Итог: {result_desc}"
    )

    # Кнопка как в видео (играть снова)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Играть еще раз", callback_data=f"game_{game_type}")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="to_main")]
    ])

    await call.message.answer(final_text, reply_markup=kb, parse_mode="Markdown")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
