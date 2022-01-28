# Бот для автоматизация проектов Девман
Бот помогает организовать группы учебных проектов Девман. 

## Настройки

### Подключите зависимости
```
pip install -r requirements.txt
```
### Подключите переменные окружения
Создайте файл .env в директории `/dvmn_projects` рядом с `settings.py` и введите
```
PROJECT_ORGANIZER_TG_TOKEN=<token>
```
где token - токен телеграм-бота.

### Подключите базу данных
Создайте базу данных, запустив команду
```
python manage.py migrate
```

## Запуск бота
Для запуска бота введите
```
python manage.py project_organizer_bot
```

## Редактирование бота
Код бота располагается в `/project_organizer/management/commands/project_organizer_bot.py`
Модели базы данных располагаются в `/project_organizer/models.py`
