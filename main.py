import asyncio
import random
import hashlib
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных
user_db = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_header(user: types.User):
    uid = user.id
    if uid not in user_db:
        user_db[uid] = {"balance": 1000, "lvl": 1}
    u = user_db[uid]
    return (f"👤 {user.first_name} | ID: `{uid}`\n"
            f"🏆 Ваш уровень: {u['lvl']}\n"
            f"💰 Баланс: {u['balance']} m¢\n"
            f"────────────────")

# --- ГЛАВНОЕ МЕНЮ (6 кнопок + быстрые + режимы + профиль) ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="g_basket"), 
         InlineKeyboardButton(text="⚽", callback_data="g_foot"),
         InlineKeyboardButton(text="🎯", callback_data="g_darts"), 
         InlineKeyboardButton(text="🎳", callback_data="g_bowl"),
         InlineKeyboardButton(text="🎲", callback_data="g_dice"), 
         InlineKeyboardButton(text="🎰", callback_data="g_slots")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="m_fast"), 
         InlineKeyboardButton(text="Режимы 💣", callback_data="m_modes")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# --- МЕНЮ БЫСТРЫХ ИГР (КАК НА ВИДЕО) ---
def fast_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 Рул. рулетка", callback_data="g_roulette"), 
         InlineKeyboardButton(text="🎰 Монета", callback_data="g_coin")],
        [InlineKeyboardButton(text="🎯 Дартс", callback_data="g_darts"), 
         InlineKeyboardButton(text="🎲 Кубик", callback_data="g_dice")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="prep_mines"), 
         InlineKeyboardButton(text="🚀 Краш", callback_data="g_crash")],
        [InlineKeyboardButton(text="🎣 Рыбалка", callback_data="g_fish"), 
         InlineKeyboardButton(text="🎰 Слоты", callback_data="g_slots")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ])

# --- МЕНЮ ВЫБОРА МИН (3, 4, 5, 10, 11, 12) ---
def mines_setup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 3", callback_data="st_m_3"), 
         InlineKeyboardButton(text="💣 4", callback_data="st_m_4"), 
         InlineKeyboardButton(text="💣 5", callback_data="st_m_5")],
        [InlineKeyboardButton(text="💣 10", callback_data="st_m_10"), 
         InlineKeyboardButton(text="💣 11", callback_data="st_m_11"), 
         InlineKeyboardButton(text="💣 12", callback_data="st_m_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fast")]
    ])

# --- ОБРАБОТЧИКИ НАВИГАЦИИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(get_header(message.from_user), reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(get_header(call.from_user), reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "m_fast")
async def open_fast(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Быстрые игры**", reply_markup=fast_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "prep_mines")
async def open_mines_prep(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_header(call.from_user)}\n💣 **Мины**\nВыбери количество бомб на поле:", reply_markup=mines_setup_kb(), parse_mode="Markdown")

# --- ЛОГИКА ИГРЫ МИНЫ ---

@dp.callback_query(F.data.startswith("st_m_"))
async def start_mines_game(call: types.CallbackQuery):
    count = int(call.data.split("_")[2])
    h = hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]
    
    # Сетка 5x5
    kb_list = []
    for _ in range(5):
        kb_list.append([InlineKeyboardButton(text="🔹", callback_data="mine_click") for _ in range(5)])
    kb_list.append([InlineKeyboardButton(text=f"📥 Забрать (x1.00)", callback_data="m_cashout")])
    kb_list.append([InlineKeyboardButton(text="⬅️ Выход", callback_data="prep_mines")])
    
    text = (f"{get_header(call.from_user)}\n"
            f"💣 **Игра началась!**\n"
            f"Мин на поле: `{count}`\n"
            f"🛡 Hash: `{h}...`\n"
            f"────────────────\n"
            f"Удачи, не подорвись!")
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")

# --- ЛОГИКА ОСТАЛЬНЫХ КНОПОК (DICE) ---

@dp.callback_query(F.data.in_(["g_basket", "g_foot", "g_dice", "g_slots", "g_bowl", "g_darts"]))
async def play_dice_game(call: types.CallbackQuery):
    game_emojis = {
        "g_basket": "🏀", "g_foot": "⚽", "g_dice": "🎲", 
        "g_slots": "🎰", "g_bowl": "🎳", "g_darts": "🎯"
    }
    emoji = game_emojis[call.data]
    
    # Эффект броска
    dice = await call.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5) # Ждем анимацию
    
    # Результат (простая логика выигрыша)
    is_win = dice.dice.value >= 4 if emoji != "🎰" else dice.dice.value in [1, 22, 43, 64]
    
    if is_win:
        user_db[call.from_user.id]["balance"] += 100
        result = "🥳 **Победа!**"
    else:
        user_db[call.from_user.id]["balance"] -= 50
        result = "❌ **Проигрыш!**"
        
    await call.message.answer(f"{get_header(call.from_user)}\n{result}\nРезультат: {dice.dice.value}", reply_markup=main_kb(), parse_mode="Markdown")

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
