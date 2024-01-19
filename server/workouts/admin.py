from django.contrib import admin

from server.workouts.models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by_username', 'id', 'created_at')

    def created_by_username(self, obj):
        return obj.created_by.user.username if obj.created_by else "Server"