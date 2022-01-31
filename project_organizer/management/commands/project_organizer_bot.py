import json
import os
import random

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

from .utils import create_teams_helper, timeslots_helper


(
    NO_DB,
    CREATOR,
    PM_DIALOG,
    MAIN_MENU,
    STUDENT_DIALOG,
    DELETE,
) = range(6)


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
    if username == creator.tg_name:
        return creator_dialog(update, context)

    if Project_manager.objects.filter(tg_user__tg_name=username):
        return pm_dialog(update, context)

    if Student.objects.filter(tg_user__tg_name=username):
        return student_dialog(update, context)

    update.message.reply_text(
        'Вас нет в списке. Как вы сюда попали?'
    )
    # на случай ошибок ввода
    context.user_data['error_message'] = 'Я вас не понимаю, выберите один из вариантов.'

    return done(update, context)


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
    with open(file_path, 'r', encoding='utf-8-sig') as file:
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
    keyboard=[['Сжечь все']]
    if Project_manager.objects.filter(from_time=None):
        text = (
            '\n'.join(pm.tg_user.tg_name for pm in Project_manager.objects.filter(from_time=None))
        )
        update.message.reply_text(
            'Отошлите ссылку на бота этим ПМ:\n' + text
        )
        final_text = (
            'Как только они отметят свое время, '
            'вы получите уведомление'
        )
    elif not Student.objects.filter(tg_user__tg_id__isnull=False):
        text = (
            '\n'.join(student.tg_user.tg_name
                      for student in Student.objects.filter(desire_times=''))
        )
        update.message.reply_text(
            'Отошлите ссылку на бота этим студентам:\n' + text
        )
        final_text = (
            'Как только кто-то отметит время, вы получите уведомление'
        )
        keyboard.insert(0, ['Пускай за них решит судьба!'])
    else:
        text = (
            '\n'.join('{} - {}'.format(student.name, student.tg_user.tg_name)
                      for student in Student.objects.filter(desire_times=''))
        )
        update.message.reply_text(
            'Эти студенты еще не указали свое время:\n' + text
        )
        final_text = (
            'Нажмите Сформировать, чтобы посмотреть '
            'команды на текущий момент'
        )
        keyboard.insert(0, ['Пускай за них решит судьба!'])
        keyboard.insert(0, ['Сформировать'])
    update.message.reply_text(
        final_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return CREATOR


def create_teams(update, context):
    update.message.reply_text(
        'Идет формирование команд...',
    )
    create_teams_helper.create_teams()
    return teams_comfirm(update, context)


def teams_comfirm(update, context):
    for pm in Project_manager.objects.all():
        update.message.reply_text(f'PM - {pm}')
        pm_teams = Team.objects.filter(project_manager=pm)
        if not pm_teams:
            text = f'{pm} пока без команд'
        else:
            text = ''
            for team in pm_teams:
                team_id = team.team_id
                team_members = '\n'.join(student.name for student in team.students.all())
                team_time = team.call_time.strftime('%H:%M')
                text += (
                    '\n\n'
                    f'Команда №{team_id}\n'
                    f'Созвон в {team_time}\n'
                    f'Участники:\n{team_members}'
                )
        update.message.reply_text(text)
    if not Team.objects.all():
        return creator_dialog(update, context)
    update.message.reply_text(
        'Подтвердите составы команд',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Сформировать'], ['Утвердить']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return CREATOR


def teams_complete(update, context):
    for team in Team.objects.all():
        pm = team.project_manager
        pm_name = pm.name
        team_id = team.team_id
        team_members = '\n'.join('{} - {}'.format(student.name, student.tg_user.tg_name) for student in team.students.all())
        team_time = team.call_time.strftime('%H:%M')
        pm_text = (
            f'Команда №{team_id}\n'
            f'Созвон в {team_time}\n'
            f'Участники:\n{team_members}'
        )
        context.bot.send_message(
            pm.tg_user.tg_id, 
            text=pm_text,
        )
        for student in team.students.all():
            student_text = (
                'Приветствую!\n'
                f'Ваша команда созванивается в {team_time}\n'
                f'Ваш ПМ - {pm_name}\n'
                'Первый созвон во вторник.\n'
                'А пока заполните анкету, '
                'прочитайте инструкций на 50 страниц, '
                'приведите в порядок все прошлые проекты '
                'и перечитайте "Войну и мир".\n'
                'Все это вам обязательно пригодится.\n'
                'До встречи!'
            )
            if student.tg_user.tg_id:
                context.bot.send_message(
                    student.tg_user.tg_id, 
                    text=student_text,
                )
    update.message.reply_text(
        'Всем участникам разосланы уведомления '
        'о времени созвонов их групп.',
    )
    return done(update, context)


def pm_dialog(update, context):
    username = update.message.from_user.name
    user_id = update.message.from_user.id
    pm_tg_user = Tg_user.objects.get(tg_name=username)
    if not pm_tg_user.tg_id:
        pm_tg_user.tg_id = user_id
        pm_tg_user.save()
    pm = Project_manager.objects.get(tg_user=pm_tg_user)
    if not pm.from_time:
        update.message.reply_text(
            'Укажите временной промежуток для созвонов с командами '
            '(в формате 17:30-21:00)',
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        update.message.reply_text(
            'Вы указали время с {} до {}'.format(pm.from_time, pm.until_time),
            reply_markup = ReplyKeyboardMarkup(
                keyboard=[['Изменить']],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
    
    return PM_DIALOG


def pm_time_confirm(update, context):
    time_interval = update.message.text.split('-')
    username = update.message.from_user.name
    pm = Project_manager.objects.get(tg_user__tg_name=username)
    pm.from_time = time_interval[0]
    pm.until_time = time_interval[1]
    pm.save()
    if not Project_manager.objects.filter(from_time__isnull=True):
        creator=Tg_user.objects.get(is_creator=True)
        context.bot.send_message(creator.tg_id, 
                                 text="Все ПМы указали свое время")
    return pm_dialog(update, context)
    

def pm_time_change(update, context):
    username = update.message.from_user.name
    pm = Project_manager.objects.get(tg_user__tg_name=username)
    pm.from_time = None
    pm.until_time = None
    pm.save()
    return pm_dialog(update, context)


def get_unique_timeslots():
    timeslots = timeslots_helper.create_timeslots()
    times = []
    for timeslot in timeslots:
        time = timeslot['start']
        if time not in times:
            times.append(time)
    return times


def random_desire_times(update, context):
    timeslots = get_unique_timeslots()
    times_number = random.randint(1, len(timeslots))
    random_desire_times = random.sample(timeslots, k=times_number)
    for student in Student.objects.filter(desire_times=''):
        student.desire_times = ','.join(random_desire_times)
        student.save()
    return creator_dialog(update, context)
        


def student_dialog(update, context):
    username = update.message.from_user.name
    user_id = update.message.from_user.id
    student_tg_user = Tg_user.objects.get(tg_name=username)
    if not student_tg_user.tg_id:
        student_tg_user.tg_id = user_id
        student_tg_user.save()
    student = Student.objects.get(tg_user=student_tg_user)

    timeslots = get_unique_timeslots()
    
    keyboard = [['Подтвердить']]
    desire_times = student.desire_times.split(',')
    if update.message.text:
        if update.message.text in desire_times:
            desire_times.remove(update.message.text)
        elif update.message.text in timeslots:
            desire_times.append(update.message.text)
        student.desire_times = ','.join(sorted(desire_times))
        student.save()
        if student.desire_times:
            text = '\n'.join(desire_times)
            update.message.reply_text(
                f'Вы выбрали:\n{text}',
            )
    # timeslots = sorted(list(set(timeslots) - set(desire_times)))
    for timeslot in timeslots:
        keyboard.append([timeslot])

    update.message.reply_text(
        'Выберете удобное время для созвона (можно несколько)',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return STUDENT_DIALOG


def student_confirm(update, context):
    username = update.message.from_user.name
    student = Student.objects.get(tg_user__tg_name=username)
    student_desire_times = '\n'.join(student.desire_times.split(','))
    update.message.reply_text(
            'Спасибо!\n'
            'Вы выбрали:\n'
            f'{student_desire_times}'
            '\nПосле формирования команд '
            'вам придет уведомление',
        )
    return done(update, context)


def delete_confirm(update, context):
    update.message.reply_text(
        'Вы точно уверены, что хотите все сжечь? Вся база будет стерта!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['БЕЗУСЛОВНО!!!'], ['Отмена! Отмена!']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return DELETE


def delete_db(update, context):
    Tg_user.objects.all().delete()
    update.message.reply_text(
        'Все данные удалены.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return done(update, context)
    


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
                    teams_complete,
                ),
                MessageHandler(
                    Filters.regex('^Пускай за них решит судьба!$'),
                    random_desire_times,
                ),
                MessageHandler(
                    Filters.regex('^Сжечь все$'),
                    delete_confirm,
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
                    Filters.regex('^(((|1)[0-9])|(2[0-4]))\:((00)|(30))\-(((|1)([0-9]))|(2[0-4]))\:((00)|(30))$'),
                    pm_time_confirm,
                ),
                MessageHandler(
                    Filters.regex('^Изменить$'),
                    pm_time_change,
                ),
            ],
            STUDENT_DIALOG: [
                MessageHandler(
                    Filters.regex('^(([01][0-9])|(2[0-4]))\:((00)|(30))$'),
                    student_dialog,
                ),
                MessageHandler(
                    Filters.regex('^Подтвердить$'),
                    student_confirm,
                ),
            ],
            DELETE: [
                MessageHandler(
                    Filters.regex('^БЕЗУСЛОВНО!!!$'),
                    delete_db,
                ),
                MessageHandler(
                    Filters.regex('^Отмена! Отмена!$'),
                    creator_dialog,
                ),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
        allow_reentry=True
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
