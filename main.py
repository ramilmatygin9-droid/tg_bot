import random
import asyncio
import hashlib
import time
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# --- НАСТРОЙКИ ЛОГИРОВАНИЯ ---
logging.basicConfig(level=logging.INFO)

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
API_TOKEN = '8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ГЛОБАЛЬНАЯ БАЗА ДАННЫХ (ЭМУЛЯЦИЯ) ---
# В реальном проекте тут подключение к PostgreSQL/SQLite
class Database:
    def __init__(self):
        self.users = {}

    def get_user(self, uid, name="Игрок"):
        if uid not in self.users:
            self.users[uid] = {
                'name': name,
                'balance': 100.0,
                'reg_date': datetime.now().strftime("%d.%m.%Y"),
                'stats': {
                    'mines_wins': 0, 'mines_loses': 0,
                    'gems_wins': 0, 'gems_loses': 0,
                    'arena_wins': 0, 'arena_loses': 0,
                    'fast_wins': 0, 'fast_loses': 0,
                    'total_bet': 0.0, 'total_win': 0.0
                },
                'bets': {
                    'mines': 10.0,
                    'gems': 10.0,
                    'arena': 10.0,
                    'fast': 10.0
                },
                'current_game': None
            }
        return self.users[uid]

db = Database()

# --- СОСТОЯНИЯ (FSM) ---
class Form(StatesGroup):
    edit_mines_bet = State()
    edit_gems_bet = State()
    edit_arena_bet = State()
    edit_fast_bet = State()

# --- МАТЕМАТИЧЕСКИЙ ДВИЖОК ---
class Engine:
    @staticmethod
    def get_mines_mult(mines, opened):
        if opened == 0: return 1.0
        # Классическая формула комбинаторики для игры Mines
        res = 1.0
        for i in range(opened):
            res *= (25 - i) / (25 - mines - i)
        return round(res * 0.96, 2)

    @staticmethod
    def generate_hash():
        salt = str(random.getrandbits(128))
        return hashlib.sha256(salt.encode()).hexdigest()

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💣 МИНЫ (5x5)", callback_data="play_mines"))
    builder.row(types.InlineKeyboardButton(text="💎 АЛМАЗНАЯ БАШНЯ", callback_data="play_gems"))
    builder.row(types.InlineKeyboardButton(text="🏟 АРЕНА: ДУЭЛЬ", callback_data="play_arena"))
    builder.row(types.InlineKeyboardButton(text="🚀 БЫСТРЫЙ КРАШ", callback_data="play_fast"))
    builder.row(types.InlineKeyboardButton(text="👤 МОЙ ПРОФИЛЬ", callback_data="view_profile"))
    builder.row(types.InlineKeyboardButton(text="⚙️ НАСТРОЙКА СТАВОК", callback_data="all_bets"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user = db.get_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        f"👋 *ПРИВЕТ, {message.from_user.first_name.upper()}!*\n\n"
        f"Твой баланс: *{user['balance']:.2f}* mф\n"
        f"Выбирай режим и начинай выигрывать!",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# --- РАЗДЕЛ: ПРОФИЛЬ ---
@dp.callback_query(F.data == "view_profile")
async def profile_cb(callback: types.CallbackQuery):
    u = db.get_user(callback.from_user.id)
    s = u['stats']
    text = (
        f"👤 *ПРОФИЛЬ ИГРОКА:* `{u['name']}`\n"
        f"................................................\n"
        f"💰 *БАЛАНС:* {u['balance']:.2f} mф\n"
        f"📅 *В ИГРЕ С:* {u['reg_date']}\n\n"
        f"📊 *СТАТИСТИКА (W/L):*\n"
        f"💣 Мины: {s['mines_wins']} / {s['mines_loses']}\n"
        f"💎 Башня: {s['gems_wins']} / {s['gems_loses']}\n"
        f"🏟 Арена: {s['arena_wins']} / {s['arena_loses']}\n"
        f"🚀 Краш: {s['fast_wins']} / {s['fast_loses']}\n\n"
        f"💸 *ВСЕГО СТАВОК:* {s['total_bet']:.1f}\n"
        f"🏆 *ОБЩИЙ ВЫИГРЫШ:* {s['total_win']:.1f}\n"
        f"................................................"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В ГЛАВНОЕ МЕНЮ", callback_data="to_main")
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- РАЗДЕЛ: НАСТРОЙКА СТАВОК ---
@dp.callback_query(F.data == "all_bets")
async def bets_menu(callback: types.CallbackQuery):
    u = db.get_user(callback.from_user.id)
    b = u['bets']
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💣 Мины: {b['mines']}", callback_data="set_mines_bet")
    builder.button(text=f"💎 Башня: {b['gems']}", callback_data="set_gems_bet")
    builder.button(text=f"🏟 Арена: {b['arena']}", callback_data="set_arena_bet")
    builder.button(text=f"🚀 Краш: {b['fast']}", callback_data="set_fast_bet")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🏠 НАЗАД", callback_data="to_main"))
    await callback.message.edit_text("*ВЫБЕРИ РЕЖИМ ДЛЯ ИЗМЕНЕНИЯ СТАВКИ:*", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("set_") and F.data.endswith("_bet"))
async def bet_input_start(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    if mode == "mines": await state.set_state(Form.edit_mines_bet)
    elif mode == "gems": await state.set_state(Form.edit_gems_bet)
    elif mode == "arena": await state.set_state(Form.edit_arena_bet)
    elif mode == "fast": await state.set_state(Form.edit_fast_bet)
    await callback.message.edit_text(f"📝 *ВВЕДИ СУММУ СТАВКИ ДЛЯ* `{mode.upper()}`:")

@dp.message(Form.edit_mines_bet)
@dp.message(Form.edit_gems_bet)
@dp.message(Form.edit_arena_bet)
@dp.message(Form.edit_fast_bet)
async def bet_save(message: types.Message, state: FSMContext):
    st = await state.get_state()
    try:
        val = float(message.text)
        if val < 0.1: raise ValueError
        u = db.get_user(message.from_user.id)
        if "mines" in st: u['bets']['mines'] = val
        elif "gems" in st: u['bets']['gems'] = val
        elif "arena" in st: u['bets']['arena'] = val
        elif "fast" in st: u['bets']['fast'] = val
        await state.clear()
        await message.answer(f"✅ *СТАВКА СОХРАНЕНА:* {val} mф", reply_markup=main_menu_kb(), parse_mode="Markdown")
    except:
        await message.answer("❌ *ОШИБКА! ВВЕДИ ПОЛОЖИТЕЛЬНОЕ ЧИСЛО.*")

# --- ИГРОВОЙ ФУНКЦИОНАЛ: МИНЫ ---
@dp.callback_query(F.data == "play_mines")
async def mines_difficulty(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for m in [3, 5, 10, 15, 24]:
        builder.button(text=f"💣 {m} МИН", callback_data=f"start_mines_{m}")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🏠 НАЗАД", callback_data="to_main"))
    await callback.message.edit_text("*ВЫБЕРИ СЛОЖНОСТЬ (КОЛ-ВО МИН):*", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("start_mines_"))
async def mines_game_init(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = db.get_user(uid)
    m_count = int(callback.data.split("_")[-1])
    bet = u['bets']['mines']

    if u['balance'] < bet:
        return await callback.answer("❌ НЕДОСТАТОЧНО СРЕДСТВ!", show_alert=True)

    u['balance'] -= bet
    u['stats']['total_bet'] += bet
    
    # Генерация поля
    cells = ["💎"] * (25 - m_count) + ["💣"] * m_count
    random.shuffle(cells)
    
    active_game = {
        'type': 'mines',
        'field': [cells[i:i+5] for i in range(0, 25, 5)],
        'mask': [[False for _ in range(5)] for _ in range(5)],
        'm_count': m_count,
        'gems': 0,
        'bet': bet,
        'hash': Engine.generate_hash(),
        'over': False
    }
    u['current_game'] = active_game
    await render_mines(callback.message, uid)

async def render_mines(message, uid):
    u = db.get_user(uid)
    game = u['current_game']
    builder = InlineKeyboardBuilder()

    for r in range(5):
        for c in range(5):
            if game['mask'][r][c]:
                char = game['field'][r][c]
                builder.button(text=char, callback_data="void")
            elif game['over']:
                # "Пизда открылась" - показываем всё поле в конце
                char = game['field'][r][c]
                builder.button(text=char, callback_data="void")
            else:
                builder.button(text="❓", callback_data=f"mines_cl_{r}_{c}")
    
    builder.adjust(5)
    
    current_m = Engine.get_mines_mult(game['m_count'], game['gems'])
    next_m = Engine.get_mines_mult(game['m_count'], game['gems'] + 1)

    if not game['over']:
        if game['gems'] > 0:
            builder.row(types.InlineKeyboardButton(text="💰 ЗАБРАТЬ ВЫИГРЫШ", callback_data="mines_cashout"))
        text = (
            f"💣 *ИГРА: МИНЫ* (x{current_m})\n"
            f"........................\n"
            f"💵 *СТАВКА:* {game['bet']} mф\n"
            f"💎 *НАЙДЕНО:* {game['gems']}\n"
            f"⏭ *СЛЕДУЮЩИЙ:* x{next_m}\n"
            f"........................"
        )
    else:
        # Проверяем, был ли взрыв
        won = any(game['field'][r][c] == "💣" and game['mask'][r][c] for r in range(5) for c in range(5))
        title = "💥 *ПРОИГРЫШ!*" if won else "🏆 *ВЫИГРЫШ!*"
        builder.row(types.InlineKeyboardButton(text="🔄 ПОВТОРИТЬ", callback_data=f"start_mines_{game['m_count']}"))
        builder.row(types.InlineKeyboardButton(text="🏠 МЕНЮ", callback_data="to_main"))
        text = f"{title}\n\n📊 *ИТОГ:* x{current_m}\n🔑 *HASH:* `{game['hash'][:16]}`"

    await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("mines_cl_"))
async def mines_click_handler(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = db.get_user(uid)
    game = u['current_game']
    if not game or game['over']: return
    
    _, _, r, c = callback.data.split("_")
    r, c = int(r), int(c)
    game['mask'][r][c] = True
    
    if game['field'][r][c] == "💣":
        game['over'] = True
        u['stats']['mines_loses'] += 1
        u['stats']['total_lost'] = u['stats'].get('total_lost', 0) + game['bet']
    else:
        game['gems'] += 1
        if game['gems'] == (25 - game['m_count']):
            await mines_finish(callback, uid, True)
            return
    
    await render_mines(callback.message, uid)

@dp.callback_query(F.data == "mines_cashout")
async def mines_manual_cash(callback: types.CallbackQuery):
    await mines_finish(callback, callback.from_user.id, False)

async def mines_finish(callback, uid, auto):
    u = db.get_user(uid)
    game = u['current_game']
    if game['over']: return
    
    m = Engine.get_mines_mult(game['m_count'], game['gems'])
    win = game['bet'] * m
    u['balance'] += win
    u['stats']['mines_wins'] += 1
    u['stats']['total_win'] += win
    game['over'] = True
    await render_mines(callback.message, uid)

# --- ИГРОВОЙ ФУНКЦИОНАЛ: АЛМАЗНАЯ БАШНЯ (GEMS) ---
@dp.callback_query(F.data == "play_gems")
async def gems_init(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = db.get_user(uid)
    bet = u['bets']['gems']
    if u['balance'] < bet: return await callback.answer("❌ МАЛО mф", show_alert=True)

    u['balance'] -= bet
    u['stats']['total_bet'] += bet
    
    # 7 уровней, в каждом 3 клетки, 1 бомба
    tower = []
    for _ in range(7):
        row = ["💎", "💎", "💣"]
        random.shuffle(row)
        tower.append(row)
        
    u['current_game'] = {
        'type': 'gems',
        'field': tower,
        'step': 0,
        'bet': bet,
        'over': False,
        'hash': Engine.generate_hash()
    }
    await render_gems(callback.message, uid)

async def render_gems(message, uid):
    u = db.get_user(uid)
    game = u['current_game']
    builder = InlineKeyboardBuilder()
    
    # Отрисовка башни снизу вверх
    for r in range(6, -1, -1):
        for c in range(3):
            if r < game['step']:
                builder.button(text=game['field'][r][c], callback_data="void")
            elif r == game['step'] and not game['over']:
                builder.button(text="❓", callback_data=f"gems_cl_{c}")
            elif game['over']:
                builder.button(text=game['field'][r][c], callback_data="void")
            else:
                builder.button(text="🔒", callback_data="void")
    
    builder.adjust(3)
    mults = [1.45, 2.18, 3.27, 4.91, 7.36, 11.05, 16.57]
    curr_m = mults[game['step']-1] if game['step'] > 0 else 1.0
    
    if not game['over']:
        if game['step'] > 0:
            builder.row(types.InlineKeyboardButton(text="💰 ЗАБРАТЬ", callback_data="gems_cashout"))
        text = f"💎 *АЛМАЗНАЯ БАШНЯ*\n\n📈 *МНОЖИТЕЛЬ:* x{curr_m}\n📶 *ЭТАЖ:* {game['step']+1}/7"
    else:
        builder.row(types.InlineKeyboardButton(text="🔄 ЕЩЕ РАЗ", callback_data="play_gems"))
        builder.row(types.InlineKeyboardButton(text="🏠 МЕНЮ", callback_data="to_main"))
        text = "*БАШНЯ ОБРУШИЛАСЬ!*"

    await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("gems_cl_"))
async def gems_click(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = db.get_user(uid)
    game = u['current_game']
    idx = int(callback.data.split("_")[-1])
    
    if game['field'][game['step']][idx] == "💣":
        game['over'] = True
        u['stats']['gems_loses'] += 1
    else:
        game['step'] += 1
        if game['step'] == 7:
            await gems_finish(callback, uid)
            return
    await render_gems(callback.message, uid)

async def gems_finish(callback, uid):
    u = db.get_user(uid)
    game = u['current_game']
    mults = [1.45, 2.18, 3.27, 4.91, 7.36, 11.05, 16.57]
    win = game['bet'] * mults[game['step']-1]
    u['balance'] += win
    u['stats']['gems_wins'] += 1
    u['stats']['total_win'] += win
    game['over'] = True
    await render_gems(callback.message, uid)

@dp.callback_query(F.data == "gems_cashout")
async def gems_manual(callback: types.CallbackQuery):
    await gems_finish(callback, callback.from_user.id)

# --- ИГРОВОЙ ФУНКЦИОНАЛ: АРЕНА (DUEL) ---
@dp.callback_query(F.data == "play_arena")
async def arena_duel(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = db.get_user(uid)
    bet = u['bets']['arena']
    if u['balance'] < bet: return await callback.answer("❌ МАЛО mф", show_alert=True)

    u['balance'] -= bet
    p_card = random.randint(2, 14)
    d_card = random.randint(2, 14)
    
    cards = {11: "J", 12: "Q", 13: "K", 14: "A"}
    p_name = cards.get(p_card, str(p_card))
    d_name = cards.get(d_card, str(d_card))

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 РЕВАНШ", callback_data="play_arena"))
    builder.row(types.InlineKeyboardButton(text="🏠 МЕНЮ", callback_data="to_main"))

    if p_card > d_card:
        win = bet * 1.95
        u['balance'] += win
        u['stats']['arena_wins'] += 1
        res = f"🏆 *ПОБЕДА!*\nТвоя карта: *{p_name}*\nДилер: *{d_name}*\n💰 +{win:.1f}"
    elif p_card < d_card:
        u['stats']['arena_loses'] += 1
        res = f"💀 *ПРОИГРЫШ*\nТвоя карта: *{p_name}*\nДилер: *{d_name}*\n📉 -{bet}"
    else:
        u['balance'] += bet
        res = f"🤝 *НИЧЬЯ!*\nОба выкинули *{p_name}*\nСтавка возвращена."

    await callback.message.edit_text(f"🏟 *АРЕНА: ДУЭЛЬ*\n\n{res}", reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- ИГРОВОЙ ФУНКЦИОНАЛ: БЫСТРЫЙ КРАШ ---
@dp.callback_query(F.data == "play_fast")
async def crash_game(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = db.get_user(uid)
    bet = u['bets']['fast']
    if u['balance'] < bet: return await callback.answer("❌ МАЛО mф", show_alert=True)

    u['balance'] -= bet
    # Шанс на крупный икс
    outcome = random.random()
    if outcome < 0.6: mult = 0.0 # Слив
    elif outcome < 0.85: mult = random.uniform(1.2, 2.0)
    else: mult = random.uniform(2.0, 5.0)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 ПУСК", callback_data="play_fast"))
    builder.row(types.InlineKeyboardButton(text="🏠 МЕНЮ", callback_data="to_main"))

    if mult > 0:
        win = bet * mult
        u['balance'] += win
        u['stats']['fast_wins'] += 1
        res = f"🚀 *КРАШ ВЗЛЕТЕЛ!*\nМножитель: *x{mult:.2f}*\n💰 Выигрыш: {win:.1f}"
    else:
        u['stats']['fast_loses'] += 1
        res = f"💥 *КРАШНУЛСЯ СРАЗУ!*\nМножитель: *x0.0*\n📉 Ставка потеряна."

    await callback.message.edit_text(f"🚀 *БЫСТРЫЙ КРАШ*\n\n{res}", reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- СИСТЕМНЫЕ ОБРАБОТЧИКИ ---
@dp.callback_query(F.data == "to_main")
async def to_main_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"👋 *ГЛАВНОЕ МЕНЮ*\n\nБаланс: *{user['balance']:.2f}* mф",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "void")
async def void_handler(callback: types.CallbackQuery):
    await callback.answer()

async def main():
    print(f"Бот запущен на токене: {API_TOKEN}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
