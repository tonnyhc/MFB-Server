import datetime

from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction, IntegrityError
from simple_history.models import HistoricalRecords

from server.profiles.models import Profile
from django.db.models import Max

from server.utils import string_to_bool
from server.workouts.utils import get_value_or_default


class MuscleGroup(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Rest(models.Model):
    minutes = models.IntegerField(default=0)
    seconds = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.minutes}m {self.seconds}s"

    def edit_session(self, minutes, seconds):
        # checking if the fields are the same to not make the edit to the db
        if self.minutes == minutes and self.seconds == seconds:
            return self
        self.minutes = minutes
        self.seconds = seconds
        self.save()
        return self


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
    # this is the index the set will be in the exercise session
    set_index = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )

    history = HistoricalRecords()

    @staticmethod
    def edit_data(request, set_instance, set_data):
        # TODO: Check if all the fields are the same, to not make the edits
        if request.user.profile != set_instance.created_by:
            return PermissionDenied("You can only edit your own sets")
        set_intance_fields = {
            'weight': set_instance.weight,
            'reps': set_instance.reps,
            'min_reps': set_instance.min_reps,
            'max_reps': set_instance.max_reps,
            'to_failure': set_instance.to_failure,
            'bodyweight': set_instance.bodyweight

        }
        set_data_fields = {
            'weight': float(set_data.get('weight')),
            'reps': int(set_data.get('reps')),
            'min_reps': int(set_data.get('min_reps')),
            'max_reps': int(set_data.get('max_reps')),
            'to_failure': bool(set_data.get('to_failure')),
            'bodyweight': bool(set_data.get('bodyweight'))
        }

        if set_data_fields == set_intance_fields:
            return set_instance

        set_instance.reps = set_data['reps']
        set_instance.weight = set_data['weight']
        set_instance.min_reps = set_data['min_reps']
        set_instance.max_reps = set_data['max_reps']
        set_instance.to_failure = set_data['to_failure']
        set_instance.bodyweight = set_data['bodyweight']

        set_instance.save()
        return set_instance

    @staticmethod
    def remove_set_instance(set_instance):
        set_instance.delete()
        set_instance.save()

    class Meta:
        ordering = ['set_index']


class Interval(models.Model):
    time = models.TimeField()
    distance = models.PositiveIntegerField()
    level = models.PositiveIntegerField()
    pace = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)

    index_in_session = models.PositiveIntegerField(
        default=0
    )


class Exercise(models.Model):
    MAX_LEN_TIPS = 255
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )
    # cover_photo = CloudinaryField('image', blank=True, null=True)
    targeted_muscle_groups = models.ManyToManyField(MuscleGroup, blank=True,
                                                    null=True)
    instructions = models.TextField(
        blank=True,
        null=True
    )

    video_tutorial = CloudinaryField(resource_type="video", blank=True, null=True)
    tips_and_tricks = models.TextField(
        max_length=MAX_LEN_TIPS,
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
    is_cardio = models.BooleanField(
        blank=True,
        null=True,
        default=False,
    )
    bodyweight = models.BooleanField(
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
    # sets = models.ManyToManyField(Set)
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    notes = models.TextField(
        blank=True,
        null=True
    )

    history = HistoricalRecords()

    @staticmethod
    def validate_sets(data):
        required_fields = ['weight', 'reps', 'min_reps', 'max_reps', 'to_failure', 'bodyweight']
        numbers_fields = ['weight', 'reps', 'min_reps', 'max_reps']
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
                reps=None if set_data['to_failure'] else set_data['reps'],
                min_reps=None if set_data['to_failure'] else set_data['min_reps'],
                max_reps=None if set_data['to_failure'] else set_data['max_reps'],
                to_failure=set_data['to_failure'],
                bodyweight=set_data['bodyweight'],
                created_by=request.user.profile

            )
            sets_array.append(set_instance)
            exercise_session.sets.add(set_instance)
        return sets_array

    # TODO :NEW
    @staticmethod
    def create_session(request, exercise_name: str, exercise_id: int, session_data):
        try:
            exercise = Exercise.objects.get(name=exercise_name, pk=exercise_id)
        except Exercise.DoesNotExist:
            raise ValidationError(f"There was a problem selecting the exercise - {exercise_name}")

        with transaction.atomic():
            exercise_session = ExerciseSession.objects.create(
                profile=request.user.profile,
                exercise=exercise,
            )
            if not session_data or len(session_data) <= 0:  # if there is no data for the session
                raise ValidationError("Cant create empty exercise session")
            for item in session_data:
                if item['type'] == 'set':
                    ExerciseSession.add_set(request, exercise_session, item['data'])
                elif item['type'] == 'rest':
                    ExerciseSession.add_rest(request, exercise_session, item['data'])
                elif item['type'] == 'interval':
                    ExerciseSession.add_interval(request, exercise_session, item['data'])

        return exercise_session

    @staticmethod
    def add_single_set_instance(request, exercise_session, set_data):
        current_sets = exercise_session.sets.all()
        max_set_index = current_sets.aggregate(Max('set_index'))['set_index__max']
        new_set_index = max_set_index + 1 if max_set_index is not None else 0
        try:
            is_valid = ExerciseSession.validate_sets([set_data])
        except ValidationError as e:
            raise ValidationError(e.message)
        set_instance = Set.objects.create(
            weight=set_data.get('weight', 0),
            reps=set_data.get('reps', 0),
            min_reps=set_data.get('min_reps', 0),
            max_reps=set_data.get('max_reps', 0),
            to_failure=set_data.get('to_failure', False),
            bodyweight=set_data.get('bodyweight', False),
            set_index=new_set_index,
            created_by=request.user.profile
        )

        exercise_session.sets.add(set_instance)
        return set_instance

    @staticmethod
    def edit_session(request, exercise_session, data):
        sets = data['session_data']
        notes = data['notes']
        for exercise_set in sets:
            if not 'id' in exercise_set:
                ExerciseSession.add_single_set_instance(request, exercise_session, exercise_set)
                continue
            if exercise_set['type'] == 'rest':
                rest = Rest.objects.get(pk=exercise_set['id'])
                rest.edit_session(exercise_set['data']['minutes'], exercise_set['data']['seconds'])
                continue
            # TODO: Check if the item is rest or interval
            try:
                set_instance = Set.objects.get(pk=exercise_set['id'])
                Set.edit_data(set_instance, exercise_set.get('data', {}))
            except Set.DoesNotExist:
                return models.ObjectDoesNotExist
        exercise_session.notes = notes
        return exercise_session.save()

    # added later
    @staticmethod
    def add_set(request, exercise_session, set_data):
        # TODO: Check the items fields and if there are empty dont create the instance

        set_instance = Set.objects.create(
            weight=float(set_data.get('weight', 0)),
            reps=int(set_data.get('reps', 0)),
            min_reps=int(set_data.get('min_reps', 0)),
            max_reps=int(set_data.get('max_reps', 0)),
            to_failure=string_to_bool(set_data.get('to_failure', False)),  # Convert string to boolean
            bodyweight=string_to_bool(set_data.get('bodyweight', False)),  # Convert string to boolean
            created_by=request.user.profile
        )
        content_type = ContentType.objects.get_for_model(set_instance)
        ExerciseSessionItem.objects.create(
            exercise_session=exercise_session,
            content_type=content_type,
            object_id=set_instance.id,
            order=ExerciseSessionItem.objects.filter(exercise_session=exercise_session).count()
        )
        return set_instance

    # added later
    @staticmethod
    def add_rest(request, exercise_session, rest_data):
        rest_instance = Rest.objects.create(
            minutes=rest_data.get('minutes', 0),
            seconds=rest_data.get('seconds', 0),
            created_by=request.user.profile
        )
        content_type = ContentType.objects.get_for_model(rest_instance)
        ExerciseSessionItem.objects.create(
            exercise_session=exercise_session,
            content_type=content_type,
            object_id=rest_instance.id,
            order=ExerciseSessionItem.objects.filter(exercise_session=exercise_session).count()
        )
        return rest_instance

    @staticmethod
    def add_interval(request, exercise_session, interval_data):
        from server.workouts.utils import convert_str_time_to_interval_time

        # {'distance': '3000', 'level': '', 'pace': '5', 'time': '0:2:0'}
        transformed_time = convert_str_time_to_interval_time(interval_data.get('time', '0:0:0'))

        interval_instance = Interval.objects.create(
            time=datetime.time(transformed_time['hours'], transformed_time['minutes'], transformed_time['seconds']),
            distance=get_value_or_default(interval_data, 'distance'),
            level=get_value_or_default(interval_data, 'level'),
            pace=get_value_or_default(interval_data, 'pace'),
            created_by=request.user.profile
        )
        content_type = ContentType.objects.get_for_model(interval_instance)
        ExerciseSessionItem.objects.create(
            exercise_session=exercise_session,
            content_type=content_type,
            object_id=interval_instance.id,
            order=ExerciseSessionItem.objects.filter(exercise_session=exercise_session).count()
        )
        return interval_instance


class SupersetSession(models.Model):
    exercises = models.ManyToManyField(ExerciseSession)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Superset Session created by {self.created_by} at {self.created_at}"

    def add_exercise_sessions(self, exercise_sessions):
        """Iterating over the exercises and checking if the exercise session
        is not in the superset and if it is not adding it to the list of exercises to add"""
        exercises = self.exercises.all()
        exercises_to_add = []

        for exercise_session in exercise_sessions:
            if exercise_session not in exercises:
                exercises_to_add.append(exercise_session)
        if len(exercises_to_add) == 0:
            return self
        self.exercises.add(*exercises_to_add)
        self.save()
        return self

    @staticmethod
    def edit_session(request, superset_session, data):
        from server.workouts.utils import remove_exercises_not_in_list
        exercises_in_superset_instance = superset_session.exercises.all()
        """This function is removing the exercises that are not in the list of exercises but are in the superset"""
        exercises_after_deletion = remove_exercises_not_in_list(exercises_in_superset_instance,
                                                                data.get('exercises', {}))
        """This function is adding the new exercises to the superset"""
        session_after_exercise_add = superset_session.add_exercise_sessions(exercises_after_deletion)
        for exercise_session in session_after_exercise_add.exercises.all():
            exercise_data = next(
                (exercise for exercise in data.get('exercises') if exercise['id'] == exercise_session.pk),
                None)
            """And this is editing the exercise"""
            ExerciseSession.edit_session(request, exercise_session, exercise_data)
        superset_session.notes = data.get('notes')
        return superset_session.save()


# added later
class ExerciseSessionItem(models.Model):
    exercise_session = models.ForeignKey(ExerciseSession, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class WorkoutSession(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME
    )
    # TODO: On a later basis add a field for total sets per muscle group or something similar
    total_exercises = models.IntegerField()
    total_sets = models.IntegerField()
    total_weight_volume = models.IntegerField()
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
    exercises = models.ManyToManyField(
        'WorkoutExerciseSession',
        related_name='workout_sessions'
    )

    def add_exercise_sessions(self, exercise_sessions):
        self.exercises.add(*exercise_sessions)
        self.save()
        return self

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

    @staticmethod
    def edit_session(request, workout_session, new_data):
        from server.workouts.utils import update_workout_session_exercises

        workout_name = new_data.get('name')
        exercises = new_data.get('exercises')

        updated_exercises = update_workout_session_exercises(request, workout_session, exercises)

        workout_session.name = workout_name
        workout_session.exercises.set(updated_exercises)
        workout_session.save()
        return workout_session


class WorkoutExerciseSession(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    workout_session = models.ForeignKey(WorkoutSession, related_name='workout_exercises', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        # exercise_name = ''
        if self.content_type.model == 'supersetsession':
            exercise_name = 'Superset'
        else:
            exercise_name = self.content_object.exercise.name
        return f"Workout Exercise Session {self.id} ---- {exercise_name}"


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
