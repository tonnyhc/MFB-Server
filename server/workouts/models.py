from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction, IntegrityError

from server.profiles.models import Profile


class Set(models.Model):
    weight = models.FloatField(
        blank=True,
        null=True
    )
    reps = models.IntegerField(
        blank=True,
        null=True
    )
    min_reps = models.IntegerField(
        blank=True,
        null=True
    )
    max_reps = models.IntegerField(
        blank=True,
        null=True
    )
    to_failure = models.BooleanField(
        default=False
    )
    bodyweight = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )


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
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_published = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name

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

    @staticmethod
    def validate_sets(data):
        required_fields = ['weight', 'reps', 'minReps', 'maxReps', 'failure', 'bodyweight']
        numbers_fields = ['weight', 'reps', 'minReps', 'maxReps']
        for set_data in data:
            if not all(field in set_data for field in required_fields):
                raise ValidationError("Each set must have values for all fields: {}".format(', '.join(required_fields)))

            for field in numbers_fields:
                try:
                    field_value = set_data[field]
                    float(field_value)
                except ValueError:
                    raise ValidationError(f"The value for {field} must be a number and must not be emtpy")

    @staticmethod
    def create_sets(request, exercise_session, sets_data):
        sets_array = []
        ExerciseSession.validate_sets(sets_data)

        for set_data in sets_data:
            set_instance = Set.objects.create(
                weight=None if set_data['bodyweight'] else set_data['weight'],
                reps=None if set_data['failure'] else set_data['reps'],
                min_reps=None if set_data['failure'] else set_data['minReps'],
                max_reps=None if set_data['failure'] else set_data['maxReps'],
                to_failure=set_data['failure'],
                bodyweight=set_data['bodyweight'],
                created_by=request.user.profile

            )
            sets_array.append(set_instance)
            exercise_session.sets.add(set_instance)
        return sets_array

    @staticmethod
    def create_session(request, exercise_name, sets_data):
        try:
            exercise = Exercise.objects.get(name=exercise_name)
        except Exercise.DoesNotExist:
            raise ValidationError("There was a problem selecting the exercise - " + exercise_name)

        exercise_session = ExerciseSession.objects.create(
            profile=request.user.profile,
            exercise=exercise
        )

        ExerciseSession.create_sets(request, exercise_session, sets_data)

        return exercise_session


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
    is_published = models.BooleanField(
        default=False
    )

    @staticmethod
    def create_session(request, workout_name, exercises):
        if not workout_name:
            raise ValidationError("Provide a name for your workout")
        if len(exercises) == 0:
            raise ValidationError("Please add exercises to your workout")

        workout_session = WorkoutSession.objects.create(
            name=workout_name,
            total_exercises=len(exercises),
            total_sets=0,
            total_weight_volume=0,
            created_by=request.user.profile
        )

        for exercise_data in exercises:
            exercise_session = ExerciseSession.create_session(request, exercise_data['name'],
                                                              exercise_data['sets'])
            workout_session.exercises.add(exercise_session)

        workout_session.total_sets = workout_session.exercises.aggregate(total_sets=models.Count('sets'))[
                                         'total_sets'] or 0
        workout_session.total_weight_volume = \
            workout_session.exercises.aggregate(
                total_weight_volume=models.Sum(models.F('sets__weight') * models.F('sets__reps')))[
                'total_weight_volume']
        workout_session.save()

        return workout_session

    @staticmethod
    def publish_workout(request, workout_id):
        user = request.user
        try:
            workout = WorkoutSession.objects.get(id=workout_id)
            if workout.created_by != user.profile:
                raise PermissionDenied("You do not have permission to publish this workout.")
            workout.is_published = True
            workout.save()
            return workout
        except WorkoutSession.DoesNotExist:
            raise IntegrityError("Workout does not exist.")


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
    def create_workout_plan(request, workout_plan_data):
        try:
            with transaction.atomic():
                name = workout_plan_data['planName']
                workouts = workout_plan_data['workouts']
                total_workouts = len(workouts)

                # Plan name validation
                if not name:
                    raise ValidationError("Provide a name for your workout plan")

                workout_plan = WorkoutPlan.objects.create(
                    name=name,
                    total_workouts=total_workouts,
                    created_by=request.user.profile
                )

                for workout_data in workout_plan_data['workouts']:
                    workout_name = workout_data['workoutName']
                    exercises_data = workout_data['exercises']
                    # Creating the instance
                    workout_session = WorkoutSession.create_session(request=request, workout_name=workout_name,
                                                                    exercises=exercises_data)
                    # adding the instance to the workout plan instance
                    workout_plan.workouts.add(workout_session)
                #     calculating the total_sets
                workout_plan.total_sets = workout_plan.workouts.aggregate(total_sets=models.Sum('total_sets'))[
                    'total_sets']
                # calculating the total weight volume
                total_weight_volume_aggregate = workout_session.exercises.aggregate(
                    total_weight_volume=models.Sum(models.F('sets__weight') * models.F('sets__reps'),
                                                   output_field=models.FloatField())
                )
                workout_session.total_weight_volume = total_weight_volume_aggregate['total_weight_volume'] or 0
                workout_plan.save()

                return workout_plan

        except Exception as e:
            # Handle the exception or log it
            raise e
