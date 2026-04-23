import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Вставь свой токен
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_header(user):
    return (f"👤 {user.first_name} | ID: `{user.id}`\n"
            f"🏆 Ваш уровень: 1\n"
            f"💰 Баланс: 1000 m¢\n"
            f"────────────────")

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="prep_basketball"), 
            InlineKeyboardButton(text="⚽", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
            InlineKeyboardButton(text="🎳", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰", callback_data="prep_slots")
        ],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"), 
            InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
        ]
    ])

# --- МЕНЮ ВЫБОРА ДЛЯ КАЖДОЙ ИГРЫ ---

def get_game_bet_kb(game):
    kb = []
    if game == "basketball":
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="bet_basketball_goal")],
              [InlineKeyboardButton(text="🏀 Мимо - x1.6", callback_data="bet_basketball_miss")]]
    elif game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.8", callback_data="bet_football_goal")],
              [InlineKeyboardButton(text="⚽ Мимо - x2.2", callback_data="bet_football_miss")]]
    elif game == "darts":
        kb = [[InlineKeyboardButton(text="🎯 Центр - x5.0", callback_data="bet_darts_center")],
              [InlineKeyboardButton(text="🔴 Красное - x2.0", callback_data="bet_darts_red")],
              [InlineKeyboardButton(text="⚪ Белое - x2.0", callback_data="bet_darts_white")]]
    elif game == "dice":
        kb = [[InlineKeyboardButton(text="1️⃣ Нечетное - x1.9", callback_data="bet_dice_odd"),
               InlineKeyboardButton(text="2️⃣ Четное - x1.9", callback_data="bet_dice_even")],
              [InlineKeyboardButton(text="📉 1-3 - x2.0", callback_data="bet_dice_small"),
               InlineKeyboardButton(text="📈 4-6 - x2.0", callback_data="bet_dice_big")]]
    elif game == "bowling":
        kb = [[InlineKeyboardButton(text="🎳 Страйк - x5.0", callback_data="bet_bowling_strike")],
              [InlineKeyboardButton(text="🎳 Сбить часть - x1.4", callback_data="bet_bowling_partial")]]
    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить - 10 m¢", callback_data="bet_slots_spin")]]
    
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(get_header(message.from_user) + "\nВыбирай игру:", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back(call: types.CallbackQuery):
    await call.message.edit_text(get_header(call.from_user) + "\nВыбирай игру:", reply_markup=main_kb())

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    names = {"basketball": "Баскетбол", "football": "Футбол", "darts": "Дартс", "dice": "Кубик", "bowling": "Боулинг", "slots": "Слоты"}
    await call.message.edit_text(f"{get_header(call.from_user)}\nИгра: **{names[game]}**\nВыбери исход:", 
                                 reply_markup=get_game_bet_kb(game), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("bet_"))
async def play(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]
    bet_choice = data[2]
    
    emoji_map = {"basketball": "🏀", "football": "⚽", "darts": "🎯", "bowling": "🎳", "dice": "🎲", "slots": "🎰"}
    dice_msg = await call.message.answer_dice(emoji=emoji_map[game_type])
    val = dice_msg.dice.value
    
    await asyncio.sleep(3.5)
    
    win = False
    coef = 1.0
    
    # Логика выигрыша
    if game_type == "basketball":
        is_goal = val >= 4
        win = (bet_choice == "goal" and is_goal) or (bet_choice == "miss" and not is_goal)
        coef = 2.4 if bet_choice == "goal" else 1.6
    elif game_type == "football":
        is_goal = val >= 3
        win = (bet_choice == "goal" and is_goal) or (bet_choice == "miss" and not is_goal)
        coef = 1.8 if bet_choice == "goal" else 2.2
    elif game_type == "darts":
        if bet_choice == "center": win = (val == 6); coef = 5.0
        elif bet_choice == "red": win = (val in [4, 5]); coef = 2.0
        elif bet_choice == "white": win = (val in [2, 3]); coef = 2.0
    elif game_type == "dice":
        if bet_choice == "even": win = (val % 2 == 0); coef = 1.9
        elif bet_choice == "odd": win = (val % 2 != 0); coef = 1.9
        elif bet_choice == "small": win = (val <= 3); coef = 2.0
        elif bet_choice == "big": win = (val >= 4); coef = 2.0
    elif game_type == "bowling":
        is_strike = (val == 6)
        win = (bet_choice == "strike" and is_strike) or (bet_choice == "partial" and not is_strike and val > 1)
        coef = 5.0 if bet_choice == "strike" else 1.4
    elif game_type == "slots":
        win = (val in [1, 22, 43, 64]); coef = 10.0 # Джекпот на слотах

    res_text = "🥳 **Победа! ✅**" if win else "❌ **Проигрыш!**"
    profit = f"{int(10 * coef)} m¢" if win else "0 m¢"

    final_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Играть еще раз", callback_data=f"prep_{game_type}")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="to_main")]
    ])

    await call.message.answer(f"{get_header(call.from_user)}\n{res_text}\n\n💰 Выигрыш: {profit}\n🎲 Результат: {val}", 
                               reply_markup=final_kb, parse_mode="Markdown")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
