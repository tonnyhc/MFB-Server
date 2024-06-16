from django.contrib import admin

from server.workouts.models import Exercise, WorkoutSession, WorkoutPlan, Set, ExerciseSession, MuscleGroup, \
    ExerciseSessionItem


@admin.register(ExerciseSessionItem)
class ExerciseSessionItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by_username', 'id', 'created_at')

    def created_by_username(self, obj):
        return obj.created_by.user.username if obj.created_by else "Server"


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'created_by')

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

@admin.register(ExerciseSession)
class ExerciseSessionAdmin(admin.ModelAdmin):
    pass

@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    pass

@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    pass