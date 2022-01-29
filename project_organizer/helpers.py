from datetime import datetime, timedelta

from project_organizer.models import Project_manager, Student, Team


def plus_halfhour(time):
    fulldate = datetime(100, 1, 1, time.hour, time.minute, time.second)
    shifted_fulldate = fulldate + timedelta(minutes=30)
    return shifted_fulldate.time()


def minus_halfhour(time):
    fulldate = datetime(100, 1, 1, time.hour, time.minute, time.second)
    shifted_fulldate = fulldate - timedelta(minutes=30)
    return shifted_fulldate.time()


def interval(start, end):
    delta = (end.hour - start.hour)*60 + end.minute - start.minute
    return delta


def create_timeslots_list():
    managers = Project_manager.objects.all()
    timeslots = []
    for manager in managers:
        start = manager.from_time
        while start <= minus_halfhour(manager.until_time):
            timeslot = dict()
            timeslot['pm'] = manager
            timeslot['start'] = start
            timeslots.append(timeslot)
            start = plus_halfhour(start)
    sorted_timeslots = sorted(timeslots, key=lambda k: k['start'])
    return sorted_timeslots


def create_students_lists():
    novices = list(Student.objects.filter(level='novice'))
    novices_plus = list(Student.objects.filter(level='novice+'))
    juniors = list(Student.objects.filter(level='junior'))

    sorted_novices = sorted(
        novices,
        key=lambda k: interval(k.from_time, k.until_time)
    )
    sorted_novices_plus = sorted(
        novices_plus,
        key=lambda k: interval(k.from_time, k.until_time)
    )
    sorted_juniors = sorted(
        juniors,
        key=lambda k: interval(k.from_time, k.until_time)
    )

    return sorted_novices, sorted_novices_plus, sorted_juniors


def create_teams():
    timeslots = create_timeslots_list()
    empty_timeslots = []
    novices, novices_plus, juniors = create_students_lists()

    team_id = 1
    for timeslot in timeslots:
        team = []
        if (len(novices) + len(novices_plus)) >= len(juniors):
            for novice in novices:
                if (
                    minus_halfhour(novice.until_time) >=
                    timeslot['start'] >=
                    novice.from_time
                ):
                    team.append(novice)
                    novices.remove(novice)
                    break
            for novice_plus in novices_plus:
                if (
                    minus_halfhour(novice_plus.until_time) >=
                    timeslot['start'] >=
                    novice_plus.from_time
                ):
                    team.append(novice_plus)
                    novices_plus.remove(novice_plus)
                    break
            third_novice_added = False
            if len(novices) > len(novices_plus):
                for novice in novices:
                    if (
                        minus_halfhour(novice.until_time) >=
                        timeslot['start'] >=
                        novice.from_time
                    ):
                        team.append(novice)
                        novices.remove(novice)
                        third_novice_added = True
                        break
            if not third_novice_added:
                for novice_plus in novices_plus:
                    if (
                        minus_halfhour(novice_plus.until_time) >=
                        timeslot['start'] >=
                        novice_plus.from_time
                    ):
                        team.append(novice_plus)
                        novices_plus.remove(novice_plus)
                        break
        if not team:
            for junior in juniors:
                if (
                    minus_halfhour(junior.until_time) >=
                    timeslot['start'] >=
                    junior.from_time
                ):
                    team.append(junior)
                    juniors.remove(junior)
                if len(team) == 3:
                    break
        if team:
            team_in_db = Team.objects.create(
                team_id=team_id,
                project_manager=timeslot['pm'],
                call_time=timeslot['start'],
            )
            for student in team:
                student.team = team_in_db
                student.save()
            team_id += 1
        else:
            empty_timeslots.append(timeslot)
