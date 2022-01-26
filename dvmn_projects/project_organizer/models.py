from django.db import models


class Tg_user(models.Model):
    tg_id = models.IntegerField()
    tg_name = models.CharField(max_length=25)

    def __str__(self):
        return '{} - {}'.format(self.tg_id, self.tg_name)
