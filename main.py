import asyncio
import random
import math
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class GameStates(StatesGroup):
    waiting_for_bet = State()

# Имитация базы данных
users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "balance": 1000.0,
            "bet": 100.0,
            "mines": 3,
            "game_active": False,
            "field": [],
            "opened": []
        }
    return users[uid]

def calculate_mult(opened, total_mines):
    if opened == 0: return 1.0
    # Классическая формула Mines
    res = math.comb(25, opened) / math.comb(25 - total_mines, opened)
    return round(res, 2)

# --- КЛАВИАТУРЫ ---

def main_kb(bal):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💣 Mines", callback_data="mines_start"))
    builder.row(
        types.InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit")
    )
    builder.row(types.InlineKeyboardButton(text="📊 Топ", callback_data="top"),
                types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))
    return builder.as_markup()

def mines_settings_kb(bet, mines):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"💰 Ставка: {bet} ₽", callback_data="change_bet"))
    # Выбор количества мин как в оригинале
    builder.row(
        types.InlineKeyboardButton(text="3💣", callback_data="set_m_3"),
        types.InlineKeyboardButton(text="5💣", callback_data="set_m_5"),
        types.InlineKeyboardButton(text="10💣", callback_data="set_m_10")
    )
    builder.row(types.InlineKeyboardButton(text="▶️ ИГРАТЬ", callback_data="start_round"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="to_main"))
    return builder.as_markup()

def game_field_kb(opened, field, finished=False):
    builder = InlineKeyboardBuilder()
    for i in range(25):
        if i in opened:
            builder.add(types.InlineKeyboardButton(text="💎" if field[i] == 0 else "💣", callback_data="ignore"))
        else:
            text = "🔹" if not finished else ("💣" if field[i] == 1 else "🔹")
            builder.add(types.InlineKeyboardButton(text=text, callback_data=f"press_{i}"))
    builder.adjust(5)
    if not finished:
        builder.row(types.InlineKeyboardButton(text="💰 ЗАБРАТЬ", callback_data="cashout"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    u = get_user(message.from_user.id)
    await message.answer(
        f"👋 **Привет, {message.from_user.first_name}!**\n\n"
        f"💳 Баланс: `{u['balance']:.2f} ₽`",
        reply_markup=main_kb(u['balance']),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def to_main(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    await c.message.edit_text(f"💳 Баланс: `{u['balance']:.2f} ₽`", reply_markup=main_kb(u['balance']), parse_mode="Markdown")

@dp.callback_query(F.data == "mines_start")
async def mines_setup(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    await c.message.edit_text(
        f"💣 **Mines**\n\nВыбери количество мин и ставку:",
        reply_markup=mines_settings_kb(u['bet'], u['mines']),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("set_m_"))
async def set_mines(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    u['mines'] = int(c.data.split("_")[-1])
    await mines_setup(c)

@dp.callback_query(F.data == "change_bet")
async def ask_bet(c: types.CallbackQuery, state: FSMContext):
    await c.message.answer("⌨️ Введите сумму ставки:")
    await state.set_state(GameStates.waiting_for_bet)
    await c.answer()

@dp.message(GameStates.waiting_for_bet)
async def process_bet(m: types.Message, state: FSMContext):
    if m.text.isdigit():
        u = get_user(m.from_user.id)
        u['bet'] = float(m.text)
        await m.answer(f"✅ Ставка обновлена: {u['bet']} ₽")
        await state.clear()
        await cmd_start(m)

@dp.callback_query(F.data == "start_round")
async def start_round(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    if u['balance'] < u['bet']:
        return await c.answer("❌ Недостаточно средств!", show_alert=True)
    
    u['balance'] -= u['bet']
    u['game_active'] = True
    u['opened'] = []
    # Генерация поля
    f = [0]*25
    for p in random.sample(range(25), u['mines']): f[p] = 1
    u['field'] = f
    
    await c.message.edit_text(
        f"🕹 **Игра началась!**\n💎 Коэффициент: `x1.0`",
        reply_markup=game_field_kb([], f),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("press_"))
async def game_process(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    if not u['game_active']: return
    
    idx = int(c.data.split("_")[1])
    if u['field'][idx] == 1: # Проигрыш
        u['game_active'] = False
        await c.message.edit_text(
            f"💥 **ВЗРЫВ!**\nВы потеряли `{u['bet']} ₽`",
            reply_markup=game_field_kb(range(25), u['field'], True),
            parse_mode="Markdown"
        )
    else: # Успех
        u['opened'].append(idx)
        m = calculate_mult(len(u['opened']), u['mines'])
        await c.message.edit_text(
            f"💎 **Успешно!**\n📈 Коэф: `x{m}`\n💰 Выплата: `{round(u['bet']*m, 2)} ₽`",
            reply_markup=game_field_kb(u['opened'], u['field']),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "cashout")
async def cashout(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    if not u['game_active'] or not u['opened']: return
    
    m = calculate_mult(len(u['opened']), u['mines'])
    win = round(u['bet'] * m, 2)
    u['balance'] += win
    u['game_active'] = False
    
    await c.message.edit_text(
        f"✅ **Выигрыш забрали!**\n➕ Прибавка: `{win} ₽`\n💳 Баланс: `{u['balance']:.2f} ₽`",
        reply_markup=main_kb(u['balance']),
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# Расчет коэффициента (математика Mines)
def get_mult(n, m, opened):
    if opened == 0: return 1.0
    return round(math.comb(n, opened) / math.comb(n - m, opened), 2)

# --- Клавиатуры ---

def main_kb(bal):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💣 Mines", callback_data="m_menu"))
    kb.row(types.InlineKeyboardButton(text="👤 Профиль", callback_data="p"),
           types.InlineKeyboardButton(text="💳 Пополнить", callback_data="d"))
    return kb.as_markup()

def settings_kb(bet, m_count):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text=f"💰 Ставка: {bet} ₽", callback_data="edit_bet"))
    kb.row(types.InlineKeyboardButton(text=f"💣 Мин: {m_count}", callback_data="edit_m"))
    kb.row(types.InlineKeyboardButton(text="▶️ ИГРАТЬ", callback_data="start"))
    kb.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="home"))
    return kb.as_markup()

def game_kb(opened, field, finished=False):
    kb = InlineKeyboardBuilder()
    for i in range(25):
        if i in opened:
            val = "💎" if field[i] == 0 else "💣"
            kb.add(types.InlineKeyboardButton(text=val, callback_data="done"))
        else:
            char = "🔹" if not finished else ("💣" if field[i] == 1 else "🔹")
            kb.add(types.InlineKeyboardButton(text=char, callback_data=f"step_{i}"))
    kb.adjust(5)
    if not finished:
        kb.row(types.InlineKeyboardButton(text="💰 ЗАБРАТЬ", callback_data="cash"))
    return kb.as_markup()

# --- Обработчики ---

@dp.message(Command("start"))
async def start(m: types.Message):
    d = get_data(m.from_user.id)
    await m.answer(f"💎 **G-MINES**\n\nБаланс: `{d['bal']} ₽`", reply_markup=main_kb(d['bal']), parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def home(c: types.CallbackQuery):
    d = get_data(c.from_user.id)
    await c.message.edit_text(f"💎 **G-MINES**\n\nБаланс: `{d['bal']} ₽`", reply_markup=main_kb(d['bal']), parse_mode="Markdown")

@dp.callback_query(F.data == "m_menu")
async def m_menu(c: types.CallbackQuery):
    d = get_data(c.from_user.id)
    await c.message.edit_text(f"💣 **Mines**\nНастройте игру:", reply_markup=settings_kb(d['bet'], d['mines']), parse_mode="Markdown")

# Изменение ставки
@dp.callback_query(F.data == "edit_bet")
async def edit_bet(c: types.CallbackQuery, state: FSMContext):
    await c.message.answer("Введите сумму ставки:")
    await state.set_state(GameStates.waiting_for_bet)

@dp.message(GameStates.waiting_for_bet)
async def set_bet(m: types.Message, state: FSMContext):
    if m.text.isdigit():
        d = get_data(m.from_user.id)
        d['bet'] = float(m.text)
        await m.answer(f"✅ Ставка установлена: {d['bet']} ₽")
        await start(m)
        await state.clear()

# Изменение кол-ва мин
@dp.callback_query(F.data == "edit_m")
async def edit_m(c: types.CallbackQuery):
    d = get_data(c.from_user.id)
    d['mines'] = 3 if d['mines'] >= 10 else (d['mines'] + 2) # Простое переключение для примера
    await m_menu(c)

# Логика игры
@dp.callback_query(F.data == "start")
async def start_game(c: types.CallbackQuery):
    d = get_data(c.from_user.id)
    if d['bal'] < d['bet']: return await c.answer("Недостаточно средств!")
    
    d['bal'] -= d['bet']
    d['game'], d['open'] = True, []
    f = [0]*25
    for p in random.sample(range(25), d['mines']): f[p] = 1
    d['field'] = f
    
    await c.message.edit_text(f"🕹 **Игра началась!**\nКоэф: `x1.0`", reply_markup=game_kb([], f), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("step_"))
async def step(c: types.CallbackQuery):
    d = get_data(c.from_user.id)
    if not d['game']: return
    
    idx = int(c.data.split("_")[1])
    if d['field'][idx] == 1: # Проигрыш
        d['game'] = False
        await c.message.edit_text(f"💥 **БОМБА!**\nВы проиграли `{d['bet']} ₽`", reply_markup=game_kb(range(25), d['field'], True), parse_mode="Markdown")
    else: # Алмаз
        d['open'].append(idx)
        mult = get_mult(25, d['mines'], len(d['open']))
        await c.message.edit_text(f"💎 **Удача!**\nКоэф: `x{mult}`\nВыигрыш: `{round(d['bet']*mult, 2)} ₽`", reply_markup=game_kb(d['open'], d['field']), parse_mode="Markdown")

@dp.callback_query(F.data == "cash")
async def cash(c: types.CallbackQuery):
    d = get_data(c.from_user.id)
    if not d['game'] or not d['open']: return
    
    mult = get_mult(25, d['mines'], len(d['open']))
    win = round(d['bet'] * mult, 2)
    d['bal'] += win
    d['game'] = False
    await c.message.edit_text(f"✅ **Вы забрали {win} ₽!**", reply_markup=main_kb(d['bal']), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
