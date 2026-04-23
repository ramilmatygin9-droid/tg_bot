import asyncio
import random
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
GAME_TOKEN = "8359920618:AAHKLw57b3LJ7MupDtL3hWP_Msl1SwTABSQ" 
ADMIN_TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"
MY_ID = 846239258 

bot = Bot(token=GAME_TOKEN)
admin_bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

user_data = {"balance": 1000, "level": 1, "bet": 10}
user_support_state = {}
admin_reply_state = {}
change_bet_state = {}

# Хранилище активных игр Мин
active_mines = {}

DOTS = ". . . . . . . . . . . . . . . . . . ."
LINE = "────────────────"

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="prep_basketball"), InlineKeyboardButton(text="⚽", callback_data="prep_football"), InlineKeyboardButton(text="🎯", callback_data="prep_darts"), InlineKeyboardButton(text=" bowling", callback_data="prep_bowling"), InlineKeyboardButton(text="🎲", callback_data="prep_dice"), InlineKeyboardButton(text="🎰", callback_data="prep_slots")],
        [InlineKeyboardButton(text="💣 МИНЫ", callback_data="prep_mines"), InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")],
        [InlineKeyboardButton(text="🏦 Банк", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"), InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="under_dev")]
    ])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    now = datetime.now().strftime("%H:%M:%S | %d.%m.%Y")
    text = (f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 Баланс: **{user_data['balance']} руб.**\n💸 Ставка: **{user_data['bet']} руб.**\n🕒 Время: `{now}`\n\n👇 *Выбери игру и начинай!*")
    await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- РЕЖИМ МИНЫ (КАК НА СКРИНШОТАХ) ---
@dp.callback_query(F.data == "prep_mines")
async def mines_choice(call: types.CallbackQuery):
    text = f"Рамиль\n💣 **Мины · выбери мины!**\n{DOTS}\n💸 Ставка: {user_data['bet']} руб."
    kb = [
        [InlineKeyboardButton(text="Удвоить ставку 💸", callback_data="mines_double")],
        [InlineKeyboardButton(text="1", callback_data="st_m_1"), InlineKeyboardButton(text="2", callback_data="st_m_2"), InlineKeyboardButton(text="3", callback_data="st_m_3")],
        [InlineKeyboardButton(text="4", callback_data="st_m_4"), InlineKeyboardButton(text="5", callback_data="st_m_5"), InlineKeyboardButton(text="6", callback_data="st_m_6")],
        [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "mines_double")
async def mines_double(call: types.CallbackQuery):
    user_data["bet"] *= 2
    await mines_choice(call)

@dp.callback_query(F.data.startswith("st_m_"))
async def start_mines_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True); return
    
    count = int(call.data.split("_")[2])
    uid = call.from_user.id
    
    # Генерация поля: 0 - пусто, 1 - мина
    field = [0]*25
    mines_pos = random.sample(range(25), count)
    for p in mines_pos: field[p] = 1
    
    active_mines[uid] = {"field": field, "count": count, "opened": [], "bet": user_data["bet"]}
    await render_mines(call, uid)

async def render_mines(call: types.CallbackQuery, uid: int):
    game = active_mines[uid]
    opened_count = len(game["opened"])
    
    # Расчет множителя (упрощенно как на скрине)
    coef = round(1 + (opened_count * (game["count"] / 10)), 2)
    next_coefs = " → ".join([f"x{round(coef + (i * 0.07), 2)}" for i in range(1, 6)])
    
    text = (f"Рамиль\n💎 **Мины · игра идёт.**\n{DOTS}\n💣 Мин: {game['count']}\n"
            f"💸 Ставка: {game['bet']} руб.\n📊 Выигрыш: x{coef} / {int(game['bet']*coef)} руб.\n\n"
            f"🧱 Следующий множитель:\n`| {next_coefs} |`")
    
    kb = []
    for i in range(5):
        row = []
        for j in range(5):
            idx = i * 5 + j
            if idx in game["opened"]:
                row.append(InlineKeyboardButton(text="💎", callback_data="ignore"))
            else:
                row.append(InlineKeyboardButton(text="❓", callback_data=f"m_cl_{idx}"))
        kb.append(row)
    
    if opened_count > 0:
        kb.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="mines_take")])
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("m_cl_"))
async def mine_click(call: types.CallbackQuery):
    uid = call.from_user.id
    idx = int(call.data.split("_")[2])
    game = active_mines[uid]
    
    if game["field"][idx] == 1: # ПРОИГРЫШ
        user_data["balance"] -= game["bet"]
        coef = round(1 + (len(game["opened"]) * (game["count"] / 10)), 2)
        text = (f"Рамиль\n💥 **Мины · Проигрыш!**\n{DOTS}\n💣 Мин: {game['count']}\n"
                f"💸 Ставка: {game['bet']} руб.\n💎 Открыто: {len(game['opened'])} из 25\n"
                f"📝 Мог забрать: x{coef} / {int(game['bet']*coef)} руб.")
        
        kb = []
        for i in range(5):
            row = []
            for j in range(5):
                cur = i * 5 + j
                if cur == idx: row.append(InlineKeyboardButton(text="💥", callback_data="ignore"))
                elif game["field"][cur] == 1: row.append(InlineKeyboardButton(text="💣", callback_data="ignore"))
                else: row.append(InlineKeyboardButton(text="💎", callback_data="ignore"))
            kb.append(row)
        kb.append([InlineKeyboardButton(text=f"🔄 Повторить · {game['bet']} руб.", callback_data=f"st_m_{game['count'] Black")])
        kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main"), InlineKeyboardButton(text="Честность 🔑", callback_data="ignore")])
        
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        del active_mines[uid]
    else: # ПРОДОЛЖАЕМ
        game["opened"].append(idx)
        if len(game["opened"]) + game["count"] == 25: # Все открыл
            await mines_take(call)
        else:
            await render_mines(call, uid)

@dp.callback_query(F.data == "mines_take")
async def mines_take(call: types.CallbackQuery):
    uid = call.from_user.id
    game = active_mines[uid]
    coef = round(1 + (len(game["opened"]) * (game["count"] / 10)), 2)
    win = int(game["bet"] * coef)
    user_data["balance"] += (win - game["bet"])
    
    await call.message.answer(f"✅ Вы забрали {win} руб.!")
    await back_to_main(call)
    del active_mines[uid]

# --- ОСТАЛЬНОЙ КОД (БЕЗ ИЗМЕНЕНИЙ) ---
@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def view_profile(call: types.CallbackQuery):
    await call.message.edit_text(f"👤 **ПРОФИЛЬ**\n{LINE}\n💰 Баланс: **{user_data['balance']} руб.**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]]))

@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    if game == "mines": return
    kb = [[InlineKeyboardButton(text="Играть", callback_data=f"bet_{game}_go")], [InlineKeyboardButton(text="◀️ назад", callback_data="to_main")]]
    await call.message.edit_text(f"🕹 Игра: {game.upper()}\nСтавка: {user_data['bet']} руб.", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.message()
async def handle_messages(message: types.Message):
    if message.text.isdigit() and change_bet_state.get(message.from_user.id):
        user_data["bet"] = int(message.text)
        change_bet_state[message.from_user.id] = False
        await message.answer(f"✅ Ставка: {user_data['bet']} руб.", reply_markup=main_kb())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
