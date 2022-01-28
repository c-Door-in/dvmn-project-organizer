from django.contrib import admin
from django.db.models import fields

from .models import Tg_user, Project_manager, Team, Student

@admin.register(Tg_user)
class Tg_userAdmin(admin.ModelAdmin):
    list_display = (
        'tg_id',
        'tg_name',
        'is_creator',
    )


@admin.register(Project_manager)
class Project_managerAdmin(admin.ModelAdmin):
    list_display = (
        'tg_user',
        'name',
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        'team_id',
        'project_manager',
        'call_time',
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'tg_user',
        'name',
        'level',
        'from_time',
        'until_time',
        'team',
    )
