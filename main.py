import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ТОКЕН - СЮДА (после отзыва старого, вставь НОВЫЙ)
TOKEN = "8034796055:AAFBzzyK3IFs9BsKx02Al-fPCXSIFJ3uV90"

# Включим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Словарь с ответами на разные типы сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    # 1. Если прислали премиум-эмодзи (специальный апдейт)
    if message.text and message.text.startswith("👑"):
        await message.reply_text(f"🎉 Ого! Ты прислал премиум-эмодзи: {message.text}\nСпасибо, {user.first_name}!")
        return
    
    # 2. Обычный текст
    if message.text:
        text_lower = message.text.lower()
        if "привет" in text_lower:
            await message.reply_text(f"Привет, {user.first_name}! 👋")
        elif "как дела" in text_lower:
            await message.reply_text("У меня всё отлично, а у тебя? 😊")
        else:
            await message.reply_text(f"Ты написал: «{message.text}»\nЯ тебя понял, {user.first_name}!")
    
    # 3. Стикеры (включая премиум-стикеры)
    elif message.sticker:
        premium_note = " (это премиум-стикер! ✨)" if message.sticker.is_premium else ""
        await message.reply_text(
            f"🎨 Классный стикер{premium_note}!\n"
            f"Emoji: {message.sticker.emoji or 'нет'}"
        )
    
    # 4. Фото
    elif message.photo:
        await message.reply_text(f"📸 Красивое фото! Спасибо, {user.first_name}!")
    
    # 5. Голосовое сообщение
    elif message.voice:
        await message.reply_text("🎙 Услышал твой голос! (бот не умеет распознавать речь, но спасибо)")
    
    # 6. Видео
    elif message.video:
        await message.reply_text("🎬 Видео получено! Интересно, что там?")
    
    # 7. Аудио/музыка
    elif message.audio:
        await message.reply_text("🎵 Музыка! Классный трек!")
    
    # 8. Документ/файл
    elif message.document:
        await message.reply_text(f"📄 Файл «{message.document.file_name}» получен!")
    
    # 9. Геолокация
    elif message.location:
        await message.reply_text("📍 Ага, скинул геолокацию! (но я не слежу, честно)")
    
    # 10. Контакт
    elif message.contact:
        await message.reply_text(f"📞 Контакт: {message.contact.first_name} {message.contact.last_name or ''}")
    
    # 11. Опрос
    elif message.poll:
        await message.reply_text("📊 Опрос получен! Результаты узнаю позже.")
    
    # 12. Всё остальное (dice, game, invoice и т.д.)
    else:
        await message.reply_text(f"✅ Получил твоё сообщение, {user.first_name}! (это какой-то особый тип)")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот-ответчик. Пиши мне что угодно:\n"
        "• Текст\n"
        "• Стикеры (включая премиум)\n"
        "• Фото, видео, голосовые\n"
        "• Премиум-эмодзи (коронованные)\n\n"
        "Я всё равно отвечу! 😎"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Что я умею?\n"
        "- Отвечать на любые сообщения\n"
        "- Распознавать премиум-эмодзи 👑\n"
        "- Отвечать на премиум-стикеры ✨\n"
        "- Реагировать на фото, видео, голосовые\n\n"
        "Просто напиши мне что-нибудь!"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Обработчик на ВСЕ сообщения (кроме команд)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Бот запущен и слушает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
