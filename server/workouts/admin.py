from django.contrib import admin

from server.workouts.models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    pass
