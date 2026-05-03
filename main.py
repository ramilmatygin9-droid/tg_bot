import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ ---
TOKEN = "8536336708:AAENFbvx3EwI1jvZl8-0qLYKWaKey8G3j3I"
ADMIN_ID = 0  # <--- ЗАМЕНИ 0 НА СВОЙ ID (узнай в @userinfobot)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных в памяти
users_data = {}
bot_settings = {"welcome_text": "👑 Добро пожаловать в Phoenix Ultimate Game!"}

class SetupState(StatesGroup):
    waiting_for_welcome = State()

def get_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {"balance": 1000}
    return users_data[user_id]

# --- КЛАВИАТУРЫ ---

def main_menu_kb(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎮 ИГРОВОЙ ЗАЛ", callback_data="all_games")],
        [InlineKeyboardButton(text="💰 МОЙ БАЛАНС", callback_data="my_balance")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙️ НАСТРОЙКИ", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def games_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 РАКЕТА (X2+)", callback_data="game_rocket")],
        [InlineKeyboardButton(text="💣 МИНЫ (САПЕР)", callback_data="game_mines")],
        [InlineKeyboardButton(text="🎰 СЛОТЫ", callback_data="game_slots")],
        [InlineKeyboardButton(text="🖱️ КЛИКЕР", callback_data="game_clicker")],
        [InlineKeyboardButton(text="🔙 НАЗАД", callback_data="to_main")]
    ])

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer(
        f"{bot_settings['welcome_text']}\n\n"
        f"💵 Твой баланс: `{get_user(message.from_user.id)['balance']}` коинов",
        reply_markup=main_menu_kb(message.from_user.id),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "all_games")
async def all_games(callback: CallbackQuery):
    await callback.message.edit_text("✨ **ВЫБЕРИ ИГРУ:**", reply_markup=games_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "my_balance")
async def check_balance(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.answer(f"💰 Твой кошелек: {user['balance']} коинов", show_alert=True)

# --- ИГРА: РАКЕТА ---
@dp.callback_query(F.data == "game_rocket")
async def rocket_start(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☁️ Низко (x1.5)", callback_data="fly_1.5")],
        [InlineKeyboardButton(text="☁️ Средне (x2.0)", callback_data="fly_2.0")],
        [InlineKeyboardButton(text="🌤 Высоко (x5.0)", callback_data="fly_5.0")],
        [InlineKeyboardButton(text="🌌 В космос (x10.0)", callback_data="fly_10.0")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="all_games")]
    ])
    await callback.message.edit_text(
        "🚀 **ЗАПУСК РАКЕТЫ**\n\nВыбери высоту. Чем выше, тем больше приз, но ракета может взорваться! \n💰 Ставка: **100** коинов.",
        reply_markup=kb, parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("fly_"))
async def rocket_fly(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    bet = 100
    if user["balance"] < bet:
        return await callback.answer("❌ Мало коинов!", show_alert=True)
    
    user["balance"] -= bet
    mult = float(callback.data.split("_")[1])
    chances = {1.5: 75, 2.0: 48, 5.0: 18, 10.0: 7} # Шансы в %
    
    await callback.message.edit_text(f"🚀 Ракета летит на высоту **x{mult}**... 💨")
    await asyncio.sleep(2)

    if random.randint(1, 100) <= chances[mult]:
        win = int(bet * mult)
        user["balance"] += win
        await callback.message.answer(f"✅ **УСПЕХ!** Ракета долетела! \nПриз: `{win}` коинов!", parse_mode="Markdown")
    else:
        await callback.message.answer(f"💥 **БА-БАХ!** Ракета взорвалась на полпути... \nПотеряно: `{bet}` коинов.", parse_mode="Markdown")
    await all_games(callback)

# --- ИГРА: МИНЫ ---
@dp.callback_query(F.data == "game_mines")
async def mines_start(callback: CallbackQuery):
    # Генерация поля: 3 кристалла и 1 мина
    field = ["💎", "💎", "💎", "💣"]
    random.shuffle(field)
    
    kb = []
    row = []
    for i in range(4):
        # В callback_data прячем, что там лежит
        res_type = "bomb" if field[i] == "💣" else "gem"
        row.append(InlineKeyboardButton(text="❓", callback_data=f"open_{res_type}"))
    kb.append(row)
    kb.append([InlineKeyboardButton(text="🔙 Выход", callback_data="all_games")])
    
    await callback.message.edit_text(
        "💣 **МИННОЕ ПОЛЕ**\nПод одной кнопкой мина, под другими — кристаллы! Нажми на удачу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("open_"))
async def mines_open(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    res = callback.data.split("_")[1]
    
    if res == "bomb":
        user["balance"] -= 150
        await callback.answer("💥 ВЗРЫВ! Ты проиграл 150 коинов.", show_alert=True)
        await all_games(callback)
    else:
        user["balance"] += 100
        await callback.answer("💎 КРИСТАЛЛ! +100 коинов.", show_alert=True)
        # Перемешиваем заново для следующего хода
        await mines_start(callback)

# --- СЛОТЫ И КЛИКЕР ---

@dp.callback_query(F.data == "game_slots")
async def play_slots(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["balance"] < 50: return await callback.answer("❌ Минимум 50 коинов!")
    user["balance"] -= 50
    msg = await callback.message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)
    if msg.dice.value in [1, 22, 43, 64]:
        user["balance"] += 500
        await callback.message.answer("🎉 **ДЖЕКПОТ!** +500 коинов!")
    await callback.answer()

@dp.callback_query(F.data == "game_clicker")
async def play_clicker(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    user["balance"] += 10
    await callback.message.edit_text(
        f"🖱️ **СУПЕР КЛИКЕР**\nЖми кнопку — руби бабло!\nБаланс: `{user['balance']}`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚡ КЛИК (+10)", callback_data="game_clicker")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="all_games")]
        ]), parse_mode="Markdown"
    )
    await callback.answer()

# --- АДМИНКА ---

@dp.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Сменить Приветствие", callback_data="set_welcome")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("⚙️ **АДМИН-ПАНЕЛЬ**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "set_welcome")
async def set_welcome(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Пришли новый текст для команды /start:")
    await state.set_state(SetupState.waiting_for_welcome)
    await callback.answer()

@dp.message(SetupState.waiting_for_welcome)
async def welcome_saved(message: types.Message, state: FSMContext):
    bot_settings["welcome_text"] = message.text
    await message.answer(f"✅ Приветствие изменено на:\n_{message.text}_", parse_mode="Markdown")
    await state.clear()

# --- СИСТЕМА ---

@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        bot_settings["welcome_text"],
        reply_markup=main_menu_kb(callback.from_user.id)
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
