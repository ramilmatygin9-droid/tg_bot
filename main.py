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
user_data = {"balance": 1000, "bet": 10}
game_sessions = {}
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---

def main_kb():
    """Главное меню со скриншота"""
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
    """Меню из кнопки Режимы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"), InlineKeyboardButton(text="Алмазы 💠", callback_data="under_dev")],
        [InlineKeyboardButton(text="Башня 🏰", callback_data="under_dev"), InlineKeyboardButton(text="Золото ⚜️", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="HiLo ⬇️", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21(Очко)", callback_data="under_dev"), InlineKeyboardButton(text="Пирамида 🏜", callback_data="under_dev")],
        [InlineKeyboardButton(text="🥊 Арена", callback_data="under_dev")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="mstart_1"), InlineKeyboardButton(text="2", callback_data="mstart_2"), InlineKeyboardButton(text="3", callback_data="mstart_3")],
        [InlineKeyboardButton(text="4", callback_data="mstart_4"), InlineKeyboardButton(text="5", callback_data="mstart_5"), InlineKeyboardButton(text="6", callback_data="mstart_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")]
    ])

# --- ОБРАБОТЧИКИ ОСНОВНЫХ КНОПОК ---

@dp.message(Command("start", "play"))
async def start_cmd(message: types.Message):
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {user_data['balance']} m¢\n💸 **Ставка:** {user_data['bet']} m¢\n\n👇 *Выбери игру и начинай!*"
    await message.answer(text, reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {user_data['balance']} m¢\n💸 **Ставка:** {user_data['bet']} m¢\n\n👇 *Выбери игру и начинай!*"
    await call.message.edit_text(text, reply_markup=main_kb())

@dp.callback_query(F.data == "menu_modes")
async def open_modes_menu(call: types.CallbackQuery):
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {user_data['balance']} m¢\n💸 **Ставка:** {user_data['bet']} m¢\n\n👇 *Выбери игру и начинай!*"
    await call.message.edit_text(text, reply_markup=modes_kb())

@dp.callback_query(F.data == "change_bet")
async def change_bet_handler(call: types.CallbackQuery):
    user_data['bet'] = 10 if user_data['bet'] != 10 else 20
    await call.answer(f"Ставка изменена на {user_data['bet']} m¢")
    await to_main(call)

# --- ЛОГИКА МИН ---

@dp.callback_query(F.data == "menu_mines")
async def mines_setup(call: types.CallbackQuery):
    text = f"Рамиль\n💣 **Мины · выбери мины!**\n{DOTS}\n💸 **Ставка:** {user_data['bet']} m¢"
    await call.message.edit_text(text, reply_markup=mines_start_kb())

@dp.callback_query(F.data.startswith("mstart_"))
async def mines_game_begin(call: types.CallbackQuery):
    m_count = int(call.data.split("_")[1])
    uid = call.from_user.id
    if user_data['balance'] < user_data['bet']:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    user_data['balance'] -= user_data['bet']
    board = [0] * 25
    for i in random.sample(range(25), m_count): board[i] = 1
    
    game_sessions[uid] = {'board': board, 'opened': [], 'over': False, 'mines': m_count, 'bet': user_data['bet']}
    await update_mines_screen(call, uid)

async def update_mines_screen(call, uid):
    s = game_sessions[uid]
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            char = "❓"
            if idx in s['opened']: char = "💣" if s['board'][idx] == 1 else "💎"
            row.append(InlineKeyboardButton(text=char, callback_data=f"mstep_{idx}"))
        kb.append(row)
    
    if not s['over']:
        if len(s['opened']) > 0:
            kb.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="m_cashout")])
        kb.append([InlineKeyboardButton(text="Честность 🔑", callback_data="under_dev"), InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    else:
        kb.append([InlineKeyboardButton(text="🔄 Повторить", callback_data=f"mstart_{s['mines']}")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")])
    
    msg = "Игра идёт..." if not s['over'] else "Игра окончена!"
    await call.message.edit_text(f"Рамиль\n💣 **Мины · {msg}**\n{DOTS}\n💣 **Мин:** {s['mines']}\n💸 **Ставка:** {s['bet']} m¢", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("mstep_"))
async def mines_step(call: types.CallbackQuery):
    uid = call.from_user.id
    idx = int(call.data.split("_")[1])
    s = game_sessions.get(uid)
    if not s or s['over'] or idx in s['opened']: return
    
    s['opened'].append(idx)
    if s['board'][idx] == 1: s['over'] = True
    await update_mines_screen(call, uid)

@dp.callback_query(F.data == "m_cashout")
async def mines_win(call: types.CallbackQuery):
    uid = call.from_user.id
    s = game_sessions.get(uid)
    if not s or s['over']: return
    
    mult = 1.2 + (len(s['opened']) * 0.2)
    win = int(s['bet'] * mult)
    user_data['balance'] += win
    s['over'] = True
    await call.answer(f"💰 Забрано {win} m¢!", show_alert=True)
    await update_mines_screen(call, uid)

# --- ПРОЧИЕ ИГРЫ ---

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_emoji_games(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    text = f"Рамиль\n🎲 **Игра {game.capitalize()}**\n{DOTS}\n💸 **Ставка:** {user_data['bet']} m¢"
    kb = [[InlineKeyboardButton(text="▶️ Начать игру", callback_data=f"go_{game}")], [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("go_"))
async def start_emoji_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    emojis = {"basketball": "🏀", "football": "⚽", "darts": "🎯", "bowling": "🎳", "dice": "🎲", "slots": "🎰"}
    await call.message.answer_dice(emoji=emojis.get(game, "🎲"))
    await asyncio.sleep(4)
    await call.message.answer("Игра завершена!", reply_markup=main_kb())

@dp.callback_query(F.data == "under_dev")
async def dev_stub(call: types.CallbackQuery):
    await call.answer("🚧 Режим в разработке", show_alert=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

