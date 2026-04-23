import asyncio
import random
import math
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Твой токен
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для ввода ставки
class GameStates(StatesGroup):
    waiting_for_bet = State()

# Временная БД
users = {}

def get_data(uid):
    if uid not in users:
        users[uid] = {"bal": 5000.0, "bet": 100.0, "mines": 3, "game": False, "field": [], "open": []}
    return users[uid]

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
