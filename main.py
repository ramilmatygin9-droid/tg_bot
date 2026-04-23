import asyncio
import random
import hashlib
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных состояний игры
games = {}

def get_header(user: types.User):
    return (f"👤 {user.first_name} | ID: `{user.id}`\n"
            f"🏆 Ваш уровень: 1\n"
            f"💰 Баланс: 1000 m¢\n"
            f"────────────────")

# --- ГЛАВНОЕ МЕНЮ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀", callback_data="g_b"), InlineKeyboardButton(text="⚽", callback_data="g_f"),
         InlineKeyboardButton(text="🎯", callback_data="g_d"), InlineKeyboardButton(text="🎳", callback_data="g_bw"),
         InlineKeyboardButton(text="🎲", callback_data="g_dice"), InlineKeyboardButton(text="🎰", callback_data="g_s")],
        [InlineKeyboardButton(text="🚀 Быстрые", callback_data="m_fast"), InlineKeyboardButton(text="Режимы 💣", callback_data="m_modes")]
    ])

# --- МЕНЮ БЫСТРЫХ ИГР ---
@dp.callback_query(F.data == "m_fast")
async def fast_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="none"), InlineKeyboardButton(text="🎰 Монета", callback_data="none")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="prep_mines"), InlineKeyboardButton(text="🚀 Краш", callback_data="none")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n🚀 **Быстрые игры**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ВЫБОР КОЛИЧЕСТВА МИН ---
@dp.callback_query(F.data == "prep_mines")
async def setup_mines(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="💣 3", callback_data="st_m_3"), InlineKeyboardButton(text="💣 5", callback_data="st_m_5"), InlineKeyboardButton(text="💣 10", callback_data="st_m_10")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fast")]
    ]
    await call.message.edit_text(f"{get_header(call.from_user)}\n💣 **Мины**\nВыбери количество бомб:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- ГЕНЕРАЦИЯ ПОЛЯ 5х5 ---
def create_mines_kb(uid):
    game = games[uid]
    kb = []
    for y in range(5):
        row = []
        for x in range(5):
            pos = f"{x}_{y}"
            if pos in game['open']:
                row.append(InlineKeyboardButton(text="💎", callback_data="none"))
            else:
                row.append(InlineKeyboardButton(text="🔹", callback_data=f"click_{pos}"))
        kb.append(row)
    
    kb.append([InlineKeyboardButton(text=f"📥 Забрать {game['current_win']} m¢", callback_data="m_cashout")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- СТАРТ ИГРЫ МИНЫ ---
@dp.callback_query(F.data.startswith("st_m_"))
async def start_mines(call: types.CallbackQuery):
    count = int(call.data.split("_")[2])
    uid = call.from_user.id
    
    # Генерируем случайные мины
    all_pos = [f"{x}_{y}" for x in range(5) for y in range(5)]
    mine_pos = random.sample(all_pos, count)
    
    games[uid] = {
        "mines": mine_pos,
        "open": [],
        "m_count": count,
        "current_win": 10,
        "hash": hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]
    }
    
    await call.message.edit_text(
        f"{get_header(call.from_user)}\n💣 **Игра началась!**\nМин: {count}\n🛡 Hash: `{games[uid]['hash']}`",
        reply_markup=create_mines_kb(uid),
        parse_mode="Markdown"
    )

# --- КЛИК ПО ЯЧЕЙКЕ ---
@dp.callback_query(F.data.startswith("click_"))
async def handle_click(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in games: return
    
    pos = call.data.split("_")[1] + "_" + call.data.split("_")[2]
    game = games[uid]
    
    if pos in game['mines']:
        # ВЗРЫВ
        del games[uid]
        await call.message.edit_text(f"{get_header(call.from_user)}\n💥 **БА-БАХ! Вы подорвались!**", 
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="prep_mines")]]), 
                                     parse_mode="Markdown")
    else:
        # АЛМАЗ
        game['open'].append(pos)
        game['current_win'] = int(game['current_win'] * 1.5) # Множитель за каждый алмаз
        await call.message.edit_reply_markup(reply_markup=create_mines_kb(uid))

# --- КЭШАУТ (ЗАБРАТЬ ДЕНЬГИ) ---
@dp.callback_query(F.data == "m_cashout")
async def cashout(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in games: return
    win = games[uid]['current_win']
    del games[uid]
    await call.message.edit_text(f"{get_header(call.from_user)}\n💰 **Выигрыш забран!**\nВы получили: {win} m¢", 
                                 reply_markup=main_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(get_header(call.from_user), reply_markup=main_kb(), parse_mode="Markdown")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(get_header(message.from_user), reply_markup=main_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
