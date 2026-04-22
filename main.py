import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
WEB_APP_URL = "https://твой-сайт.vercel.app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Имитация базы данных
user_db = {}

def get_user(uid, name="Игрок"):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'game': None, 'name': name}
    return user_db[uid]

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu(uid):
    u = get_user(uid)
    text = (
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        f"💰 **Баланс:** {u['bal']} m₽\n"
        f"💸 **Ставка:** {u['bet']} m₽\n\n"
        "👇 *Выбери игру и начинай!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["🏀", "⚽", "🎯", "🎳", "🎲", "🎰"]],
        [
            InlineKeyboardButton(text="🚀 Быстрые", callback_data="none"), 
            InlineKeyboardButton(text="Режимы 💣", callback_data="mines_start")
        ],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="none")]
    ])
    return text, kb

# --- ПОДМЕНЮ ДЛЯ КАЖДОЙ ИГРЫ (КАК НА СКРИНШОТАХ) ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_submenu(callback: types.CallbackQuery):
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id, callback.from_user.first_name)
    
    # Базовый текст для всех игр
    base_text = f"👤 **{u['name']}**\n"
    
    rows = []
    if emoji == "⚽":
        text = base_text + "⚽ **Футбол · выбери исход!**\n. . . . . . . . . . . . . . . . . .\n" + f"💸 **Ставка:** {u['bet']} m₽"
        rows = [
            [InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="bet_⚽_win")],
            [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="bet_⚽_lose")]
        ]
    elif emoji == "🏀":
        text = base_text + "🏀 **Баскетбол · выбери исход!**\n. . . . . . . . . . . . . . . . . .\n" + f"💸 **Ставка:** {u['bet']} m₽"
        rows = [
            [InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="bet_🏀_win")],
            [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="bet_🏀_lose")]
        ]
    elif emoji == "🎯":
        text = base_text + "🎯 **Дартс · выбери исход!**\n. . . . . . . . . . . . . . . . . .\n" + f"💸 **Ставка:** {u['bet']} m₽\n\n🔰 **Коэффициенты:**\n🔴 Красное (x1.94)\n⚪ Белое (x2.9)\n🎯 Центр (x5.8)\n😯 Мимо (x5.8)"
        rows = [
            [InlineKeyboardButton(text="🔴 Красное", callback_data="bet_🎯_r"), InlineKeyboardButton(text="⚪ Белое", callback_data="bet_🎯_w")],
            [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_🎯_c"), InlineKeyboardButton(text="😯 Мимо", callback_data="bet_🎯_m")]
        ]
    elif emoji == "🎳":
        text = base_text + "🎳 **Боулинг · выбери исход!**\n. . . . . . . . . . . . . . . . . .\n" + f"💸 **Ставка:** {u['bet']} m₽\n\n🔰 **Коэффициенты:**\n1 - 5 кегли (x5.8)\n🎳 Страйк (x5.8)\n😟 Мимо (x5.8)"
        rows = [
            [InlineKeyboardButton(text="1 кегля", callback_data="bet_🎳_1"), InlineKeyboardButton(text="3 кегли", callback_data="bet_🎳_3")],
            [InlineKeyboardButton(text="4 кегли", callback_data="bet_🎳_4"), InlineKeyboardButton(text="5 кегель", callback_data="bet_🎳_5")],
            [InlineKeyboardButton(text="🎳 Страйк", callback_data="bet_🎳_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="bet_🎳_0")]
        ]
    elif emoji == "🎲":
        text = base_text + "🍀 **Кубик · выбери режим!**\n. . . . . . . . . . . . . . . . . .\n" + f"💸 **Ставка:** {u['bet']} m₽"
        rows = [
            [InlineKeyboardButton(text=str(i), callback_data=f"bet_🎲_{i}") for i in range(1, 4)],
            [InlineKeyboardButton(text=str(i), callback_data=f"bet_🎲_{i}") for i in range(4, 7)],
            [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="bet_🎲_e"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="bet_🎲_o")],
            [InlineKeyboardButton(text="= Равно 3 x5.8", callback_data="bet_🎲_3")],
            [InlineKeyboardButton(text="➕ Больше 3 x1.94", callback_data="bet_🎲_b"), InlineKeyboardButton(text="➖ Меньше 3 x2.9", callback_data="bet_🎲_s")]
        ]
    else: # Слот-машина
        text = base_text + "🎰 **Слоты · Испытай удачу!**"
        rows = [[InlineKeyboardButton(text="🎰 Крутить", callback_data="bet_🎰_go")]]

    rows.append([InlineKeyboardButton(text="◀️ назад", callback_data="to_main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="Markdown")

# --- ОБРАБОТКА СТАВКИ И РЕЗУЛЬТАТА ---
@dp.callback_query(F.data.startswith("bet_"))
async def play_game(callback: types.CallbackQuery):
    _, emoji, choice = callback.data.split("_")
    u = get_user(callback.from_user.id)
    
    # Визуальный эффект "броска"
    msg = await callback.message.answer_dice(emoji=emoji)
    val = msg.dice.value
    
    await asyncio.sleep(4) # Ждем пока анимация докрутится
    
    # Простая логика выигрыша (для примера)
    win = random.choice([True, False]) # Тут можно прописать реальную проверку val
    
    if win:
        u['bal'] += int(u['bet'] * 2)
        await callback.message.answer(f"✅ Вы выиграли! Баланс: {u['bal']} m₽")
    else:
        u['bal'] -= u['bet']
        await callback.message.answer(f"❌ Проигрыш! Баланс: {u['bal']} m₽")
    
    # Возвращаем главное меню
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.answer(t, reply_markup=k, parse_mode="Markdown")

# --- МИНЫ (КАК НА 1-М СКРИНШОТЕ) ---
@dp.callback_query(F.data == "mines_start")
async def start_mines_game(callback: types.CallbackQuery):
    uid = callback.from_user.id
    mines = random.sample(range(25), 3) # 3 мины
    user_db[uid]['game'] = {'mines': mines, 'open': []}
    await render_mines_grid(callback.message, uid)

async def render_mines_grid(message, uid):
    game = user_db[uid]['game']
    btns = []
    for i in range(0, 25, 5):
        row = []
        for j in range(i, i + 5):
            char = "💎" if j in game['open'] else "❓"
            row.append(InlineKeyboardButton(text=char, callback_data=f"hit_{j}"))
        btns.append(row)
    btns.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="to_main")])
    await message.edit_text("💣 **Мины Бот**\nУгадывай кристаллы!", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("hit_"))
async def hit_mine(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    uid = callback.from_user.id
    game = user_db[uid]['game']
    
    if idx in game['mines']:
        await callback.message.edit_text("💥 БАБАХ! Вы проиграли.")
        await asyncio.sleep(2)
        t, k = get_main_menu(uid)
        await callback.message.answer(t, reply_markup=k)
    else:
        game['open'].append(idx)
        await render_mines_grid(callback.message, uid)

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.message()
async def start_anyway(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
