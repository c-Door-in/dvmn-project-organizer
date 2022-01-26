from django.db import models


class Tg_user(models.Model):
    tg_id = models.IntegerField()
    tg_name = models.CharField(max_length=25)

    def __str__(self):
        return '{} - {}'.format(self.tg_id, self.tg_name)


class Project_manager(models.Model):
    tg_id = models.ForeignKey(
        Tg_user,
        on_delete=models.CASCADE,
        related_name='project_managers',
    ),
    name = models.CharField(max_length=25)

    def __str__(self):
        return name


class Team(models.Model):
    team_id = models.IntegerFiels()
    project_manager = models.ForeignKey(
        Project_manager,
        on_delete=models.SET_NULL,
        related_name='teams',
        null=True,
    )
    call_time = models.TimeField('Team call start time')

    def __str__(self):
        return 'Team leading by {} starts calling at {}'.format(
            self.call_time,
            self.project_manager,
        )
