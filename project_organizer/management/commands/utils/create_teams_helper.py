from project_organizer.models import Team

from .timeslots_helper import minus_halfhour, create_timeslots
from .get_students import get_students


def create_teams():
    if Team.objects.all():
        Team.objects.all().delete()
    timeslots = create_timeslots()
    empty_timeslots = []
    novices, novices_plus, juniors = get_students()

    team_id = 1
    for timeslot in timeslots:
        team = []
        if (len(novices) + len(novices_plus)) >= len(juniors):
            for novice in novices:
                if timeslot['start'] in novice.desire_times:
                    team.append(novice)
                    novices.remove(novice)
                    break
            for novice_plus in novices_plus:
                if timeslot['start'] in novice_plus.desire_times:
                    team.append(novice_plus)
                    novices_plus.remove(novice_plus)
                    break
            third_novice_added = False
            if len(novices) > len(novices_plus):
                for novice in novices:
                    if timeslot['start'] in novice.desire_times:
                        team.append(novice)
                        novices.remove(novice)
                        third_novice_added = True
                        break
            if not third_novice_added:
                for novice_plus in novices_plus:
                    if timeslot['start'] in novice_plus.desire_times:
                        team.append(novice_plus)
                        novices_plus.remove(novice_plus)
                        break
        if not team:
            for junior in juniors:
                if timeslot['start'] in junior.desire_times:
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
