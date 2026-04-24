import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# Имитация базы данных
user_data = {"balance": 44, "bet": 10}
game_sessions = {}
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ (ИНТЕРФЕЙС) ---

def main_kb():
    """Главное меню как на последнем скриншоте"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏀", callback_data="prep_basketball"),
            InlineKeyboardButton(text="⚽", callback_data="prep_football"),
            InlineKeyboardButton(text="🎯", callback_data="prep_darts"),
            InlineKeyboardButton(text="🎳", callback_data="prep_bowling"),
            InlineKeyboardButton(text="🎲", callback_data="prep_dice"),
            InlineKeyboardButton(text="🎰", callback_data="under_dev")
        ],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_modes")
        ],
        [
            InlineKeyboardButton(text="🕹 Играть в WEB", web_app=types.WebAppInfo(url="https://google.com"))
        ],
        [
            InlineKeyboardButton(text="📝 Изменить ставку", callback_data="change_bet")
        ]
    ])

def modes_kb():
    """Меню режимов из кнопки Режимы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"), InlineKeyboardButton(text="Алмазы 💠", callback_data="under_dev")],
        [InlineKeyboardButton(text="Башня 🏰", callback_data="under_dev"), InlineKeyboardButton(text="Золото ⚜️", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="HiLo ⬇️", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21(Очко)", callback_data="under_dev"), InlineKeyboardButton(text="Пирамида 🏜", callback_data="under_dev")],
        [InlineKeyboardButton(text="🥊 Арена", callback_data="under_dev")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- ЛОГИКА МИНЫ (РАБОЧАЯ) ---

def get_mines_setup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="mstart_1"), InlineKeyboardButton(text="2", callback_data="mstart_2"), InlineKeyboardButton(text="3", callback_data="mstart_3")],
        [InlineKeyboardButton(text="4", callback_data="mstart_4"), InlineKeyboardButton(text="5", callback_data="mstart_5"), InlineKeyboardButton(text="6", callback_data="mstart_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")]
    ])

def get_mines_game_kb(uid):
    s = game_sessions[uid]
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            btn_text = "❓"
            if idx in s['opened']:
                btn_text = "💣" if s['board'][idx] == 1 else "💎"
            row.append(InlineKeyboardButton(text=btn_text, callback_data=f"mclick_{idx}"))
        kb.append(row)
    
    if not s['over']:
        kb.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="m_cashout")])
        kb.append([InlineKeyboardButton(text="Честность 🔑", callback_data="under_dev"), InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    else:
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {s['bet']} m¢", callback_data=f"mstart_{s['mines_count']}")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes"), InlineKeyboardButton(text="Честность 🔑", callback_data="under_dev")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {user_data['balance']} m¢\n💸 **Ставка:** {user_data['bet']} m¢\n\n👇 *Выбери игру и начинай!*"
    await message.answer(text, reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {user_data['balance']} m¢\n💸 **Ставка:** {user_data['bet']} m¢\n\n👇 *Выбери игру и начинай!*"
    await call.message.edit_text(text, reply_markup=main_kb())

@dp.callback_query(F.data == "menu_modes")
async def open_modes(call: types.CallbackQuery):
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {user_data['balance']} m¢\n💸 **Ставка:** {user_data['bet']} m¢\n\n👇 *Выбери игру и начинай!*"
    await call.message.edit_text(text, reply_markup=modes_kb())

# Логика игры Мины
@dp.callback_query(F.data == "menu_mines")
async def mines_setup(call: types.CallbackQuery):
    text = f"Рамиль\n💣 **Мины · выбери мины!**\n{DOTS}\n💸 **Ставка:** {user_data['bet']} m¢"
    await call.message.edit_text(text, reply_markup=get_mines_setup_kb())

@dp.callback_query(F.data.startswith("mstart_"))
async def mines_start(call: types.CallbackQuery):
    m_count = int(call.data.split("_")[1])
    if user_data['balance'] < user_data['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user_data['balance'] -= user_data['bet']
    board = [0] * 25
    for i in random.sample(range(25), m_count): board[i] = 1
    
    game_sessions[call.from_user.id] = {
        'board': board, 'opened': [], 'over': False, 
        'bet': user_data['bet'], 'mines_count': m_count
    }
    
    text = f"Рамиль\n🍀 **Мины · начни игру!**\n{DOTS}\n💣 **Мин:** {m_count}\n💸 **Ставка:** {user_data['bet']} m¢"
    await call.message.edit_text(text, reply_markup=get_mines_game_kb(call.from_user.id))

@dp.callback_query(F.data.startswith("mclick_"))
async def mines_click(call: types.CallbackQuery):
    uid = call.from_user.id
    idx = int(call.data.split("_")[1])
    s = game_sessions.get(uid)
    
    if not s or s['over'] or idx in s['opened']: return

    s['opened'].append(idx)
    if s['board'][idx] == 1: # Попал на мину
        s['over'] = True
        text = f"Рамиль\n💥 **Мины · Проигрыш!**\n{DOTS}\n💣 **Мин:** {s['mines_count']}\n💸 **Ставка:** {s['bet']} m¢\n💎 **Открыто:** {len(s['opened'])-1} из {25-s['mines_count']}"
    else:
        text = f"Рамиль\n💎 **Мины · игра идёт.**\n{DOTS}\n💣 **Мин:** {s['mines_count']}\n💸 **Ставка:** {s['bet']} m¢\n📈 **Выигрыш:** x{1.1 + len(s['opened'])*0.1:.2f}"

    await call.message.edit_text(text, reply_markup=get_mines_game_kb(uid))

@dp.callback_query(F.data == "under_dev")
async def dev(call: types.CallbackQuery):
    await call.answer("🛠 Этот режим скоро появится!", show_alert=True)

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
