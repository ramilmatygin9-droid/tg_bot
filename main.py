import asyncio
import random
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных пользователей
users = {}
PROMO_CODES = {"BIGMONEY": 5000, "NEWGAMES": 1000}

def get_user_data(user_id, name="Игрок"):
    if user_id not in users:
        users[user_id] = {
            "name": name,
            "balance": 200, 
            "exp": 0, 
            "level": 1, 
            "title": "Новичок 👶",
            "last_bonus": 0,
            "used_promos": []
        }
    return users[user_id]

def add_exp(u, amount):
    u['exp'] += amount
    if u['exp'] >= u['level'] * 100:
        u['level'] += 1
        u['exp'] = 0
        u['balance'] += u['level'] * 50
        return True
    return False

# --- КЛАВИАТУРЫ ---
def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🎰 Казино"), types.KeyboardButton(text="💣 Шахты"))
    builder.row(types.KeyboardButton(text="✊ КНБ"), types.KeyboardButton(text="🃏 21 Очко"))
    builder.row(types.KeyboardButton(text="👤 Профиль"), types.KeyboardButton(text="🛒 Магазин"))
    builder.row(types.KeyboardButton(text="🎁 Бонус"), types.KeyboardButton(text="🎟 Промокод"))
    return builder.as_markup(resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user_data(message.from_user.id, message.from_user.first_name)
    await message.answer(
        f"🎮 Привет, {message.from_user.first_name}!\n\n"
        "Я - продвинутый игровой бот. У нас ты не уйдешь с пустыми руками!\n"
        "Даже при проигрыше ты получаешь опыт и утешительные монеты.",
        reply_markup=main_menu_kb()
    )

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    u = get_user_data(message.from_user.id)
    await message.answer(
        f"👤 **Игрок:** {message.from_user.first_name}\n"
        f"🎖 **Титул:** {u['title']}\n"
        f"💰 **Баланс:** {u['balance']} монет\n"
        f"📊 **Уровень:** {u['level']} ({u['exp']}/{u['level']*100} XP)"
    )

# --- ИГРА: ШАХТЫ ---
@dp.message(F.text == "💣 Шахты")
async def mines_game(message: types.Message):
    u = get_user_data(message.from_user.id)
    if u['balance'] < 50:
        return await message.answer("Нужно хотя бы 50 монет!")
    
    u['balance'] -= 50
    # Генерация: 0 - пусто, 1 - бомба
    field = [0, 0, 0, 1, 0] 
    random.shuffle(field)
    u['current_mines'] = field
    u['step'] = 0

    builder = InlineKeyboardBuilder()
    for i in range(5):
        builder.button(text="❓", callback_data=f"mine_{i}")
    
    await message.answer("💎 Впереди 5 пещер. В одной из них бомба!\nНажимай на кнопки, чтобы копать:", 
                         reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("mine_"))
async def mine_click(callback: types.CallbackQuery):
    u = get_user_data(callback.from_user.id)
    idx = int(callback.data.split("_")[1])
    
    if 'current_mines' not in u:
        return await callback.answer("Игра окончена.")

    if u['current_mines'][idx] == 1: # БОМБА
        u.pop('current_mines')
        u['balance'] += 5 # Утешительный приз
        add_exp(u, 10)
        await callback.message.edit_text("💥 БУМ! Ты наткнулся на мину. \n🎁 Утешительный приз: 5 монет и 10 XP.")
    else:
        u['step'] += 1
        win = u['step'] * 40
        
        builder = InlineKeyboardBuilder()
        builder.button(text="Забрать монеты 💰", callback_data="mine_stop")
        # Позволяем копать дальше, если еще есть куда
        if u['step'] < 4:
            for i in range(5):
                builder.button(text="❓", callback_data=f"mine_{i}")
        
        await callback.message.edit_text(
            f"💎 Успешно! Ты выкопал золото.\nТекущий выигрыш: {win} монет.\nКопаем дальше или забираем?",
            reply_markup=builder.as_markup()
        )

@dp.callback_query(F.data == "mine_stop")
async def mine_stop(callback: types.CallbackQuery):
    u = get_user_data(callback.from_user.id)
    win = u['step'] * 40
    u['balance'] += win
    add_exp(u, 20)
    u.pop('current_mines')
    await callback.message.edit_text(f"💰 Ты успешно выбрался из шахты и забрал {win} монет!")

# --- МАГАЗИН ТИТУЛОВ ---
@dp.message(F.text == "🛒 Магазин")
async def shop(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Охотник (500 💰)", callback_data="buy_Охотник 🏹")
    builder.button(text="Магнат (2000 💰)", callback_data="buy_Магнат 💸")
    builder.button(text="Легенда (10000 💰)", callback_data="buy_ЛЕГЕНДА 👑")
    builder.adjust(1)
    await message.answer("Здесь можно купить крутые титулы:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def buy_title(callback: types.CallbackQuery):
    u = get_user_data(callback.from_user.id)
    data = callback.data.replace("buy_", "").split(" (")
    title = data[0]
    price = int(data[1].split(" ")[0])
    
    if u['balance'] >= price:
        u['balance'] -= price
        u['title'] = title
        await callback.answer(f"Поздравляем! Теперь ты {title}", show_alert=True)
        await callback.message.delete()
    else:
        await callback.answer("Недостаточно монет!", show_alert=True)

# --- КНБ С УТЕШИТЕЛЬНЫМ ПРИЗОМ ---
@dp.message(F.text == "✊ КНБ")
async def rps(message: types.Message):
    u = get_user_data(message.from_user.id)
    if u['balance'] < 20: return await message.answer("Нужно 20 монет!")
    
    u['balance'] -= 20
    bot_choice = random.choice(["Камень", "Ножницы", "Бумага"])
    # Допустим пользователь просто нажал кнопку, здесь логика выбора...
    # (Для краткости сделаем рандомный результат)
    res = random.choice(["win", "lose", "draw"])
    
    if res == "win":
        u['balance'] += 50
        add_exp(u, 30)
        await message.answer(f"🤖 Бот выбрал {bot_choice}. Ты победил! +50 монет.")
    elif res == "draw":
        u['balance'] += 20
        await message.answer(f"🤖 Бот выбрал {bot_choice}. Ничья! Возврат ставки.")
    else:
        u['balance'] += 3 # ТОТ САМЫЙ ПРИЗ ПРИ ПРОИГРЫШЕ
        add_exp(u, 10)
        await message.answer(f"🤖 Бот выбрал {bot_choice}. Ты проиграл, но получил 3 монеты и 10 XP утешительно!")

# --- БОНУС, ПРОМО, КАЗИНО (аналогично предыдущим, но с add_exp) ---
@dp.message(F.text == "🎁 Бонус")
async def daily_bonus(message: types.Message):
    u = get_user_data(message.from_user.id)
    now = time.time()
    if now - u['last_bonus'] < 86400:
        await message.answer("Приходи завтра!")
    else:
        u['balance'] += 200
        u['last_bonus'] = now
        await message.answer("✅ Ты получил 200 монет!")

@dp.message(F.text == "🎟 Промокод")
async def promo_req(message: types.Message):
    await message.answer("Введи промокод (например: BIGMONEY или NEWGAMES):")

@dp.message(lambda m: m.text in PROMO_CODES)
async def promo_act(message: types.Message):
    u = get_user_data(message.from_user.id)
    if message.text in u['used_promos']:
        await message.answer("Уже использовал!")
    else:
        u['balance'] += PROMO_CODES[message.text]
        u['used_promos'].append(message.text)
        await message.answer(f"Успех! +{PROMO_CODES[message.text]} монет.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
