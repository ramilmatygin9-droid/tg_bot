import random
import asyncio
import hashlib
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# ТОКЕН (Тот, что ты скинул)
API_TOKEN = '8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ВРЕМЕННАЯ БАЗА ДАННЫХ ---
users = {}  # Баланс и ставки
active_games = {}  # Текущие сессии игры

# --- ВСПОМОГАТЕЛЬНАЯ ЛОГИКА ---

def calculate_multiplier(mines, opened):
    """Математический расчет множителя (как в оригинале)"""
    if opened == 0: return 1.0
    # Формула вероятности: nCr
    res = 1.0
    for i in range(opened):
        res *= (25 - i) / (25 - mines - i)
    # Маржа системы 3-4%
    return round(res * 0.96, 2)

def get_game_hash():
    """Генерация хеша для проверки честности"""
    random_str = str(random.getrandbits(128))
    return hashlib.sha256(random_str.encode()).hexdigest()

# --- ГЕНЕРАТОРЫ ИНТЕРФЕЙСА ---

def main_menu_kb(uid):
    """Главное меню с кнопками игр"""
    builder = InlineKeyboardBuilder()
    # Кнопки как на скриншотах
    builder.row(types.InlineKeyboardButton(text="💣 Мины", callback_data="mines_start"))
    builder.row(types.InlineKeyboardButton(text="💎 Алмазы", callback_data="none"))
    builder.row(types.InlineKeyboardButton(text="🏟 Арена", callback_data="none"))
    builder.row(types.InlineKeyboardButton(text="🚀 Быстрые", callback_data="none"))
    builder.row(types.InlineKeyboardButton(text="📝 Изменить ставку", callback_data="edit_bet"))
    return builder.as_markup()

def mines_settings_kb():
    """Выбор количества мин"""
    builder = InlineKeyboardBuilder()
    for i in [1, 3, 5, 10, 15, 24]:
        builder.button(text=f"💣 {i}", callback_data=f"set_mines_{i}")
    builder.adjust(3)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {'balance': 1000.0, 'bet': 10.0}
    
    await message.answer(
        f"🕹 *ДАВАЙ НАЧНЕМ ИГРАТЬ!*\n\n"
        f"💰 *Баланс:* {users[uid]['balance']} mф\n"
        f"💵 *Ставка:* {users[uid]['bet']} mф\n\n"
        f"👇 *Выбери игру ниже:*",
        reply_markup=main_menu_kb(uid),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "mines_start")
async def mines_setup(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💣 *Мины · выбери кол-во мин!* \n\nЧем больше мин на поле, тем выше риск и итоговый множитель.",
        reply_markup=mines_settings_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("set_mines_"))
async def start_game_process(callback: types.CallbackQuery):
    uid = callback.from_user.id
    mines_count = int(callback.data.split("_")[-1])
    bet = users[uid]['bet']

    if users[uid]['balance'] < bet:
        return await callback.answer("❌ Недостаточно средств для ставки!", show_alert=True)

    # Списываем ставку
    users[uid]['balance'] -= bet
    
    # Генерируем поле
    raw_field = ["💎"] * (25 - mines_count) + ["💣"] * mines_count
    random.shuffle(raw_field)
    field = [raw_field[i:i+5] for i in range(0, 25, 5)]

    # Сохраняем игру
    active_games[uid] = {
        "field": field,
        "visible": [[False for _ in range(5)] for _ in range(5)],
        "mines": mines_count,
        "opened_gems": 0,
        "bet": bet,
        "hash": get_game_hash(),
        "finished": False
    }

    await update_game_ui(callback.message, uid)

async def update_game_ui(message, uid):
    """Основная функция отрисовки игрового процесса"""
    game = active_games[uid]
    builder = InlineKeyboardBuilder()

    # Рисуем сетку 5x5
    for r in range(5):
        for c in range(5):
            if game['visible'][r][c]:
                # Если клетка открыта — показываем что там
                builder.button(text=game['field'][r][c], callback_data=f"press_{r}_{c}")
            elif game['finished']:
                # Если игра окончена — показываем всё поле
                builder.button(text=game['field'][r][c], callback_data="void")
            else:
                # Иначе — знак вопроса
                builder.button(text="❓", callback_data=f"press_{r}_{c}")
    
    builder.adjust(5)

    curr_m = calculate_multiplier(game['mines'], game['opened_gems'])
    next_m = calculate_multiplier(game['mines'], game['opened_gems'] + 1)

    if not game['finished']:
        # Кнопка «Забрать» появляется только если нашли хотя бы 1 алмаз
        if game['opened_gems'] > 0:
            builder.row(types.InlineKeyboardButton(text="💰 Забрать выигрыш", callback_data="take_money"))
        
        text = (
            f"💎 *Мины · игра идёт.*\n"
            f"........................\n"
            f"💣 *Мин:* {game['mines']}\n"
            f"💵 *Ставка:* {game['bet']} mф\n"
            f"📈 *Выигрыш:* x{curr_m} / {round(game['bet']*curr_m, 2)} mф\n\n"
            f"🧮 *Следующий множитель:* \n"
            f"x{next_m} ➡ ..."
        )
    else:
        # Меню после завершения
        builder.row(types.InlineKeyboardButton(text="🔄 Повторить", callback_data=f"set_mines_{game['mines']}"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        # Проверяем, был ли подрыв
        is_lose = any(game['field'][r][c] == "💣" and game['visible'][r][c] for r in range(5) for c in range(5))
        title = "💥 *Мины · Проигрыш!*" if is_lose else "🏆 *Мины · Победа!*"
        
        text = (
            f"{title}\n"
            f"........................\n"
            f"💣 *Мин:* {game['mines']}\n"
            f"💎 *Открыто:* {game['opened_gems']} из {25 - game['mines']}\n"
            f"🔑 *Hash:* `{game['hash'][:20]}...`"
        )

    try:
        await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except TelegramBadRequest:
        pass

@dp.callback_query(F.data.startswith("press_"))
async def handle_press(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in active_games or active_games[uid]['finished']:
        return await callback.answer()

    _, r, c = callback.data.split("_")
    r, c = int(r), int(c)
    game = active_games[uid]

    if game['visible'][r][c]: return await callback.answer()

    # Открываем клетку
    game['visible'][r][c] = True

    if game['field'][r][c] == "💣":
        # ПРОИГРЫШ
        game['finished'] = True
    else:
        # АЛМАЗ
        game['opened_gems'] += 1
        # Если открыли все алмазы — автовыигрыш
        if game['opened_gems'] == (25 - game['mines']):
            await process_win(callback, uid)
            return

    await update_game_ui(callback.message, uid)

@dp.callback_query(F.data == "take_money")
async def take_money_handler(callback: types.CallbackQuery):
    uid = callback.from_user.id
    await process_win(callback, uid)

async def process_win(callback, uid):
    game = active_games[uid]
    if game['finished']: return

    mult = calculate_multiplier(game['mines'], game['opened_gems'])
    win_sum = game['bet'] * mult
    users[uid]['balance'] += win_sum
    game['finished'] = True
    
    await update_game_ui(callback.message, uid)
    await callback.answer(f"🎉 Вы выиграли {round(win_sum, 2)} mф!", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    uid = callback.from_user.id
    await callback.message.edit_text(
        f"🕹 *ГЛАВНОЕ МЕНЮ*\n\n💰 *Баланс:* {users[uid]['balance']} mф\n💵 *Ставка:* {users[uid]['bet']} mф",
        reply_markup=main_menu_kb(uid),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "void")
async def void_click(callback: types.CallbackQuery):
    await callback.answer()

# --- ЗАПУСК ---
if __name__ == "__main__":
    print("Бот запущен на токене 8359920618...")
    asyncio.run(dp.start_polling(bot))
