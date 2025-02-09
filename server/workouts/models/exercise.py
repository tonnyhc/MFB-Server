from datetime import datetime

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models, transaction
from django.db.models import Max
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError, PermissionDenied

from server.profiles.models import Profile
from django.contrib.contenttypes.models import ContentType

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
        # print(set_data_fields)
        # print(set_intance_fields)
        if set_data_fields == set_intance_fields:
            # print("The fields are the same")
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

    def edit_data(self, request, interval_data):
        if request.user.profile != self.created_by:
            return PermissionDenied("You can only edit your own sets")
        interval_instance_fields = {
            'time': self.time,
            'distance': self.distance,
            'level': self.level,
            'pace': self.pace,

        }
        # TODO: Check if all the fields are the same, to not make the edits

        interval_data_fields = {
            'time': interval_data.get('time'),
            'distance': int(interval_data.get('distance')),
            'level': int(interval_data.get('level')),
            'pace': int(interval_data.get('pace')),

        }

        if interval_data_fields == interval_instance_fields:
            return self

        splitted_time = interval_data.get('time', '0:0:0').split(':')
        self.time = datetime.time(int(splitted_time[0]), int(splitted_time[1]), int(splitted_time[2]))
        self.weight = interval_data['distance']
        self.min_reps = interval_data['level']
        self.max_reps = interval_data['pace']

        self.save()
        return self


class Exercise(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )
    targeted_muscle_groups = models.ManyToManyField(MuscleGroup, blank=True,
                                                    null=True)
    is_cardio = models.BooleanField(
        default=False,
    )
    bodyweight = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


class CustomExercise(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )
    targeted_muscle_groups = models.ManyToManyField(MuscleGroup, blank=True,
                                                    null=True)
    is_cardio = models.BooleanField(
        default=False,
    )
    bodyweight = models.BooleanField(
        default=False
    )

    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    @staticmethod
    def create_exercise(request, exercise_data, *args, **kwargs):
        with transaction.atomic():

            exercise_name = exercise_data.get('name', '')
            bodyweight_compatible = exercise_data.get('bodyweight_compatible', False)
            cardio_exercise = exercise_data.get('cardio_exercise', False)
            instructions = exercise_data.get('instructions', [])
            muscle_groups = exercise_data.get('muscle_groups', [])
            if not exercise_name:
                return PermissionDenied("Exercise name is required")
            if len(muscle_groups) <= 0 and not cardio_exercise:
                return PermissionDenied("Exercise must have at least one muscle group")
            muscle_groups_for_instance = []
            for group in muscle_groups:
                try:
                    muscle_group_instance = MuscleGroup.objects.get(id=group.get('id', None))
                    muscle_groups_for_instance.append(muscle_group_instance)
                except MuscleGroup.DoesNotExist:
                    return PermissionDenied("Muscle group instance does not exist!")

            exercise_instance = CustomExercise.objects.create(name=exercise_name,
                                                              is_cardio=cardio_exercise,
                                                              bodyweight=bodyweight_compatible,
                                                              created_by=request.user.profile)
            exercise_instance.targeted_muscle_groups.set(muscle_groups_for_instance)
            for instruction in instructions:
                text = instruction.get('text', '')

                instruction_instance = ExerciseInstruction.create_instance(request, text, exercise_instance)
                instruction_instance.save()
            exercise_instance.save()
            return exercise_instance

    def __str__(self):
        return self.name


class ExerciseInstruction(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    history = HistoricalRecords()

    # Generic relation fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    exercise_content_object = GenericForeignKey('content_type', 'object_id')

    @staticmethod
    def create_instance(request, text: str, exercise_instance):
        content_type = ContentType.objects.get_for_model(exercise_instance)
        return ExerciseInstruction.objects.create(
            text=text,
            exercise_content_object=exercise_instance,
            created_by=request.user.profile,
            content_type=content_type,
            object_id=exercise_instance.id
        )

    def __str__(self):
        return self.text


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
                if 'type' not in item or not item['type']:
                    raise ValidationError("Can't create set session without a type!")
                if 'data' not in item or not item['data']:
                    raise ValidationError("Can't create set session without data!")
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
            if exercise_set['type'] == 'interval':
                interval_instance = Interval.objects.get(pk=exercise_set['id'])
                interval_instance.edit_data(request, exercise_set.get('data', {}))
                continue
            try:
                set_instance = Set.objects.get(pk=exercise_set['id'])
                Set.edit_data(request, set_instance, exercise_set.get('data', {}))
            except Set.DoesNotExist:
                return models.ObjectDoesNotExist
        exercise_session.notes = notes
        exercise_session.save()
        return exercise_session

    # added later
    @staticmethod
    def add_set(request, exercise_session, set_data):
        # TODO: Check the items fields and if there are empty dont create the instance

        set_instance = Set.objects.create(
            weight=float(set_data['weight']) if set_data.get('weight') not in [None, '', 'null'] else None,
            reps=int(set_data['reps']) if set_data.get('reps') not in [None, '', 'null'] else None,
            min_reps=int(set_data['min_reps']) if set_data.get('min_reps') not in [None, '', 'null'] else None,
            max_reps=int(set_data['max_reps']) if set_data.get('max_reps') not in [None, '', 'null'] else None,
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
