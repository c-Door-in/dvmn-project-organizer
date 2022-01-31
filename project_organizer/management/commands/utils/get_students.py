from project_organizer.models import Student


def interval(start, end):
    delta = (end.hour - start.hour)*60 + end.minute - start.minute
    return delta


def get_students():
    novices = list(Student.objects.filter(level='novice',
                                          desire_times__isnull=False))
    novices_plus = list(Student.objects.filter(level='novice+',
                                               desire_times__isnull=False))
    juniors = list(Student.objects.filter(level='junior',
                                          desire_times__isnull=False))

    sorted_novices = sorted(
        novices,
        key=lambda k: len(k.desire_times)
    )
    sorted_novices_plus = sorted(
        novices_plus,
        key=lambda k: len(k.desire_times)
    )
    sorted_juniors = sorted(
        juniors,
        key=lambda k: len(k.desire_times)
    )

    return sorted_novices, sorted_novices_plus, sorted_juniors
