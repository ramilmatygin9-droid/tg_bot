import logging
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Включим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Токен бота (вставь свой)
TOKEN = "8034796055:AAFrpMOUowWvo6W3kGBsoMiq9RVjsaM2Qig"

# Состояния для ConversationHandler
GUESSING = 1

# Хранилище загаданных чисел для каждого пользователя
user_games = {}

# Клавиатура с числами 1–9 для удобства (можно расширить)
def get_number_keyboard():
    buttons = [[KeyboardButton(str(i)) for i in range(1, 10)],
               [KeyboardButton("0"), KeyboardButton("Сдаюсь"), KeyboardButton("Новая игра")]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🎮\n\n"
        "Я загадаю число от 1 до 100, а ты попробуй угадать.\n"
        "Напиши /new_game, чтобы начать новую игру.\n"
        "В любой момент можешь написать 'Сдаюсь' или /give_up.",
        reply_markup=get_number_keyboard()
    )

# Начать новую игру
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    secret_number = random.randint(1, 100)
    user_games[user_id] = secret_number
    await update.message.reply_text(
        "🎲 Я загадал число от 1 до 100.\n"
        "Попробуй угадать! Введи своё число (или нажми на кнопку).",
        reply_markup=get_number_keyboard()
    )
    return GUESSING

# Обработка угадывания
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Проверка на "Сдаюсь"
    if text.lower() == "сдаюсь":
        secret = user_games.get(user_id)
        if secret is None:
            await update.message.reply_text("Нет активной игры. Начни новую: /new_game")
            return ConversationHandler.END
        await update.message.reply_text(
            f"😔 Жаль! Я загадал {secret}.\n"
            "Чтобы сыграть снова, набери /new_game"
        )
        del user_games[user_id]
        return ConversationHandler.END

    # Проверка на "Новая игра" прямо из игры
    if text.lower() == "новая игра":
        await new_game(update, context)
        return GUESSING

    # Пытаемся преобразовать в число
    try:
        guess_num = int(text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи целое число от 1 до 100 (или нажми на кнопку).")
        return GUESSING

    # Проверяем, есть ли игра для этого пользователя
    secret = user_games.get(user_id)
    if secret is None:
        await update.message.reply_text("Нет активной игры. Начни новую: /new_game")
        return ConversationHandler.END

    # Сравниваем числа
    if guess_num < 1 or guess_num > 100:
        await update.message.reply_text("Число должно быть от 1 до 100. Попробуй ещё раз.")
        return GUESSING

    if guess_num < secret:
        await update.message.reply_text("📈 Больше! Попробуй ещё.")
    elif guess_num > secret:
        await update.message.reply_text("📉 Меньше! Попробуй ещё.")
    else:
        await update.message.reply_text(
            f"🎉 Поздравляю! Ты угадал число {secret}!\n"
            "Хочешь сыграть ещё? Напиши /new_game"
        )
        del user_games[user_id]
        return ConversationHandler.END

    return GUESSING

# Команда /give_up — сдаться в игре
async def give_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    secret = user_games.get(user_id)
    if secret is None:
        await update.message.reply_text("Нет активной игры. Начни новую: /new_game")
        return ConversationHandler.END
    await update.message.reply_text(
        f"🤷 Ты сдался. Я загадал {secret}.\n"
        "Напиши /new_game, чтобы начать заново."
    )
    del user_games[user_id]
    return ConversationHandler.END

# Отмена (если вдруг нужно выйти из диалога)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Игра прервана. Напиши /new_game, чтобы начать новую.")
    return ConversationHandler.END

# Главная функция
def main():
    app = Application.builder().token(TOKEN).build()

    # ConversationHandler управляет состояниями игры
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new_game", new_game)],
        states={
            GUESSING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guess),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("give_up", give_up)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
