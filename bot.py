import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация
TOKEN = "8156857401:AAF9qTQLD1GbAXgef_IjX7f2glkLofVH0Wk"

# Твои Premium ID
PICKAXE_ID = "5197371802136892976"   
MONEY_BAG_ID = "5206223871467878339"  
CASH_ID = "5206599371868631162"       
BALANCE_ID = "5924587830675249107"
SUPPORT_ID = "5924712865763170353"
HEART_ID = "5470092785094765546"

bot = Bot(token=TOKEN)
dp = Dispatcher()

players = {}

# --- УСТАНОВКА МЕНЮ ---
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/start", description="🏠 Главное меню"),
        BotCommand(command="/mine", description="⛏ Начать копать"),
        BotCommand(command="/balance", description="💰 Баланс"),
        BotCommand(command="/support", description="🎧 Тех. поддержка")
    ]
    await bot.set_my_commands(main_menu_commands, scope=BotCommandScopeDefault())

# --- ОБНОВЛЕННОЕ ПРИВЕТСТВИЕ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji><b>Добро пожаловать в Майнер бот</b><tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji>\n\n'
        f'Используй /mine или меню чтобы начать копать руду',
        parse_mode="HTML"
    )

@dp.message(Command("mine"))
async def mine_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in players: players[user_id] = 0

    wait_time = random.randint(5, 12)
    status_msg = await message.answer(
        f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Копаем...</b>\n⏳ Осталось: {wait_time} сек.',
        parse_mode="HTML"
    )
    
    for seconds_left in range(wait_time - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(
                f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Работа кипит!</b>\n⏳ Осталось: {seconds_left} сек.',
                parse_mode="HTML"
            )
        except: pass
    
    reward = random.randint(300, 1000)
    players[user_id] += reward
    await status_msg.delete()
    
    await message.answer(
        f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Добыча: +{reward}</b>\n'
        f'<tg-emoji emoji-id="{BALANCE_ID}">💎</tg-emoji> Баланс: <b>{players[user_id]}</b>',
        parse_mode="HTML"
    )

@dp.message(Command("balance"))
async def bal_cmd(message: types.Message):
    balance = players.get(message.from_user.id, 0)
    await message.answer(
        f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> <b>Ваш баланс:</b> {balance} монет',
        parse_mode="HTML"
    )

@dp.message(Command("support"))
async def support_cmd(message: types.Message):
    await message.answer(
        f'<tg-emoji emoji-id="{SUPPORT_ID}">🎧</tg-emoji> <b>Поддержка</b>\n\n'
        f'Есть вопросы? Пиши админу: @твой_ник',
        parse_mode="HTML"
    )

async def main():
    await set_main_menu(bot)
    print("Майнер бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
