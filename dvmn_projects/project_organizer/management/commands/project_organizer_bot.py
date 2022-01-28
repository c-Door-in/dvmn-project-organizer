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
    NO_DB,
    CREATOR,
    PM_DIALOG,
    CREATED_GAMES,
    STUDENT_DIALOG,
) = range(5)


def start(update, context):
    user_data = context.user_data

    username = update.message.from_user.name
    user_id = update.message.from_user.id

    if not Tg_user.objects.filter(is_creator=True):
        Tg_user.objects.create(
            tg_id=user_id,
            tg_name=username,
            is_creator=True
        )
        return no_db(update, context)
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


def no_db(update, context):
    chat_id = update.effective_chat.id
    username = update.message.from_user.name
    update.message.reply_text(
        f'В качестве создателя установлен {username}\n'
        'Загрузите базу данных?',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Загрузить базу данных']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return NO_DB


def create_new_db(update, context):
    file_path = os.path.join(
            settings.BASE_DIR,
            r'project_db.json'
        )
    with open(file_path, 'r', encoding='utf-8') as file:
        project_db = json.load(file)
    for user in project_db:
        Tg_user.objects.create(tg_name=user['tg_username'])
        if user['level'] == 'pm':
            Project_manager.objects.create(
                tg_user=Tg_user.objects.get(tg_name=user['tg_username']),
                name=user['name'],
            )
        else:
            Student.objects.create(
                tg_user=Tg_user.objects.get(tg_name=user['tg_username']),
                name=user['name'],
                level=user['level'],
            )
    update.message.reply_text('База данных загружена')
    return creator_dialog(update, context)

    return CREATOR


def creator_dialog(update, context):
    if Project_manager.objects.filter(from_time=None):
        text = (
            '\n'.join(pm.tg_user.tg_name for pm in Project_manager.objects.filter(from_time=None))
        )
        update.message.reply_text(
            'Отошлите ссылку на бота этим ПМ: \n' + text
        )
        update.message.reply_text(
            'Как только они отметят свое время, '
            'вы получите уведомление'
        )
        return done(update, context)
    update.message.reply_text(
        'Нажмите Сформировать, чтобы посмотреть команды на текущий момент',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Сформировать']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return CREATOR


def create_teams(update, context):
    chat_id = update.effective_chat.id
    username = update.message.from_user.name
    update.message.reply_text(
        'Нажмите Сформировать, чтобы посмотреть команды на текущий момент',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Сформировать']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return CREATOR


def comfirm(update, context):
    chat_id = update.effective_chat.id
    username = update.message.from_user.name
    update.message.reply_text(
        'Нажмите Сформировать, чтобы посмотреть команды на текущий момент',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Сформировать']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return CREATOR


def done(update, context):
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
        entry_points=[CommandHandler('start', start)],
        states={
            CREATOR: [
                MessageHandler(
                    Filters.regex('^Сформировать$'),
                    create_teams,
                ),
                MessageHandler(
                    Filters.regex('^Утвердить$'),
                    comfirm,
                ),
            ],
            NO_DB: [
                MessageHandler(
                    Filters.document.file_extension('json'),
                    create_new_db,
                ),
                MessageHandler(
                    Filters.regex('^Загрузить базу данных$'),
                    create_new_db,
                ),
            ],
            PM_DIALOG: [
                MessageHandler(
                    Filters.regex('^Сформировать$'),
                    create_teams,
                ),
                MessageHandler(
                    Filters.regex('^Утвердить$'),
                    comfirm,
                ),
            ],
            STUDENT_DIALOG: [
                MessageHandler(
                    Filters.regex('^Сформировать$'),
                    create_teams,
                ),
                MessageHandler(
                    Filters.regex('^Утвердить$'),
                    comfirm,
                ),
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
