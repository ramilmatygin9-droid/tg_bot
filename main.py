import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# === ТВОИ ДАННЫЕ ===
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище игр для Мины
games = {}

def get_main_menu(balance=182, bet=10):
    text = (
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {balance} m₽\n"
        f"💸 **Ставка:** {bet} m₽\n\n"
        "👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="play_basket"),
            InlineKeyboardButton(text="⚽", callback_data="dev"),
            InlineKeyboardButton(text="🎯", callback_data="dev"),
            InlineKeyboardButton(text="🎳", callback_data="dev"),
            InlineKeyboardButton(text="🎲", callback_data="dev"),
            InlineKeyboardButton(text="🎰", callback_data="play_slots"),
        ],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="dev"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="start_mines")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="dev")]
    ])
    return text, kb

# --- ОБРАБОТКА МЯЧИКА (🏀) И СЛОТОВ (🎰) ---

@dp.callback_query(F.data == "play_basket")
async def play_basketball(callback: types.CallbackQuery):
    # Бот кидает настоящий мяч в чат
    msg = await callback.message.answer_dice(emoji="🏀")
    # Если попал (в баскетболе это значения 4 и 5)
    if msg.dice.value >= 4:
        await callback.message.answer(f"🔥 **ПОПАДАНИЕ!** Вы выиграли 20 m₽")
    else:
        await callback.message.answer("❌ Промах! Попробуйте еще раз.")

@dp.callback_query(F.data == "play_slots")
async def play_slots(callback: types.CallbackQuery):
    # Бот крутит настоящий слот-барабан
    msg = await callback.message.answer_dice(emoji="🎰")
    # Если выпало 777 (значение 64 для слотов)
    if msg.dice.value == 64:
        await callback.message.answer("💎 **ДЖЕКПОТ! 777!** +1000 m₽")
    elif msg.dice.value in [1, 22, 43]: # Комбинации трех одинаковых (кроме 777)
        await callback.message.answer("🎉 Выигрышная комбинация! +100 m₽")
    else:
        await callback.message.answer("😢 Неудача. Попробуйте снова!")

# --- КНОПКА "В РАЗРАБОТКЕ" ---

@dp.callback_query(F.data == "dev")
async def development(callback: types.CallbackQuery):
    await callback.answer("🛠 Этот раздел находится в разработке!", show_alert=True)

# --- ЛОГИКА МИН (БЕЗ ИЗМЕНЕНИЙ) ---

def get_mines_kb(user_id):
    game = games[user_id]
    kb_buttons = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i + 5):
            btn_text = "❓"
            if j in game['opened']: btn_text = "💎"
            row.append(InlineKeyboardButton(text=btn_text, callback_data=f"cell_{j}"))
        kb_buttons.append(row)
    kb_buttons.append([InlineKeyboardButton(text=f"Забрать выигрыш ✅ ({game['win']} m₽)", callback_data="cashout")])
    return InlineKeyboardMarkup(inline_keyboard=kb_buttons)

@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    text, kb = get_main_menu()
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "start_mines")
async def start_mines(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mines_pos = random.sample(range(25), 3)
    games[user_id] = {'mines': mines_pos, 'opened': [], 'win': 10, 'active': True}
    await callback.message.edit_text("💣 **МИНЫ**\nУгадывай кристаллы!", reply_markup=get_mines_kb(user_id), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cell_"))
async def click_cell(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games or not games[user_id]['active']: return
    cell_idx = int(callback.data.split("_")[1])
    game = games[user_id]
    if cell_idx in game['opened']: return
    if cell_idx in game['mines']:
        game['active'] = False
        await callback.message.edit_text("💥 **БАБАХ!** Ты проиграл.", reply_markup=None)
        await asyncio.sleep(2)
        text, kb = get_main_menu()
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        game['opened'].append(cell_idx)
        game['win'] *= 2 
        await callback.message.edit_reply_markup(reply_markup=get_mines_kb(user_id))

@dp.callback_query(F.data == "cashout")
async def cashout_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games or not games[user_id]['active']: return
    win = games[user_id]['win']
    games[user_id]['active'] = False
    await callback.answer(f"Ты забрал {win} m₽!", show_alert=True)
    text, kb = get_main_menu()
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

