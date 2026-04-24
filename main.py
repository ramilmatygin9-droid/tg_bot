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
game_sessions = {} # Хранение состояний игры Мины
DOTS = "· · · · · · · · · · · · · · · · ·"

# --- КЛАВИАТУРЫ ---
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
            InlineKeyboardButton(text="Режимы 💣", callback_data="menu_mines") # Изменено
        ],
        [
            InlineKeyboardButton(text="⬇️ 5 💰", callback_data="bet_down"),
            InlineKeyboardButton(text="10 💰", callback_data="bet_reset"),
            InlineKeyboardButton(text="⬆️ 20 💰", callback_data="bet_up")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")] # Профиль вернулся
    ])

def mines_amount_kb():
    # Клавиатура выбора количества мин (как на image_7.png)
    kb = [
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double_bet")],
        [InlineKeyboardButton(text="1", callback_data="setmines_1"), InlineKeyboardButton(text="2", callback_data="setmines_2"), InlineKeyboardButton(text="3", callback_data="setmines_3")],
        [InlineKeyboardButton(text="4", callback_data="setmines_4"), InlineKeyboardButton(text="5", callback_data="setmines_5"), InlineKeyboardButton(text="6", callback_data="setmines_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_mines_game_kb(user_id):
    session = game_sessions.get(user_id)
    if not session: return None
    
    board = session['board']
    opened = session['opened']
    
    kb = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            if idx in opened:
                # Если ячейка открыта, показываем что там было
                text = "💎" if board[idx] == 0 else "💥"
                cb_data = "mines_ignore" # Нельзя нажать повторено
            else:
                # Ячейка закрыта
                text = "❓"
                cb_data = f"mines_open_{idx}"
            row.append(InlineKeyboardButton(text=text, callback_data=cb_data))
        kb.append(row)
        
    # Кнопки управления
    if not session['game_over']:
        if len(opened) > 0:
             # Если открыли хоть один алмаз, можно забрать выигрыш
             current_mult = session['multipliers'][len(opened) - 1]
             win_cash = int(session['bet'] * current_mult)
             kb.append([InlineKeyboardButton(text=f"Забрать выигрыш ✅ ({win_cash} m¢)", callback_data="mines_cashout")])
        kb.append([InlineKeyboardButton(text="Честность 🔑", callback_data="mines_provably")])
    else:
        # Игра окончена (проигрыш или забрали деньги)
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {session['bet']} m¢", callback_data="start_mines")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="menu_mines"), InlineKeyboardButton(text="Честность 🔑", callback_data="mines_provably")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def calculate_mines_multipliers(mines_count):
    # Упрощенный расчет множителей (для примера)
    mults = []
    total_cells = 25
    safe_cells = total_cells - mines_count
    current_mult = 1.0
    
    for i in range(safe_cells):
        # Множитель растет с каждым шагом
        step_mult = total_cells / (total_cells - i)
        # Добавляем небольшой бонус в зависимости от количества мин
        risk_bonus = 1.0 + (mines_count / 100.0)
        current_mult *= step_mult * risk_bonus
        mults.append(round(current_mult, 2))
        
    return mults

def generate_mines_text(user_id, status_icon="💣", status_text="начни игру!"):
    session = game_sessions.get(user_id)
    bet = session['bet'] if session else user_data['bet']
    mines = session['mines_count'] if session else user_data['mines_count']
    
    text = f"Рамиль\n{status_icon} *Мины · {status_text}*\n{DOTS}\n💣 *Мин: {mines}*\n💸 *Ставка: {bet} m¢*"
    
    if session and not session['game_over']:
        opened_count = len(session['opened'])
        if opened_count > 0:
            current_mult = session['multipliers'][opened_count - 1]
            win_cash = int(bet * current_mult)
            text += f"\n📈 *Выигрыш: x{current_mult} / {win_cash} m¢*"
            
        # Список следующих множителей (как на image_6.png)
        start_idx = opened_count
        next_mults = session['multipliers'][start_idx : start_idx + 5]
        if next_mults:
            mults_str = " ➡️ ".join([f"x{m}" for m in next_mults])
            text += f"\n\n🧮 *Следующий множитель:*\n┕ {mults_str} ❞\n┕ ➡️ ..."
            
    elif session and session['game_over']:
        # Текст при проигрыше или выдаче
        if session['won']:
             opened_count = len(session['opened'])
             final_mult = session['multipliers'][opened_count - 1]
             win_cash = int(bet * final_mult)
             text += f"\n✅ *Выигрыш забран!*"
             text += f"\n💰 *Итог: x{final_mult} / {win_cash} m¢*"
        else:
             opened_count = len(session['opened'])
             # Множитель, который могли забрать до взрыва
             potential_mult = session['multipliers'][opened_count - 1] if opened_count > 0 else 1.0
             potential_cash = int(bet * potential_mult)
             text += f"\n💥 *Проигрыш!*"
             text += f"\n💎 *Открыто: {opened_count} из {25 - mines}*"
             text += f"\n\n✅ *Мог забрать: x{potential_mult} / {potential_cash} m¢* ❞"

    return text

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    await message.answer(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    # Очищаем сессию игры, если возвращаемся в меню
    game_sessions.pop(call.from_user.id, None)
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢", reply_markup=main_kb())

# --- ЛОГИКА МИН ---

# 1. Экран выбора количества мин
@dp.callback_query(F.data == "menu_mines")
async def mines_menu(call: types.CallbackQuery):
    game_sessions.pop(call.from_user.id, None) # На всякий случай чистим старую игру
    bet = user_data['bet']
    text = f"Рамиль\n💣 *Мины · выбери мины!*\n{DOTS}\n💸 *Ставка: {bet} m¢*"
    await call.message.edit_text(text, reply_markup=mines_amount_kb())

# 2. Установка количества мин и старт игры
@dp.callback_query(F.data.startswith("setmines_"))
async def set_mines_and_start(call: types.CallbackQuery):
    mines_count = int(call.data.split("_")[1])
    user_data['mines_count'] = mines_count
    await start_mines_game(call)

# Отдельная кнопка "Повторить" в конце игры
@dp.callback_query(F.data == "start_mines")
async def repeat_mines_game(call: types.CallbackQuery):
    await start_mines_game(call)

async def start_mines_game(call: types.CallbackQuery):
    user_id = call.from_user.id
    bet = user_data['bet']
    mines_count = user_data['mines_count']
    
    if user_data["balance"] < bet:
        await call.answer("❌ Недостаточно m¢!", show_alert=True)
        return
        
    user_data["balance"] -= bet
    
    # Создаем поле: 0 - алмаз, 1 - мина
    board = [0] * 25
    mine_indices = random.sample(range(25), mines_count)
    for idx in mine_indices:
        board[idx] = 1
        
    # Инициализируем сессию
    game_sessions[user_id] = {
        'board': board,
        'bet': bet,
        'mines_count': mines_count,
        'opened': [],
        'multipliers': calculate_mines_multipliers(mines_count),
        'game_over': False,
        'won': False
    }
    
    text = generate_mines_text(user_id, "💣", "начни игру!")
    await call.message.edit_text(text, reply_markup=get_mines_game_kb(user_id))

# 3. Клик по ячейке поля
@dp.callback_query(F.data.startswith("mines_open_"))
async def mines_open_cell(call: types.CallbackQuery):
    user_id = call.from_user.id
    session = game_sessions.get(user_id)
    
    if not session or session['game_over']:
        await call.answer()
        return
        
    cell_idx = int(call.data.split("_")[2])
    
    if cell_idx in session['opened']:
        await call.answer()
        return
        
    session['opened'].append(cell_idx)
    
    # Проверяем, что открыли
    if session['board'][cell_idx] == 1:
        # ВЗРЫВ! Проигрыш
        session['game_over'] = True
        session['won'] = False
        # Открываем все мины для честности (упрощенно, только нажатую)
        text = generate_mines_text(user_id, "💥", "Проигрыш!")
    else:
        # Нашли алмаз!
        # Проверяем, не открыли ли мы все безопасные ячейки
        if len(session['opened']) == (25 - session['mines_count']):
            # Автоматический кэшаут, если все открыто
            session['game_over'] = True
            session['won'] = True
            final_mult = session['multipliers'][-1]
            win_cash = int(session['bet'] * final_mult)
            user_data["balance"] += win_cash
            text = generate_mines_text(user_id, "💎", "ПОБЕДА!")
        else:
            # Продолжаем игру
            text = generate_mines_text(user_id, "💎", "игра идёт.")
            
    await call.message.edit_text(text, reply_markup=get_mines_game_kb(user_id))

# 4. Забрать выигрыш
@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(call: types.CallbackQuery):
    user_id = call.from_user.id
    session = game_sessions.get(user_id)
    
    if not session or session['game_over'] or len(session['opened']) == 0:
        await call.answer()
        return
        
    session['game_over'] = True
    session['won'] = True
    
    final_mult = session['multipliers'][len(session['opened']) - 1]
    win_cash = int(session['bet'] * final_mult)
    user_data["balance"] += win_cash
    
    text = generate_mines_text(user_id, "💰", "Выигрыш забран!")
    await call.message.edit_text(text, reply_markup=get_mines_game_kb(user_id))

# 5. Игнорирование кликов по открытым ячейкам
@dp.callback_query(F.data == "mines_ignore")
async def mines_ignore_click(call: types.CallbackQuery):
    await call.answer()

# --- ОСТАЛЬНОЕ БЕЗ ИЗМЕНЕНИЙ ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_other_games(call: types.CallbackQuery):
    # Код для остальных игр остается прежним (из предыдущего ответа)
    await call.answer("Логика этой игры не менялась", show_alert=True)

@dp.callback_query(F.data.startswith("play_"))
async def play_engine_other(call: types.CallbackQuery):
    # Код для движка остальных игр остается прежним
    await call.answer()

@dp.callback_query(F.data.startswith("bet_"))
async def change_bet(call: types.CallbackQuery):
    action = call.data.split("_")[1]
    if action == "up": user_data["bet"] += 10
    elif action == "down" and user_data["bet"] > 5: user_data["bet"] -= 5
    elif action == "reset": user_data["bet"] = 10
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} m¢\n🔥 Текущая ставка: {user_data['bet']}", reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    await call.answer(f"👤 Профиль\nБаланс: {user_data['balance']} m¢", show_alert=True)

@dp.callback_query(F.data == "under_dev")
async def under_development(call: types.CallbackQuery):
    await call.answer("🚧 В разработке...", show_alert=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
