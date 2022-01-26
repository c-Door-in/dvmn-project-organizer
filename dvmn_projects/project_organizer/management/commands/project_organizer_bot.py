from django.conf import settings
from django.core.management.base import BaseCommand
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
    JOIN_GAME,
    MY_GAMES,
    CREATED_GAMES,
    JOINED_GAMES,
) = range(5)


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    user_data = context.user_data

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
    update.message.reply_text(
        'Временно недоступно',
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
