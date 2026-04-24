import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 

bot = Bot(token=GAME_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# Имитация БД
user_data = {"balance": 1000, "bet": 10, "mines_count": 3}
game_sessions = {} 
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---

# Главное меню (как на скриншотах)
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
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev"),
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_modes")
        ],
        [
            InlineKeyboardButton(text="⬇️ 5 💰", callback_data="bet_down"),
            InlineKeyboardButton(text="10 💰", callback_data="bet_reset"),
            InlineKeyboardButton(text="⬆️ 20 💰", callback_data="bet_up")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

# Меню режимов (добавлены Мины и заглушки как на фото)
def modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="menu_mines"), InlineKeyboardButton(text="Алмазы 💠", callback_data="under_dev")],
        [InlineKeyboardButton(text="🧱 Башня", callback_data="under_dev"), InlineKeyboardButton(text="Золото ⚜️", callback_data="under_dev")],
        [InlineKeyboardButton(text="🐸 Квак", callback_data="under_dev"), InlineKeyboardButton(text="HiLo ⬇️", callback_data="under_dev")],
        [InlineKeyboardButton(text="♣️ 21(Очко)", callback_data="under_dev"), InlineKeyboardButton(text="Пирамида 🏜", callback_data="under_dev")],
        [InlineKeyboardButton(text="🥊 Арена", callback_data="under_dev")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ])

# --- ЛОГИКА ИГР ---

@dp.callback_query(F.data == "menu_modes")
async def show_modes(call: types.CallbackQuery):
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 **Баланс:** {user_data['balance']} m¢\n"
            f"💸 **Ставка:** {user_data['bet']} m¢\n\n"
            f"👇 *Выбери игру и начинай!*")
    await call.message.edit_text(text, reply_markup=modes_kb())

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_games(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    bet = user_data['bet']
    btn_back = InlineKeyboardButton(text="◀️ назад", callback_data="to_main")
    
    if game == "basketball":
        text = f"Рамиль\n🏀 *Баскетбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_bask_goal")],
              [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_bask_miss")], [btn_back]]
    elif game == "football":
        text = f"Рамиль\n⚽ *Футбол · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_foot_goal")],
              [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_foot_miss")], [btn_back]]
    elif game == "darts":
        text = (f"Рамиль\n🎯 *Дартс · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 🔴 Красное (x1.94) ❞\n┕ ⚪️ Белое (x2.9)\n┕ 🎯 Центр (x5.8)\n┕ 😟 Мимо (x5.8)")
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_dart_red"), InlineKeyboardButton(text="⚪️ Белое", callback_data="play_dart_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="play_dart_center"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_dart_miss")], [btn_back]]
    elif game == "bowling":
        text = (f"Рамиль\n🎳 *Боулинг · выбери исход!*\n{DOTS}\n💸 *Ставка: {bet} m¢*\n\n"
                f"🔰 *Коэффициенты:*\n"
                f"┕ 1️⃣ - 5️⃣ кегли (x5.8) ❞\n┕ 🎳 Страйк (x5.8)\n┕ 😟 Мимо (x5.8)")
        kb = [[InlineKeyboardButton(text="1 кегла", callback_data="play_bowl_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_bowl_3")],
              [InlineKeyboardButton(text="4 кегли", callback_data="play_bowl_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_bowl_5")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_bowl_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_bowl_0")], [btn_back]]
    elif game == "dice":
        text = f"Рамиль\n🍀 *Кубик · выбери режим!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
        kb = [[InlineKeyboardButton(text="1", callback_data="play_dice_1"), InlineKeyboardButton(text="2", callback_data="play_dice_2"), InlineKeyboardButton(text="3", callback_data="play_dice_3")],
              [InlineKeyboardButton(text="4", callback_data="play_dice_4"), InlineKeyboardButton(text="5", callback_data="play_dice_5"), InlineKeyboardButton(text="6", callback_data="play_dice_6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_dice_odd")],
              [InlineKeyboardButton(text="＝ Равно 3 x5.8", callback_data="play_dice_equal3")],
              [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="play_dice_high"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="play_dice_low")],
              [btn_back]]
    else: return
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("play_"))
async def play_engine(call: types.CallbackQuery):
    data = call.data.split("_")
    game_code, selection = data[1], data[2]
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True); return
    user_data["balance"] -= user_data["bet"]
    emojis = {"bask": "🏀", "foot": "⚽", "dart": "🎯", "bowl": "🎳", "dice": "🎲"}
    dice_msg = await call.message.answer_dice(emoji=emojis.get(game_code, "🎲"))
    await asyncio.sleep(4)
    val = dice_msg.dice.value
    win, multiplier, outcome_text = False, 0.0, "неизвестно"
    # (Логика выигрыша как в прошлом коде)
    # ...
    header = f"🥳 {emojis[game_code]} Победа! ✅" if win else f"{emojis[game_code]} Проигрыш ❌"
    res_text = (f"{header}\n{DOTS}\n💸 *Ставка:* {user_data['bet']} m¢\n"
                f"🎲 *Выбрано:* {selection}\n💰 *Выигрыш:* x{multiplier} / {int(user_data['bet']*multiplier)} m¢\n"
                f"{DOTS}\n⚡️ *Итог:* {outcome_text}")
    await call.message.answer(res_text, reply_markup=main_kb())

# --- МИНЫ ---

def mines_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes")]
    ])

@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    text = f"Рамиль\n💣 *Мины · выбери мины!*\n{DOTS}\n💸 *Ставка: {user_data['bet']} m¢*"
    await call.message.edit_text(text, reply_markup=mines_start_kb())

@dp.callback_query(F.data.startswith("setmines_"))
async def start_mines_game(call: types.CallbackQuery):
    m_count = int(call.data.split("_")[1])
    user_id = call.from_user.id
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно m¢!", show_alert=True); return
    user_data["balance"] -= user_data["bet"]
    board = [0]*25
    for idx in random.sample(range(25), m_count): board[idx] = 1
    game_sessions[user_id] = {'board': board, 'bet': user_data['bet'], 'mines': m_count, 'opened': [], 'game_over': False}
    await call.message.edit_text(f"Рамиль\n🍀 *Мины · начни игру!*\n{DOTS}\n💣 *Мин: {m_count}*\n💸 *Ставка: {user_data['bet']} m¢*", reply_markup=get_mines_board_kb(user_id))

def get_mines_board_kb(user_id):
    s = game_sessions.get(user_id)
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            char = "❓"
            if idx in s['opened']: char = "💥" if s['board'][idx] == 1 else "💎"
            row.append(InlineKeyboardButton(text=char, callback_data=f"mopen_{idx}"))
        kb.append(row)
    if not s['game_over']:
        kb.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="m_cashout")])
        kb.append([InlineKeyboardButton(text="Честность 🔑", callback_data="under_dev"), InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    else:
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {s['bet']} m¢", callback_data=f"setmines_{s['mines']}")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_modes"), InlineKeyboardButton(text="Честность 🔑", callback_data="under_dev")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.callback_query(F.data.startswith("mopen_"))
async def mines_step(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    s = game_sessions.get(call.from_user.id)
    if not s or s['game_over'] or idx in s['opened']: return
    s['opened'].append(idx)
    if s['board'][idx] == 1:
        s['game_over'] = True
        text = f"Рамиль\n💥 *Мины · Проигрыш!*\n{DOTS}\n💣 *Мин: {s['mines']}*\n💸 *Ставка: {s['bet']} m¢*"
    else:
        text = f"Рамиль\n💎 *Мины · игра идёт.*\n{DOTS}\n💣 *Мин: {s['mines']}*\n💸 *Ставка: {s['bet']} m¢*"
    await call.message.edit_text(text, reply_markup=get_mines_board_kb(call.from_user.id))

# --- ОБЩЕЕ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "under_dev")
async def dev(call: types.CallbackQuery): await call.answer("🚧 В разработке", show_alert=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
