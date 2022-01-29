from django.db import models


class Tg_user(models.Model):
    tg_id = models.IntegerField(unique=True, blank=True, null=True)
    tg_name = models.CharField(unique=True, max_length=25)
    is_creator = models.BooleanField(default=False)

    def __str__(self):
        return self.tg_name


class Project_manager(models.Model):
    tg_user = models.ForeignKey(
        Tg_user,
        on_delete=models.CASCADE,
        related_name='project_managers',
    )
    name = models.CharField(max_length=25)
    from_time = models.TimeField(
        'Available from a time',
        blank=True,
        null=True
    )
    until_time = models.TimeField(
        'Available until a time',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class Team(models.Model):
    team_id = models.IntegerField()
    project_manager = models.ForeignKey(
        Project_manager,
        on_delete=models.SET_NULL,
        related_name='teams',
        null=True,
    )
    call_time = models.TimeField('Team call start time')

    def __str__(self):
        return 'Team leading by {} starts calling at {}'.format(
            self.project_manager,
            self.call_time,
        )


class Student(models.Model):
    tg_user = models.ForeignKey(
        Tg_user,
        on_delete=models.CASCADE,
        related_name='students',
        verbose_name='telegram id',
    )
    name = models.CharField(max_length=25, blank=True)
    level = models.CharField(max_length=15)
    from_time = models.TimeField(
        'Available from a time',
        blank=True,
        null=True
    )
    until_time = models.TimeField(
        'Available until a time',
        blank=True,
        null=True
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        related_name='students',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name
    
