import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ИЗ ВИДЕО ---

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="prep_basketball"),
         InlineKeyboardButton(text="⚽", callback_data="prep_football"),
         InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
         InlineKeyboardButton(text="🎳", callback_data="prep_bowling"),
         InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
         InlineKeyboardButton(text="🎰", callback_data="prep_slots")]
    ])

# Универсальная кнопка назад
back_btn = [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]

# --- МЕНЮ ВЫБОРА ПЕРЕД ИГРОЙ ---

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    header = f"👤 {call.from_user.first_name}\n────────────────\n"
    
    if game == "football":
        kb = [[InlineKeyboardButton(text="⚽ Забить гол (x1.8)", callback_data="bet_football_goal")], back_btn]
        await call.message.edit_text(header + "⚽ **Футбол**\nСтавка: 10 m¢", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    
    elif game == "basketball":
        kb = [[InlineKeyboardButton(text="🏀 Попасть в кольцо (x2.0)", callback_data="bet_basketball_goal")], back_btn]
        await call.message.edit_text(header + "🏀 **Баскетбол**\nСтавка: 10 m¢", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    
    elif game == "darts":
        kb = [[InlineKeyboardButton(text="🎯 Центр (x5.0)", callback_data="bet_darts_6")],
              [InlineKeyboardButton(text="🔴 Красное (x2.0)", callback_data="bet_darts_red"),
               InlineKeyboardButton(text="⚪ Белое (x2.0)", callback_data="bet_darts_white")], back_btn]
        await call.message.edit_text(header + "🎯 **Дартс**\nВыбери сектор:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

    elif game == "dice":
        kb = [[InlineKeyboardButton(text="1️⃣ Нечетное", callback_data="bet_dice_odd"), 
               InlineKeyboardButton(text="2️⃣ Четное", callback_data="bet_dice_even")],
              [InlineKeyboardButton(text="📉 1-3", callback_data="bet_dice_small"), 
               InlineKeyboardButton(text="📈 4-6", callback_data="bet_dice_big")], back_btn]
        await call.message.edit_text(header + "🎲 **Кубик**\nВыбери исход:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

    elif game == "bowling":
        kb = [[InlineKeyboardButton(text="🎳 Страйк (x5.0)", callback_data="bet_bowling_6")], back_btn]
        await call.message.edit_text(header + "🎳 **Боулинг**\nСбей все кегли!", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

    elif game == "slots":
        kb = [[InlineKeyboardButton(text="🎰 Крутить (10 m¢)", callback_data="bet_slots_any")], back_btn]
        await call.message.edit_text(header + "🎰 **Слоты**\nИспытай удачу!", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА РЕЗУЛЬТАТОВ ---

@dp.callback_query(F.data.startswith("bet_"))
async def play_game(call: types.CallbackQuery):
    data = call.data.split("_")
    game_type = data[1]
    user_choice = data[2]
    
    emoji_map = {"football": "⚽", "basketball": "🏀", "darts": "🎯", "bowling": "🎳", "dice": "🎲", "slots": "🎰"}
    msg = await call.message.answer_dice(emoji=emoji_map[game_type])
    
    await asyncio.sleep(4)
    val = msg.dice.value
    win = False

    if game_type == "football": win = val >= 3
    elif game_type == "basketball": win = val >= 4
    elif game_type == "bowling": win = val == 6
    elif game_type == "slots": win = val in [1, 22, 43, 64]
    elif game_type == "darts":
        if user_choice == "6": win = val == 6
        elif user_choice == "red": win = val in [4, 5]
        elif user_choice == "white": win = val in [2, 3]
    elif game_type == "dice":
        if user_choice == "even": win = val % 2 == 0
        elif user_choice == "odd": win = val % 2 != 0
        elif user_choice == "small": win = val <= 3
        elif user_choice == "big": win = val >= 4

    res_text = "🥳 **Победа!**" if win else "❌ **Проигрыш**"
    await call.message.answer(f"👤 {call.from_user.first_name}\n{res_text}\nРезультат: {val}", reply_markup=main_kb(), parse_mode="Markdown")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"👤 {message.from_user.first_name}\nВыбирай игру:", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back(call: types.CallbackQuery):
    await call.message.edit_text(f"👤 {call.from_user.first_name}\nВыбирай игру:", reply_markup=main_kb())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
