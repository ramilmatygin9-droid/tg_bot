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

active_mines_games = {}

DOTS = ". . . . . . . . . . . . . . . . . . ."
LINE = "────────────────"

# --- КЛАВИАТУРЫ (СТАРЫЙ ИНТЕРФЕЙС + ПЕРЕНЕСЕННЫЕ МИНЫ) ---
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
            InlineKeyboardButton(text="💣 МИНЫ", callback_data="prep_mines"), # Мины теперь здесь
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="under_dev")
        ],
        [InlineKeyboardButton(text="🏦 Банк", url="https://t.me/your_bot_link")],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="change_bet")],
        [
            InlineKeyboardButton(text="🆘 Помощь", callback_data="ask_help"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="under_dev")]
    ])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start", "play"))
async def cmd_start(message: types.Message):
    now = datetime.now().strftime("%H:%M:%S | %d.%m.%Y")
    if message.bot.token == GAME_TOKEN:
        text = (
            f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
            f"💰 Баланс: **{user_data['balance']} руб.**\n"
            f"💸 Ставка: **{user_data['bet']} руб.**\n"
            f"🕒 Время: `{now}`\n\n"
            f"👇 *Выбери игру и начинай!*"
        )
        await message.answer(text, reply_markup=main_kb(), parse_mode="Markdown")

# --- ЛОГИКА СООБЩЕНИЙ ---
@dp.message()
async def handle_messages(message: types.Message):
    uid = message.from_user.id
    if message.bot.token == GAME_TOKEN:
        if change_bet_state.get(uid):
            if message.text.isdigit():
                user_data["bet"] = int(message.text)
                change_bet_state[uid] = False
                await message.answer(f"✅ Ставка изменена на **{user_data['bet']} руб.**", reply_markup=main_kb())
            return
        if user_support_state.get(uid):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"adm_reply_{uid}")]])
            sms = (f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n{LINE}\n👤 Имя: {message.from_user.first_name}\n🆔 ID: `{uid}`\n{LINE}\n✉️ Текст: {message.text}")
            try:
                await admin_bot.send_message(MY_ID, sms, reply_markup=kb, parse_mode="Markdown")
                await message.answer("✅ Сообщение отправлено!") 
            except:
                await message.answer("❌ Ошибка при отправке.")
            user_support_state[uid] = False

# --- CALLBACKS ---
@dp.callback_query(F.data == "profile")
async def view_profile(call: types.CallbackQuery):
    text = f"👤 **ПРОФИЛЬ**\n{LINE}\n💰 Баланс: **{user_data['balance']} руб.**\n💸 Ставка: **{user_data['bet']} руб.**"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"🎮 **ГЛАВНОЕ МЕНЮ**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=main_kb())

# --- ПОДГОТОВКА ИГР (СТАРЫЙ ИНТЕРФЕЙС) ---
@dp.callback_query(F.data.startswith("prep_"))
async def prepare_game(call: types.CallbackQuery):
    game = call.data.split("_")[1]
    
    # Логика меню выбора для МИН
    if game == "mines":
        text = f"💣 **Мины · выбери количество!**\n{DOTS}\n💸 Ставка: {user_data['bet']} руб."
        kb = [[InlineKeyboardButton(text="1", callback_data="st_m_1"), InlineKeyboardButton(text="3", callback_data="st_m_3"), InlineKeyboardButton(text="5", callback_data="st_m_5")],
              [InlineKeyboardButton(text="10", callback_data="st_m_10"), InlineKeyboardButton(text="15", callback_data="st_m_15"), InlineKeyboardButton(text="24", callback_data="st_m_24")],
              [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]]
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        return

    header = f"👤 **{call.from_user.first_name}**\n"
    footer = f"{DOTS}\n💸 **Ставка: {user_data['bet']} руб.**"
    kb = []
    
    if game == "dice":
        text = f"{header}🍀 **Кубик · выбери режим!**\n{footer}"
        kb = [[InlineKeyboardButton(text="1", callback_data="bet_dice_v1"), InlineKeyboardButton(text="2", callback_data="bet_dice_v2"), InlineKeyboardButton(text="3", callback_data="bet_dice_v3")],
              [InlineKeyboardButton(text="4", callback_data="bet_dice_v4"), InlineKeyboardButton(text="5", callback_data="bet_dice_v5"), InlineKeyboardButton(text="6", callback_data="bet_dice_v6")],
              [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_dice_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_dice_odd")]]
    elif game == "bowling":
        text = f"{header}🎳 **Боулинг · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="1 кегля", callback_data="bet_bowling_1"), InlineKeyboardButton(text="2 кегли", callback_data="bet_bowling_2")],
              [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_bowling_strike"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_bowling_miss")]]
    elif game == "football":
        text = f"{header}⚽ **Футбол · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_football_goal")], [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_football_miss")]]
    elif game == "basketball":
        text = f"{header}🏀 **Баскет · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="🏀 Попадание - x1.6", callback_data="bet_basketball_goal")], [InlineKeyboardButton(text="🗑 Мимо - x2.4", callback_data="bet_basketball_miss")]]
    elif game == "darts":
        text = f"{header}🎯 **Дартс · выбери исход!**\n{footer}"
        kb = [[InlineKeyboardButton(text="🔴 Красное", callback_data="bet_darts_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_darts_white")],
              [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_darts_center")]]
    elif game == "slots":
        text = f"{header}🎰 **Слоты**\n{footer}"
        kb = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_slots_any")]]
    
    kb.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ЛОГИКА МИН (ПРОДВИНУТАЯ) ---
@dp.callback_query(F.data.startswith("st_m_"))
async def start_mines_game(call: types.CallbackQuery):
    if user_data["balance"] < user_data["bet"]:
        await call.answer("❌ Недостаточно средств!", show_alert=True); return
    count = int(call.data.split("_")[2])
    field = [0]*25
    mines_pos = random.sample(range(25), count)
    for p in mines_pos: field[p] = 1
    active_mines_games[call.from_user.id] = {"field": field, "count": count, "opened": [], "bet": user_data["bet"]}
    await render_mines_field(call, call.from_user.id)

async def render_mines_field(call: types.CallbackQuery, uid: int):
    game = active_mines_games[uid]
    opened = len(game["opened"])
    def get_coef(m, o):
        c = 1.0
        for i in range(o): c *= (25-i)/(25-m-i)
        return round(c * 0.95, 2)
    coef = get_coef(game["count"], opened)
    text = f"💎 **Мины · игра идёт.**\n{DOTS}\n💣 Мин: {game['count']}\n💸 Ставка: {game['bet']} руб.\n📊 Выигрыш: x{coef} / {int(game['bet']*coef)} руб."
    kb = []
    for i in range(5):
        row = [InlineKeyboardButton(text="💎" if (i*5+j) in game["opened"] else "❓", callback_data="none" if (i*5+j) in game["opened"] else f"m_cl_{i*5+j}") for j in range(5)]
        kb.append(row)
    if opened > 0: kb.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="m_take")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("m_cl_"))
async def mine_click(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in active_mines_games: return
    idx = int(call.data.split("_")[2])
    game = active_mines_games[uid]
    if game["field"][idx] == 1:
        user_data["balance"] -= game["bet"]
        await call.message.edit_text(f"💥 **БУМ! Проигрыш.**\n💰 Баланс: {user_data['balance']} руб.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Снова", callback_data="prep_mines")]]))
        del active_mines_games[uid]
    else:
        game["opened"].append(idx)
        await render_mines_field(call, uid)

@dp.callback_query(F.data == "m_take")
async def mine_take(call: types.CallbackQuery):
    uid = call.from_user.id
    game = active_mines_games[uid]
    def get_coef(m, o):
        c = 1.0
        for i in range(o): c *= (25-i)/(25-m-i)
        return round(c * 0.95, 2)
    win = int(game["bet"] * get_coef(game["count"], len(game["opened"])))
    user_data["balance"] += (win - game["bet"])
    await call.message.answer(f"✅ Забрали {win} руб.!")
    await back_to_main(call)
    del active_mines_games[uid]

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, admin_bot)

if __name__ == "__main__":
    asyncio.run(main())
