from django.db import models

from server.profiles.models import Profile


class Set(models.Model):
    weight = models.FloatField()
    reps = models.IntegerField()
    min_reps = models.IntegerField(
        blank=True,
        null=True
    )
    max_reps = models.IntegerField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    ),


class Exercise(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )
    cover_photo = models.URLField(
        blank=True,
        null=True
    )
    information = models.TextField(
        blank=True,
        null=True
    )
    video_tutorial = models.URLField(
        blank=True,
        null=True,
    )
    tips = models.TextField(
        blank=True,
        null=True,
    )

    # If this is a custom exercise for the given user then set it, otherwise if it comes from the server's
    # already declared exercises skip it
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    # targeted_muscle_groups = models.CharField()


class ExerciseSession(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE
    )
    sets = models.ManyToManyField(Set)
    created_at = models.DateTimeField(
        auto_now_add=True
    )


class WorkoutSession(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME
    )
    total_exercises = models.IntegerField()
    total_sets = models.IntegerField()
    total_weight_volume = models.IntegerField()
    exercises = models.ManyToManyField(ExerciseSession)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )


class WorkoutPlanManager(models.Manager):
    def create_workout_plan(self, workout_plan_data):
        name = workout_plan_data.planName
        total_workouts = workout_plan_data.numberOfWorkouts


class WorkoutPlan(models.Model):
    MAX_LEN_NAME = 100
    name = models.CharField(
        max_length=MAX_LEN_NAME
    )
    total_workouts = models.IntegerField()
    workouts = models.ManyToManyField(WorkoutSession)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    objects = WorkoutPlanManager()