# Generated by Django 4.0.1 on 2022-01-26 15:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project_organizer', '0003_team'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=25)),
                ('level', models.CharField(max_length=15)),
                ('desired_time', models.TimeField(blank=True, null=True, verbose_name='Desired call start time')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='project_organizer.team')),
                ('tg_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='project_organizer.tg_user', verbose_name='telegram id')),
            ],
        ),
    ]
