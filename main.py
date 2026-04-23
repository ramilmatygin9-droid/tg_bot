import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ДЛЯ ДАРТСА ---

def get_darts_kb():
    # Коэффициенты как на видео
    kb = [
        [InlineKeyboardButton(text="🎯 Центр (x5.0)", callback_data="darts_bet_center")],
        [InlineKeyboardButton(text="🔴 Красное (x2.0)", callback_data="darts_bet_red"),
         InlineKeyboardButton(text="⚪ Белое (x2.0)", callback_data="darts_bet_white")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ЛОГИКА ДАРТСА ---

@dp.callback_query(F.data == "game_darts")
async def darts_welcome(call: types.CallbackQuery):
    await call.message.edit_text(
        f"👤 {call.from_user.first_name}\n"
        "🎯 **Дартс — выбери сектор!**\n\n"
        "Ставка: 10 m¢",
        reply_markup=get_darts_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("darts_bet_"))
async def play_darts(call: types.CallbackQuery):
    bet_type = call.data.split("_")[2] # center, red, white
    
    # Отправляем дартс
    msg = await call.message.answer_dice(emoji="🎯")
    val = msg.dice.value
    
    # Значения дартса в Telegram:
    # 6 - центр (яблочко)
    # 4, 5 - красное
    # 2, 3 - белое
    # 1 - промах
    
    win = False
    coef = 0
    
    if bet_type == "center" and val == 6:
        win, coef = True, 5.0
    elif bet_type == "red" and val in [4, 5]:
        win, coef = True, 2.0
    elif bet_type == "white" and val in [2, 3]:
        win, coef = True, 2.0

    await asyncio.sleep(4) # Ждем пока дротик долетит

    if win:
        res_text = f"🥳 **Победа! x{coef}**\n💰 Выигрыш: {int(10 * coef)} m¢"
    else:
        res_text = "❌ **Проигрыш!**\nДротик попал не туда..."

    retry_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Играть еще раз", callback_data="game_darts")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="to_main")]
    ])

    await call.message.answer(
        f"👤 {call.from_user.first_name}\n"
        f"🎯 Результат броска: {val}\n"
        f"────────────────\n"
        f"{res_text}",
        reply_markup=retry_kb,
        parse_mode="Markdown"
    )

# --- ГЛАВНОЕ МЕНЮ (чтобы все работало) ---

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    # Тут используй клавиатуру из предыдущего кода с 6-ю кнопками игр
    from __main__ import get_main_menu 
    await call.message.edit_text("Выбирай игру:", reply_markup=get_main_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
