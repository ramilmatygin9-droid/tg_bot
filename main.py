import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# === НАСТРОЙКИ ===
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app"  # Замени на свою ссылку

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временное хранилище игр (в реальном боте лучше использовать БД)
games = {}

def get_main_menu(balance=182, bet=10):
    text = (
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {balance} m₽\n"
        f"💸 **Ставка:** {bet} m₽\n\n"
        "👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data="none") for e in ["🏀", "⚽", "🎯", "🎳", "🎲", "🎰"]],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="none"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="start_mines")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="none")]
    ])
    return text, kb

def get_mines_kb(user_id):
    game = games[user_id]
    grid = game['grid']
    kb_buttons = []
    
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i + 5):
            btn_text = "❓"
            if j in game['opened']:
                btn_text = "💎"
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
    # Генерируем 3 случайные бомбы
    mines_pos = random.sample(range(25), 3)
    games[user_id] = {
        'mines': mines_pos,
        'opened': [],
        'win': 10, # Начальный выигрыш равен ставке
        'active': True
    }
    await callback.message.edit_text("💣 **ИГРА НАЧАЛАСЬ!**\nНайди все кристаллы и не подорвись!", 
                                     reply_markup=get_mines_kb(user_id), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cell_"))
async def click_cell(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games or not games[user_id]['active']: return

    cell_idx = int(callback.data.split("_")[1])
    game = games[user_id]

    if cell_idx in game['opened']: return

    if cell_idx in game['mines']:
        # ПРОИГРЫШ
        game['active'] = False
        await callback.message.edit_text("💥 **БОМБА!** Ты проиграл свою ставку.", reply_markup=None)
        await asyncio.sleep(2)
        text, kb = get_main_menu()
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        # УГАДАЛ - УДВАИВАЕМ (x1.5 для баланса или x2)
        game['opened'].append(cell_idx)
        game['win'] = int(game['win'] * 2) 
        await callback.message.edit_reply_markup(reply_markup=get_mines_kb(user_id))

@dp.callback_query(F.data == "cashout")
async def cashout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games or not games[user_id]['active']: return
    
    win_amount = games[user_id]['win']
    games[user_id]['active'] = False
    
    await callback.answer(f"Поздравляем! Вы забрали {win_amount} m₽", show_alert=True)
    text, kb = get_main_menu(balance=182 + win_amount) # Условно прибавляем к балансу
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
