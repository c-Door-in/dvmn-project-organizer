from datetime import datetime, timedelta
from pprint import pprint

from project_organizer.models import Project_manager


def plus_halfhour(time):
    fulldate = datetime(100, 1, 1, time.hour, time.minute, time.second)
    shifted_fulldate = fulldate + timedelta(minutes=30)
    return shifted_fulldate.time()


def minus_halfhour(time):
    fulldate = datetime(100, 1, 1, time.hour, time.minute, time.second)
    shifted_fulldate = fulldate - timedelta(minutes=30)
    return shifted_fulldate.time()


def create_timeslots():
    managers = Project_manager.objects.all()
    timeslots = []
    for manager in managers:
        start = manager.from_time
        while start <= minus_halfhour(manager.until_time):
            timeslot = dict()
            timeslot['pm'] = manager
            timeslot['start'] = start.strftime('%H:%M')
            timeslots.append(timeslot)
            start = plus_halfhour(start)
    sorted_timeslots = sorted(timeslots, key=lambda k: k['start'])
    return sorted_timeslots
