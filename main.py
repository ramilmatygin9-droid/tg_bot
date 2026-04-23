import asyncio
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "ТВОЙ_ТОКЕН_БОТА"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных текущих игр
active_games = {}

def get_header(user: types.User):
    # Заглушка баланса, в идеале брать из БД
    return (f"👤 {user.first_name} | ID: `{user.id}`\n"
            f"🏆 Ваш уровень: 1\n"
            f"💰 Баланс: 1000 m¢\n"
            f"────────────────")

# --- КЛАВИАТУРЫ ---

def get_mines_setup_kb():
    # Выбор количества мин как на видео
    buttons = [
        [InlineKeyboardButton(text=f"💣 {i}", callback_data=f"setup_mines_{i}") for i in range(3, 6)],
        [InlineKeyboardButton(text=f"💣 {i}", callback_data=f"setup_mines_{i}") for i in range(10, 13)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_mines_field_kb(uid, finished=False):
    game = active_games[uid]
    kb = []
    for y in range(5):
        row = []
        for x in range(5):
            pos = f"{x}_{y}"
            if pos in game['opened']:
                text = "💥" if pos in game['mines_pos'] else "💎"
            elif finished and pos in game['mines_pos']:
                text = "💣" # Показываем где были мины при проигрыше
            else:
                text = "🔹"
            row.append(InlineKeyboardButton(text=text, callback_data=f"mine_click_{pos}"))
        kb.append(row)
    
    if not finished:
        kb.append([InlineKeyboardButton(text=f"📥 Забрать {game['cur_win']:.2f} m¢", callback_data="mine_stop")])
    else:
        kb.append([InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_mines")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ЛОГИКА ИГРЫ ---

@dp.callback_query(F.data == "game_mines")
async def mines_start(call: types.CallbackQuery):
    await call.message.edit_text(
        f"{get_header(call.from_user)}\n💣 **Мины**\nВыбери количество мин на поле:",
        reply_markup=get_mines_setup_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("setup_mines_"))
async def start_game_with_mines(call: types.CallbackQuery):
    uid = call.from_user.id
    count = int(call.data.split("_")[2])
    
    # Генерация случайных позиций мин
    all_positions = [f"{x}_{y}" for x in range(5) for y in range(5)]
    mines_pos = random.sample(all_positions, count)
    
    active_games[uid] = {
        "mines_count": count,
        "mines_pos": mines_pos,
        "opened": [],
        "cur_win": 10.0, # Начальная ставка
        "multiplier": 1.2 + (count * 0.15) # Пример роста коэфа
    }
    
    await call.message.edit_text(
        f"{get_header(call.from_user)}\n💣 **Мины: Игра началась!**\nСделано ходов: 0\nМножитель: x1.0",
        reply_markup=get_mines_field_kb(uid),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("mine_click_"))
async def handle_click(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in active_games: return
    
    pos = call.data.replace("mine_click_", "")
    game = active_games[uid]
    
    if pos in game['opened']:
        return await call.answer("Уже открыто!")

    game['opened'].append(pos)
    
    if pos in game['mines_pos']:
        # ПРОИГРЫШ
        await call.message.edit_text(
            f"{get_header(call.from_user)}\n💥 **КРАХ! Вы подорвались на мине!**",
            reply_markup=get_mines_field_kb(uid, finished=True),
            parse_mode="Markdown"
        )
        del active_games[uid]
    else:
        # ПОПАЛ В АЛМАЗ
        game['cur_win'] = round(game['cur_win'] * game['multiplier'], 2)
        await call.message.edit_text(
            f"{get_header(call.from_user)}\n💎 **Отлично! Алмаз найден.**\nСделано ходов: {len(game['opened'])}\nВыплата: {game['cur_win']} m¢",
            reply_markup=get_mines_field_kb(uid),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "mine_stop")
async def stop_game(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in active_games: return
    
    win = active_games[uid]['cur_win']
    # Тут можно добавить код начисления win в БД
    
    await call.message.edit_text(
        f"{get_header(call.from_user)}\n💰 **Победа! Вы забрали {win} m¢**",
        reply_markup=main_menu_kb(), # Возврат в главное меню
        parse_mode="Markdown"
    )
    del active_games[uid]

# --- ГЛАВНОЕ МЕНЮ (Заглушка) ---
@dp.callback_query(F.data == "to_main")
async def to_main(call: types.CallbackQuery):
    await call.message.edit_text(f"{get_header(call.from_user)}\nГлавное меню:", reply_markup=main_menu_kb(), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
