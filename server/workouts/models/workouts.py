from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction, IntegrityError

from server.profiles.models import Profile


class BaseWorkoutModel(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(max_length=MAX_LEN_NAME)
    total_exercises = models.IntegerField()
    total_sets = models.IntegerField()
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class WorkoutTemplate(BaseWorkoutModel):
    is_published = models.BooleanField(default=True)
    exercises = models.ManyToManyField("WorkoutTemplateExerciseItem", related_name="template_exercises")

    @staticmethod
    def create_workout_template(request, workout_name, exercises):
        from server.workouts.utils import create_exercise_sessions_for_workout
        a = 5
        if not workout_name:
            raise ValidationError("Provide a name for your workout template")
        if len(exercises) == 0:
            raise ValidationError("Please add exercises to your workout template")

        workout_template = WorkoutTemplate.objects.create(
            name=workout_name,
            total_exercises=len(exercises),
            total_sets=0,
            created_by=request.user.profile

        )

        exercise_sessions = create_exercise_sessions_for_workout(request, workout_template, exercises)
        if not exercise_sessions or len(exercise_sessions) == 0:
            workout_template.delete()
            raise ValidationError("Please add exercises to your workout template")
        workout_template.exercises.add(*exercise_sessions)
        workout_template.save()
        return workout_template

    @staticmethod
    def publish_template(request, workout_id):
        user = request.user
        try:
            workout = WorkoutTemplate.objects.get(id=workout_id)
            if workout.created_by != user.profile:
                raise PermissionDenied("You do not have permission to publish this workout.")
            workout.is_published = True
            workout.save()
            return workout
        except WorkoutSession.DoesNotExist:
            raise IntegrityError("Workout does not exist.")

    @staticmethod
    def edit_template(request, workout_session, new_data):
        from server.workouts.utils import update_workout_session_exercises

        workout_name = new_data.get('name')
        exercises = new_data.get('exercises')

        workout_session.name = workout_name
        workout_session.save()
        return workout_session


class WorkoutSession(BaseWorkoutModel):
    total_weight_volume = models.IntegerField()
    exercises = models.ManyToManyField(
        'WorkoutExerciseSession',
        related_name='workout_sessions'
    )

    @staticmethod
    def create_session(request, workout_name, exercises):
        from server.workouts.utils import create_exercise_sessions_for_workout

        if not workout_name:
            raise ValidationError("Provide a name for your workout")
        if len(exercises) == 0:
            raise ValidationError("Please add exercises to your workout")

        workout_session = WorkoutSession.objects.create(
            name=workout_name,
            total_exercises=len(exercises),
            # TODO: Move the total_set and total_weight volume to a signal
            total_sets=0,
            total_weight_volume=0,
            created_by=request.user.profile,

        )

        exercise_sessions = create_exercise_sessions_for_workout(request, workout_session, exercises)
        workout_session.exercises.add(*exercise_sessions)
        workout_session.save()
        return workout_session


class BaseExerciseItemForWorkout(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ['order']

    def __str__(self):
        exercise_name = self.content_object.exercise.name if self.content_type.model != 'supersetsession' else 'Superset'
        return f"{self.__class__.__name__} {self.id} ---- {exercise_name}"


class WorkoutExerciseSession(BaseExerciseItemForWorkout):
    workout_session = models.ForeignKey(WorkoutSession, related_name='workout_exercises', on_delete=models.CASCADE)


class WorkoutTemplateExerciseItem(BaseExerciseItemForWorkout):
    workout_template = models.ForeignKey(
        WorkoutTemplate, related_name='template_exercises', on_delete=models.CASCADE
    )


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

    @staticmethod
    def create_routine(request, routine_data):
        try:
            with transaction.atomic():
                name = routine_data['name']
                workouts = routine_data['workouts']
                total_workouts = len(workouts)

                # Plan name validation
                if not name:
                    raise ValidationError(message="Provide a name for your workout plan")

                workout_plan = WorkoutPlan.objects.create(
                    name=name,
                    total_workouts=total_workouts,
                    created_by=request.user.profile
                )

                for workout_data in routine_data['workouts']:
                    workout_name = workout_data['name']
                    exercises_data = workout_data['exercises']
                    # Creating the instance
                    workout_session = WorkoutSession.create_session(request=request, workout_name=workout_name,
                                                                    exercises=exercises_data)
                    # adding the instance to the workout plan instance
                    workout_plan.workouts.add(workout_session)

                workout_plan.save()

                return workout_plan

        except Exception as e:
            # Handle the exception or log it
            raise e


class ActiveRoutine(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    workout_plan = models.OneToOneField(
        WorkoutPlan,
        primary_key=True,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Active routine for {self.profile} created at {self.created_at}"
