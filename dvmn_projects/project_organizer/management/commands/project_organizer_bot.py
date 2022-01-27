import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from project_organizer.models import Tg_user, Project_manager, Team, Student
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    message
)
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


(
    MAIN_MENU,
    CREATOR,
    MY_GAMES,
    CREATED_GAMES,
    JOINED_GAMES,
) = range(5)


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    user_data = context.user_data

    username = update.message.from_user.name
    user_id = update.message.from_user.id

    if not Tg_user.objects.filter(is_creator=True):
        file_path = os.path.join(
            settings.BASE_DIR,
            r'project_organizer\static\project_organizer\creator.json'
        )
        with open(file_path, 'r') as file:
            creator = json.load(file)
        if creator[0]['tg_username'] == username:
            Tg_user.objects.create(
                tg_id=user_id,
                tg_name=username,
                is_creator=True
            )
        return foo(update, context)
    creator = Tg_user.objects.get(is_creator=True)
    if creator.tg_name == username:
        return creator_dialog(update, context)
        

    update.message.reply_text(
        'Проверка связи',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Создать игру', 'Вступить в игру', 'Мои игры'],
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    # на случай ошибок ввода
    context.user_data['error_message'] = 'Я вас не понимаю, выберите один из вариантов.'
    context.user_data['next_state'] = MAIN_MENU

    return MAIN_MENU


def foo(update: Update, context: CallbackContext) -> int:
    """Dumb foo func."""
    # TODO: временная заглушка
    chat_id = update.effective_chat.id
    username = update.message.from_user.name
    update.message.reply_text(
        f'Now creator is {username}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Создать игру', 'Вступить в игру', 'Мои игры'],
                ['Выход']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return MAIN_MENU


def creator_dialog(update: Update, context: CallbackContext) -> int:
    if not Project_manager.objects.all():
        file_path = os.path.join(
            settings.BASE_DIR,
            r'project_organizer\static\project_organizer\pm_for_project.json'
        )
        with open(file_path, 'r') as file:
            pm_for_project = json.load(file)
        for pm in pm_for_project:
            Tg_user.objects.create(
                tg_name=pm['tg_username'],
            )
            Project_manager.objects.create(
                tg_user=Tg_user.objects.get(tg_name=pm['tg_username']),
                name=pm['name'],
            )
        update.message.reply_text('Pm was added')
    if not Student.objects.all():
        file_path = os.path.join(
            settings.BASE_DIR,
            r'project_organizer\static\project_organizer\students_for_project.json'
        )
        with open(file_path, 'r') as file:
            students_for_project = json.load(file)
        for student in students_for_project:
            Tg_user.objects.create(tg_name=student['tg_username'])
            Student.objects.create(
                tg_user=Tg_user.objects.get(tg_name=student['tg_username']),
                name=student['name'],
                level=student['level'],
            )
        update.message.reply_text('Students was added')
    update.message.reply_text(
        'Hello, creator!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Создать игру', 'Вступить в игру', 'Мои игры'],
                ['Выход']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return MAIN_MENU


def done(update: Update, context: CallbackContext) -> int:
    """End conversation."""

    user_data = context.user_data

    update.message.reply_text(
        'До свидания!',
        reply_markup=ReplyKeyboardRemove(),
    )
    user_data.clear()

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.PROJECT_ORGANIZER_TG_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[
              CommandHandler('start', foo, Filters.regex('join-game-[a-zA-Z0-9_.-]*'), pass_args=True),
              CommandHandler('start', start, ~Filters.regex('join-game-[a-zA-Z0-9_.-]*')),
              CommandHandler('game', foo),
            ],
        states={
            MAIN_MENU: [
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
                MessageHandler(
                    Filters.regex('^Создать игру$'), foo
                ),
                MessageHandler(
                    Filters.regex('^Вступить в игру$'), foo, # !
                ),
                MessageHandler(
                    Filters.regex('^Мои игры$'), foo
                ),
                MessageHandler(
                    Filters.text & ~(Filters.regex('^Выход$') | Filters.command),
                    foo
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        main()
