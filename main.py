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

def get_user(uid):
    if uid not in user_db:
        user_db[uid] = {'bal': 1000, 'bet': 10, 'game': None}
    return user_db[uid]

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu(uid):
    u = get_user(uid)
    text = f"🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** {u['bal']} m₽\n💸 **Ставка:** {u['bet']} m₽\n\n👇 *Выбери игру и начинай!*"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"sub_{e}") for e in ["⚽", "🏀", "🎯", "🎳", "🎲", "🎰"]],
        [InlineKeyboardButton(text="🚀 Кейсы", callback_data="tab_cases"), InlineKeyboardButton(text="Режимы 💣", callback_data="mines_settings")],
        [InlineKeyboardButton(text="🕹 Играть в WEB", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="ch_bet")]
    ])
    return text, kb

# --- ПОДМЕНЮ ИГР (КАК НА СКРИНШОТАХ) ---
@dp.callback_query(F.data.startswith("sub_"))
async def show_submenu(callback: types.CallbackQuery):
    emoji = callback.data.split("_")[1]
    u = get_user(callback.from_user.id)
    text = f"👤 **Рамиль**\n{emoji} **Игра: {emoji}**\n...\n💸 **Ставка:** {u['bet']} m₽"
    
    rows = []
    if emoji == "⚽":
        rows = [[InlineKeyboardButton(text="⚽ Гол - x1.6", callback_data="play_⚽_win")],
                [InlineKeyboardButton(text="🥅 Мимо - x2.4", callback_data="play_⚽_lose")]]
    elif emoji == "🏀":
        rows = [[InlineKeyboardButton(text="🏀 Попадание - x2.4", callback_data="play_🏀_win")],
                [InlineKeyboardButton(text="🙈 Мимо - x1.6", callback_data="play_🏀_lose")]]
    elif emoji == "🎯":
        text += "\n\n🔰 **Коэффициенты:**\n🔴 Красное (x1.94)\n⚪ Белое (x2.9)\n🎯 Центр (x5.8)"
        rows = [[InlineKeyboardButton(text="🔴 Красное", callback_data="play_🎯_red"), InlineKeyboardButton(text="⚪ Белое", callback_data="play_🎯_white")],
                [InlineKeyboardButton(text="🎯 Центр", callback_data="play_🎯_center"), InlineKeyboardButton(text="😯 Мимо", callback_data="play_🎯_miss")]]
    elif emoji == "🎳":
        rows = [[InlineKeyboardButton(text="1 кегля", callback_data="play_🎳_1"), InlineKeyboardButton(text="3 кегли", callback_data="play_🎳_3")],
                [InlineKeyboardButton(text="4 кегли", callback_data="play_🎳_4"), InlineKeyboardButton(text="5 кегель", callback_data="play_🎳_5")],
                [InlineKeyboardButton(text="🎳 Страйк", callback_data="play_🎳_6"), InlineKeyboardButton(text="😟 Мимо", callback_data="play_🎳_0")]]
    elif emoji == "🎲":
        rows = [[InlineKeyboardButton(text=str(i), callback_data=f"play_🎲_{i}") for i in range(1, 4)],
                [InlineKeyboardButton(text=str(i), callback_data=f"play_🎲_{i}") for i in range(4, 7)],
                [InlineKeyboardButton(text="⚖️ Чётный x1.94", callback_data="play_🎲_even"), InlineKeyboardButton(text="🔰 Нечётный x1.94", callback_data="play_🎲_odd")]]
    
    rows.append([InlineKeyboardButton(text="⬅️ назад", callback_data="to_main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

# --- ЛОГИКА ИГРЫ С ДАЙСАМИ ---
@dp.callback_query(F.data.startswith("play_"))
async def execute_play(callback: types.CallbackQuery):
    _, emoji, choice = callback.data.split("_")
    u = get_user(callback.from_user.id)
    
    if u['bal'] < u['bet']: return await callback.answer("Недостаточно m₽")
    
    u['bal'] -= u['bet']
    msg = await callback.message.answer_dice(emoji=emoji)
    val = msg.dice.value
    await asyncio.sleep(3.5) # Ждем анимацию
    
    win = False
    # Пример логики (можно настроить под себя)
    if emoji == "⚽" and ((choice == "win" and val >= 3) or (choice == "lose" and val < 3)): win = True
    elif emoji == "🏀" and ((choice == "win" and val >= 4) or (choice == "lose" and val < 4)): win = True
    
    if win:
        prize = int(u['bet'] * 2)
        u['bal'] += prize
        await callback.message.answer(f"✅ Победа! +{prize} m₽")
    else:
        await callback.message.answer("❌ Проигрыш!")
    
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.answer(t, reply_markup=k, parse_mode="Markdown")

# --- МИНЫ (КАК НА СКРИНШОТЕ 1) ---
@dp.callback_query(F.data == "mines_settings")
async def mines_setup(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="3x3 (2 мины)", callback_data="sm_3_2")],
        [InlineKeyboardButton(text="5x5 (10 мин)", callback_data="sm_5_10")],
        [InlineKeyboardButton(text="« Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("💣 **ВЫБЕРИ РЕЖИМ МИН:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("sm_"))
async def start_mines(callback: types.CallbackQuery):
    _, size, count = map(int, callback.data.split("_")[1:])
    u = get_user(callback.from_user.id)
    u['bal'] -= u['bet']
    u['game'] = {'mines': random.sample(range(size*size), count), 'open': [], 'size': size, 'win': u['bet']}
    await render_mines(callback.message, callback.from_user.id)

async def render_mines(message, uid):
    g = user_db[uid]['game']
    size = g['size']
    btns = []
    for i in range(0, size*size, size):
        btns.append([InlineKeyboardButton(text="💎" if j in g['open'] else "❓", callback_data=f"hit_{j}") for j in range(i, i+size)])
    btns.append([InlineKeyboardButton(text="Забрать выигрыш ✅", callback_data="m_cash")])
    await message.edit_text(f"💣 Поле {size}x{size}. Множитель: x{len(g['open'])+1}", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("hit_"))
async def handle_hit(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    u = get_user(callback.from_user.id)
    g = u['game']
    if idx in g['mines']:
        u['game'] = None
        await callback.message.edit_text("💥 **БОМБА!** Вы проиграли.")
        await asyncio.sleep(2)
        t, k = get_main_menu(callback.from_user.id)
        await callback.message.answer(t, reply_markup=k)
    else:
        g['open'].append(idx)
        await render_mines(callback.message, callback.from_user.id)

@dp.callback_query(F.data == "to_main")
async def to_main(callback: types.CallbackQuery):
    t, k = get_main_menu(callback.from_user.id)
    await callback.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    t, k = get_main_menu(message.from_user.id)
    await message.answer(t, reply_markup=k, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
