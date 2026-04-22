import telebot
import os

# Твой токен от BotFather
TOKEN = "8359920618:AAFpuDjkXwbArbuC3VtaevWMIYXuBamvSt0"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Бот успешно запущен и работает! 🚀")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
