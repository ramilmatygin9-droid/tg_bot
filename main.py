import os
import requests
from telebot import TeleBot, types
from dublib.CLI.Terminalyzer import Command, ParametersTypes, Terminalyzer
from dublib.Methods.Filesystem import MakeRootDirectories, ReadJSON
from dublib.Methods.System import CheckPythonMinimalVersion, Clear
from dublib.TelebotUtils.Users import UsersManager
from dublib.CLI.TextStyler import TextStyler

# Импорт локальных модулей проекта
from Source.UI.Menu import Decorators, ReplyKeyboards
from Source.Core.Mailing import Mailer
from Source.CLI import Interaction

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ <<<<< #
#==========================================================================================#

CheckPythonMinimalVersion(3, 10)
MakeRootDirectories(["Data/Sessions", "Data/Temp"])
Settings = ReadJSON("Settings.json")

# Безопасная инициализация бота
BOT_TOKEN = Settings.get("token")
if not BOT_TOKEN or ":" not in BOT_TOKEN:
    print(TextStyler("Ошибка: Токен бота не найден в Settings.json или имеет неверный формат!").colorize.red)
    exit(1)

Bot = TeleBot(BOT_TOKEN)
Users = UsersManager("Data/Users")

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ <<<<< #
#==========================================================================================#

def save_telegram_file(user_id: int, file_id: str, subfolder: str = "Attachments"):
    """Скачивает файл из Telegram и возвращает его имя."""
    file_info = Bot.get_file(file_id)
    filename = file_info.file_path.split("/")[-1]
    file_url = f"https://api.telegram.org/file/bot{Bot.token}/{file_info.file_path}"
    
    directory = f"Data/Temp/{user_id}/{subfolder}"
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        with open(f"{directory}/{filename}", "wb") as f:
            f.write(response.content)
        return filename
    return None

#==========================================================================================#
# >>>>> ОБРАБОТЧИКИ КОМАНД <<<<< #
#==========================================================================================#

@Bot.message_handler(commands=["start"])
def bot_start(message: types.Message):
    user = Users.auth(message.from_user)
    user.set_property("message", None, force=False)
    user.set_property("attachments", list(), force=False)

    # Проверка на админа или ввод пароля
    password_match = message.text.split()[-1] == Settings.get("password") if len(message.text.split()) > 1 else False

    if user.has_permissions("admin") or password_match:
        if password_match: user.add_permissions("admin")
        
        Bot.send_message(
            chat_id=message.chat.id,
            text=f"🔒 Доступ <b>разрешён</b>. Ваш ID: <code>{user.id}</code>.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboards.menu()
        )
    else:
        Bot.send_message(
            chat_id=message.chat.id,
            text="🔒 Доступ <b>запрещён</b>. Введите пароль (пример: /start password).",
            parse_mode="HTML"
        )

# Регистрация кнопок меню из декораторов
Decorators.reply_buttons(Bot, Users)

#==========================================================================================#
# >>>>> ПРИЕМ КОНТЕНТА <<<<< #
#==========================================================================================#

@Bot.message_handler(content_types=["text"])
def handle_text(message: types.Message):
    user = Users.auth(message.from_user)
    if user.expected_type == "message":
        user.set_property("message", message.html_text)
        user.set_expected_type(None)
        Bot.send_message(message.chat.id, "✅ Текст сообщения сохранён.")

@Bot.message_handler(content_types=["photo", "video"])
def handle_media(message: types.Message):
    user = Users.auth(message.from_user)
    media_type = message.content_type # 'photo' или 'video'
    
    if user.expected_type == media_type:
        user.set_expected_type(None)
        Bot.send_chat_action(message.chat.id, "upload_document")
        
        file_id = message.photo[-1].file_id if media_type == "photo" else message.video.file_id
        filename = save_telegram_file(user.id, file_id)
        
        if filename:
            attachments = user.get_property("attachments")
            attachments.append({"filename": filename, "type": media_type})
            user.set_property("attachments", attachments)
            
            Bot.send_message(
                message.chat.id, 
                f"✅ {media_type.capitalize()} добавлено.",
                reply_markup=ReplyKeyboards.message(user)
            )
        else:
            Bot.send_message(message.chat.id, "❌ Ошибка при загрузке файла.")

@Bot.message_handler(content_types=["document"])
def handle_docs(message: types.Message):
    user = Users.auth(message.from_user)
    if user.expected_type == "targets":
        user.set_expected_type(None)
        filename = save_telegram_file(user.id, message.document.file_id, subfolder="")
        
        if filename:
            try:
                # Переименовываем в targets.xlsx для совместимости с Mailer
                os.replace(f"Data/Temp/{user.id}/{filename}", f"Data/Temp/{user.id}/targets.xlsx")
                Mailer().parse_targets_from_excel(user)
                Bot.send_message(message.chat.id, "✅ База получателей успешно загружена.")
            except Exception as e:
                Bot.send_message(message.chat.id, f"❌ Ошибка обработки Excel: {e}")

#==========================================================================================#
# >>>>> ЗАПУСК <<<<< #
#==========================================================================================#

if __name__ == "__main__":
    Clear()
    print(TextStyler(f"Бот запущен!").colorize.green)
    Bot.infinity_polling()
